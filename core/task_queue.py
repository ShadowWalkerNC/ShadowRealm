"""TaskQueue — Durable async work queue with worker pool (C48).

A lightweight alternative to Celery/RQ for intra-process background work.
Tasks are enqueued by producers and consumed by a configurable worker
pool.  Supports:
  - Priority queues (1-10 scale)
  - Dead-letter queue (DLQ) after max_retries exhausted
  - Result store (in-memory dict with TTL eviction)
  - Back-pressure: enqueue blocks / raises when queue is full
  - Pause / resume without stopping workers
  - Metrics: enqueued, dequeued, failed, dlq_size

Public API:
  q = TaskQueue(workers=4, maxsize=1000, max_retries=3)
  q.start()
  job_id = q.enqueue(fn, *args, priority, ttl_s, **kwargs)
  result = q.result(job_id, timeout_s)  # blocks until done or timeout
  q.pause() / q.resume()
  q.stop(drain=True)
  q.metrics()  -> dict
  q.dlq_items() -> list
"""

from __future__ import annotations

import heapq
import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_DEFAULT_WORKERS   = 4
_DEFAULT_MAXSIZE   = 1_000
_DEFAULT_RETRIES   = 3
_DEFAULT_RESULT_TTL = 300.0   # seconds


@dataclass
class QueuedJob:
    job_id:    str
    fn:        Callable
    args:      tuple
    kwargs:    dict
    priority:  int = 5
    ttl_s:     float = 0.0
    enqueued_at: float = field(default_factory=time.time)
    attempts:  int = 0
    max_retries: int = _DEFAULT_RETRIES
    last_error: Optional[str] = None

    def __lt__(self, other: QueuedJob) -> bool:
        return (self.priority, self.enqueued_at) < (other.priority, other.enqueued_at)


@dataclass
class JobResult:
    job_id:    str
    success:   bool
    value:     Any
    error:     Optional[str]
    duration_ms: float
    stored_at: float = field(default_factory=time.time)


