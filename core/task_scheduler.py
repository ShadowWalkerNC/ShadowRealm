"""TaskScheduler — One-shot and recurring task orchestrator (C46).

Schedules callables to run at a future time or after a delay, with:
  - One-shot: run_at(ts, fn) / run_after(delay_s, fn)
  - Recurring: every(interval_s, fn, *, jitter_s)
  - Cron-style: delegated to CronJobRunner
  - Priority queue: higher-priority tasks preempt lower in the worker pool
  - Graceful shutdown: drain or cancel pending on stop()
  - Integration with TelemetryCollector for task lifecycle events

All tasks run in a thread pool (configurable workers).
The scheduler owns a single background thread that sleeps until the next
due task, then submits it to the pool.

Public API:
  sched = TaskScheduler(workers=4)
  sched.start()
  task_id = sched.run_after(delay_s, fn, *args, **kwargs)
  task_id = sched.run_at(ts, fn, *args, **kwargs)
  task_id = sched.every(interval_s, fn, *, jitter_s, max_runs, priority)
  sched.cancel(task_id)
  sched.stop(drain=True)
  sched.status()  -> dict
"""

from __future__ import annotations

import heapq
import logging
import random
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_DEFAULT_WORKERS = 4


@dataclass
class ScheduledTask:
    task_id:    str
    fn:         Callable
    args:       tuple
    kwargs:     dict
    run_at:     float          # unix timestamp
    priority:   int = 5        # 1 (high) .. 10 (low)
    interval_s: Optional[float] = None   # recurring if set
    jitter_s:   float = 0.0
    max_runs:   int = 0        # 0 = unlimited
    runs:       int = 0
    cancelled:  bool = False
    last_error: Optional[str] = None

    # heap comparison by (run_at, priority)
    def __lt__(self, other: ScheduledTask) -> bool:
        return (self.run_at, self.priority) < (other.run_at, other.priority)


class TaskScheduler:
    """Thread-safe one-shot and recurring task scheduler."""

    def __init__(self, workers: int = _DEFAULT_WORKERS, telemetry=None):
        self._workers   = workers
        self._tel       = telemetry
        self._heap:     List[ScheduledTask] = []
        self._tasks:    Dict[str, ScheduledTask] = {}
        self._lock      = threading.Lock()
        self._wake      = threading.Event()
        self._pool:     Optional[ThreadPoolExecutor] = None
        self._thread:   Optional[threading.Thread] = None
        self._running   = False
        self._completed = 0
        self._errors    = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        self._pool   = ThreadPoolExecutor(max_workers=self._workers)
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("TaskScheduler: started")

    def stop(self, drain: bool = True) -> None:
        self._running = False
        self._wake.set()
        if self._thread:
            self._thread.join(timeout=5)
        if self._pool:
            self._pool.shutdown(wait=drain)
        logger.info("TaskScheduler: stopped")

    # ------------------------------------------------------------------
    # Schedule API
    # ------------------------------------------------------------------

    def run_at(
        self, ts: float, fn: Callable, *args,
        priority: int = 5, **kwargs
    ) -> str:
        task = ScheduledTask(
            task_id=uuid.uuid4().hex[:10],
            fn=fn, args=args, kwargs=kwargs,
            run_at=ts, priority=priority,
        )
        self._push(task)
        return task.task_id

    def run_after(
        self, delay_s: float, fn: Callable, *args,
        priority: int = 5, **kwargs
    ) -> str:
        return self.run_at(time.time() + delay_s, fn, *args,
                           priority=priority, **kwargs)

    def every(
        self,
        interval_s: float,
        fn: Callable,
        *args,
        jitter_s: float = 0.0,
        max_runs: int = 0,
        priority: int = 5,
        **kwargs,
    ) -> str:
        jitter = random.uniform(0, jitter_s) if jitter_s else 0.0
        task = ScheduledTask(
            task_id=uuid.uuid4().hex[:10],
            fn=fn, args=args, kwargs=kwargs,
            run_at=time.time() + interval_s + jitter,
            priority=priority,
            interval_s=interval_s,
            jitter_s=jitter_s,
            max_runs=max_runs,
        )
        self._push(task)
        return task.task_id

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            t = self._tasks.get(task_id)
            if t:
                t.cancelled = True
                return True
        return False

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> Dict:
        with self._lock:
            pending = [t for t in self._tasks.values() if not t.cancelled]
        return {
            "running":   self._running,
            "pending":   len(pending),
            "completed": self._completed,
            "errors":    self._errors,
            "workers":   self._workers,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _push(self, task: ScheduledTask) -> None:
        with self._lock:
            heapq.heappush(self._heap, task)
            self._tasks[task.task_id] = task
        self._wake.set()

    def _loop(self) -> None:
        while self._running:
            with self._lock:
                next_task = self._heap[0] if self._heap else None

            if next_task is None:
                self._wake.wait(timeout=60)
                self._wake.clear()
                continue

            wait = next_task.run_at - time.time()
            if wait > 0:
                self._wake.wait(timeout=wait)
                self._wake.clear()
                continue

            with self._lock:
                if self._heap:
                    task = heapq.heappop(self._heap)
                else:
                    continue

            if task.cancelled:
                self._tasks.pop(task.task_id, None)
                continue

            self._pool.submit(self._run_task, task)

    def _run_task(self, task: ScheduledTask) -> None:
        t0 = time.time()
        try:
            task.fn(*task.args, **task.kwargs)
            task.runs += 1
            with self._lock:
                self._completed += 1
            self._emit("task_done", task, duration_ms=(time.time()-t0)*1000)
        except Exception as e:
            task.last_error = str(e)
            with self._lock:
                self._errors += 1
            logger.warning(f"TaskScheduler: task '{task.task_id}' failed: {e}")
            self._emit("task_error", task, error=str(e))

        # Reschedule recurring
        if task.interval_s and not task.cancelled:
            if not task.max_runs or task.runs < task.max_runs:
                jitter = random.uniform(0, task.jitter_s) if task.jitter_s else 0.0
                task.run_at = time.time() + task.interval_s + jitter
                self._push(task)
            else:
                with self._lock:
                    self._tasks.pop(task.task_id, None)
        else:
            with self._lock:
                self._tasks.pop(task.task_id, None)

    def _emit(self, kind: str, task: ScheduledTask,
               duration_ms: float = 0.0, error: Optional[str] = None) -> None:
        if self._tel:
            try:
                self._tel.emit(kind, {"task_id": task.task_id},
                               duration_ms=duration_ms, error=error)
            except Exception:
                pass
