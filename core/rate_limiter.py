"""RateLimiter — Token-bucket and sliding-window rate limiting (C43).

Provides two algorithms selectable per rule:
  token_bucket   : smooth bursts, configurable refill rate + capacity
  sliding_window : strict per-window count, lower memory than leaky bucket

Each rule is keyed by (owner, resource) — e.g. ("alice", "llm_call").
Lookup is O(1); state is held in memory with optional Redis back-end
(pass a redis_client that exposes get/set/incr/expire).

Public API:
  rl = RateLimiter()
  rl.add_rule(resource, *, rpm, burst, algorithm, owner)   # configure
  result = rl.check(owner, resource)                       # RateResult
  result = rl.consume(owner, resource, tokens)             # deduct + check
  rl.reset(owner, resource)                                # clear state
  rl.status(owner)                                         # dict
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class RateResult:
    allowed:       bool
    remaining:     float    # tokens or requests remaining
    reset_in_s:    float    # seconds until full refill / window reset
    retry_after_s: float    # 0 if allowed, else suggested wait
    resource:      str
    owner:         str


@dataclass
class _Rule:
    resource:  str
    rpm:       float     # requests per minute
    burst:     float     # max burst (token bucket capacity)
    algorithm: str       # "token_bucket" | "sliding_window"
    owner:     Optional[str] = None   # None = applies to all owners


class _BucketState:
    def __init__(self, capacity: float, refill_rate: float):
        self.tokens     = capacity
        self.capacity   = capacity
        self.refill_rate = refill_rate   # tokens per second
        self.last_refill = time.time()

    def refill(self) -> None:
        now     = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def consume(self, tokens: float = 1.0) -> Tuple[bool, float]:
        self.refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True, self.tokens
        return False, self.tokens

    def reset_in(self) -> float:
        if self.tokens >= self.capacity:
            return 0.0
        needed = self.capacity - self.tokens
        return needed / max(self.refill_rate, 1e-9)


class _WindowState:
    def __init__(self, window_s: float, limit: int):
        self.window_s   = window_s
        self.limit      = limit
        self.timestamps = []

    def consume(self, tokens: float = 1.0) -> Tuple[bool, float]:
        now    = time.time()
        cutoff = now - self.window_s
        self.timestamps = [t for t in self.timestamps if t >= cutoff]
        count  = len(self.timestamps)
        if count + int(tokens) <= self.limit:
            for _ in range(int(tokens)):
                self.timestamps.append(now)
            return True, float(self.limit - count - int(tokens))
        return False, float(max(0, self.limit - count))

    def reset_in(self) -> float:
        if not self.timestamps:
            return 0.0
        return max(0.0, self.timestamps[0] + self.window_s - time.time())


class RateLimiter:
    """In-memory rate limiter supporting token-bucket and sliding-window."""

    def __init__(self):
        self._rules:  Dict[Tuple, _Rule]  = {}    # (owner_or_None, resource) -> Rule
        self._states: Dict[Tuple, object] = {}    # (owner, resource) -> State
        self._lock    = threading.Lock()

    # ------------------------------------------------------------------
    # Rule management
    # ------------------------------------------------------------------

    def add_rule(
        self,
        resource: str,
        *,
        rpm:       float = 60,
        burst:     float = 10,
        algorithm: str   = "token_bucket",
        owner:     Optional[str] = None,
    ) -> None:
        key = (owner, resource)
        with self._lock:
            self._rules[key] = _Rule(
                resource=resource, rpm=rpm, burst=burst,
                algorithm=algorithm, owner=owner,
            )

    def remove_rule(self, resource: str, owner: Optional[str] = None) -> bool:
        key = (owner, resource)
        with self._lock:
            return self._rules.pop(key, None) is not None

    # ------------------------------------------------------------------
    # Check / consume
    # ------------------------------------------------------------------

    def consume(
        self,
        owner:    str,
        resource: str,
        tokens:   float = 1.0,
    ) -> RateResult:
        rule = self._resolve_rule(owner, resource)
        if rule is None:
            return RateResult(allowed=True, remaining=999, reset_in_s=0,
                              retry_after_s=0, resource=resource, owner=owner)

        state = self._get_state(owner, resource, rule)
        with self._lock:
            allowed, remaining = state.consume(tokens)
            reset_in = state.reset_in()

        retry = 0.0 if allowed else max(0.1, reset_in)
        return RateResult(
            allowed=allowed, remaining=remaining,
            reset_in_s=round(reset_in, 2),
            retry_after_s=round(retry, 2),
            resource=resource, owner=owner,
        )

    def check(self, owner: str, resource: str) -> RateResult:
        """Check without consuming."""
        rule = self._resolve_rule(owner, resource)
        if rule is None:
            return RateResult(allowed=True, remaining=999, reset_in_s=0,
                              retry_after_s=0, resource=resource, owner=owner)
        state = self._get_state(owner, resource, rule)
        with self._lock:
            if isinstance(state, _BucketState):
                state.refill()
                allowed   = state.tokens >= 1.0
                remaining = state.tokens
            else:
                now    = time.time()
                cutoff = now - state.window_s
                count  = sum(1 for t in state.timestamps if t >= cutoff)
                allowed   = count < state.limit
                remaining = float(max(0, state.limit - count))
            reset_in = state.reset_in()
        return RateResult(
            allowed=allowed, remaining=remaining,
            reset_in_s=round(reset_in, 2),
            retry_after_s=0.0 if allowed else round(reset_in, 2),
            resource=resource, owner=owner,
        )

    def reset(self, owner: str, resource: str) -> None:
        with self._lock:
            self._states.pop((owner, resource), None)

    def status(self, owner: str) -> Dict:
        with self._lock:
            return {
                res: {
                    "allowed":    self.check(owner, res).allowed,
                    "remaining":  self.check(owner, res).remaining,
                    "reset_in_s": self.check(owner, res).reset_in_s,
                }
                for (o, res) in list(self._states.keys()) if o == owner
            }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _resolve_rule(self, owner: str, resource: str) -> Optional[_Rule]:
        return (
            self._rules.get((owner, resource))
            or self._rules.get((None, resource))
        )

    def _get_state(self, owner: str, resource: str, rule: _Rule):
        key = (owner, resource)
        with self._lock:
            if key not in self._states:
                rps = rule.rpm / 60.0
                if rule.algorithm == "sliding_window":
                    self._states[key] = _WindowState(
                        window_s=60.0, limit=int(rule.rpm)
                    )
                else:
                    self._states[key] = _BucketState(
                        capacity=rule.burst, refill_rate=rps
                    )
        return self._states[key]