class TaskQueue:
    """Priority work queue with retry, DLQ, and result store."""

    def __init__(
        self,
        workers:    int   = _DEFAULT_WORKERS,
        maxsize:    int   = _DEFAULT_MAXSIZE,
        max_retries: int  = _DEFAULT_RETRIES,
        result_ttl_s: float = _DEFAULT_RESULT_TTL,
        telemetry=None,
    ):
        self._workers     = workers
        self._maxsize     = maxsize
        self._max_retries = max_retries
        self._result_ttl  = result_ttl_s
        self._tel         = telemetry

        self._heap:    List[QueuedJob]       = []
        self._results: Dict[str, JobResult]  = {}
        self._dlq:     List[QueuedJob]       = []
        self._events:  Dict[str, threading.Event] = {}

        self._lock    = threading.Lock()
        self._notempty = threading.Condition(self._lock)
        self._paused  = False
        self._running = False
        self._threads: List[threading.Thread] = []

        # Counters
        self._n_enqueued = 0
        self._n_dequeued = 0
        self._n_failed   = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        self._running = True
        for _ in range(self._workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self._threads.append(t)
        # GC thread for result store
        gc = threading.Thread(target=self._gc_loop, daemon=True)
        gc.start()
        logger.info(f"TaskQueue: started {self._workers} workers")

    def stop(self, drain: bool = True) -> None:
        if drain:
            deadline = time.time() + 30
            while time.time() < deadline:
                with self._lock:
                    if not self._heap:
                        break
                time.sleep(0.1)
        self._running = False
        with self._notempty:
            self._notempty.notify_all()
        logger.info("TaskQueue: stopped")

    def pause(self) -> None:
        with self._lock:
            self._paused = True

    def resume(self) -> None:
        with self._notempty:
            self._paused = False
            self._notempty.notify_all()

    # ------------------------------------------------------------------
    # Enqueue
    # ------------------------------------------------------------------

    def enqueue(
        self,
        fn: Callable,
        *args,
        priority:    int   = 5,
        ttl_s:       float = 0.0,
        max_retries: Optional[int] = None,
        **kwargs,
    ) -> str:
        with self._lock:
            if len(self._heap) >= self._maxsize:
                raise RuntimeError(f"TaskQueue full (maxsize={self._maxsize})")
            job = QueuedJob(
                job_id=uuid.uuid4().hex[:10],
                fn=fn, args=args, kwargs=kwargs,
                priority=priority, ttl_s=ttl_s,
                max_retries=max_retries if max_retries is not None else self._max_retries,
            )
            heapq.heappush(self._heap, job)
            self._events[job.job_id] = threading.Event()
            self._n_enqueued += 1
        with self._notempty:
            self._notempty.notify()
        return job.job_id

    # ------------------------------------------------------------------
    # Result retrieval
    # ------------------------------------------------------------------

    def result(
        self,
        job_id: str,
        timeout_s: float = 30.0,
    ) -> Optional[JobResult]:
        """Block until job completes or timeout. Returns None on timeout."""
        event = self._events.get(job_id)
        if event:
            event.wait(timeout=timeout_s)
        return self._results.get(job_id)

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def metrics(self) -> Dict:
        with self._lock:
            return {
                "queued":    len(self._heap),
                "enqueued":  self._n_enqueued,
                "dequeued":  self._n_dequeued,
                "failed":    self._n_failed,
                "dlq_size":  len(self._dlq),
                "workers":   self._workers,
                "paused":    self._paused,
                "results_cached": len(self._results),
            }

    def dlq_items(self) -> List[QueuedJob]:
        with self._lock:
            return list(self._dlq)

    # ------------------------------------------------------------------
    # Worker loop
    # ------------------------------------------------------------------

    def _worker(self) -> None:
        while self._running:
            with self._notempty:
                while self._running and (self._paused or not self._heap):
                    self._notempty.wait(timeout=5)
                if not self._running:
                    return
                if not self._heap:
                    continue
                job = heapq.heappop(self._heap)
                self._n_dequeued += 1

            # TTL check
            if job.ttl_s and time.time() - job.enqueued_at > job.ttl_s:
                logger.debug(f"TaskQueue: job '{job.job_id}' expired (ttl)")
                self._store_result(job, False, None, "TTL expired", 0)
                continue

            t0 = time.time()
            try:
                value = job.fn(*job.args, **job.kwargs)
                dur   = (time.time() - t0) * 1000
                self._store_result(job, True, value, None, dur)
            except Exception as e:
                dur = (time.time() - t0) * 1000
                job.last_error = str(e)
                job.attempts  += 1
                if job.attempts <= job.max_retries:
                    logger.debug(f"TaskQueue: retry {job.attempts}/{job.max_retries} for '{job.job_id}'")
                    with self._notempty:
                        heapq.heappush(self._heap, job)
                        self._notempty.notify()
                else:
                    with self._lock:
                        self._dlq.append(job)
                        self._n_failed += 1
                    self._store_result(job, False, None, str(e), dur)
                    logger.warning(f"TaskQueue: job '{job.job_id}' sent to DLQ: {e}")

    def _store_result(self, job: QueuedJob, success: bool,
                      value: Any, error: Optional[str], dur: float) -> None:
        res = JobResult(job_id=job.job_id, success=success,
                        value=value, error=error, duration_ms=dur)
        with self._lock:
            self._results[job.job_id] = res
        ev = self._events.get(job.job_id)
        if ev:
            ev.set()

    def _gc_loop(self) -> None:
        while self._running:
            time.sleep(60)
            now = time.time()
            with self._lock:
                expired = [jid for jid, r in self._results.items()
                           if now - r.stored_at > self._result_ttl]
                for jid in expired:
                    del self._results[jid]
                    self._events.pop(jid, None)
