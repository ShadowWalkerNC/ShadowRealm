"""ToolExecutor — Safe async/sync tool call dispatch (C35).

Handles:
  - Resolving tool name → callable from the registered handler map
  - Timeout enforcement per tool call
  - Retry on transient failures (configurable)
  - Error capture and structured ToolResult packaging
  - Integration with ToolRegistry.record_error / record_success
  - Optional pre/post hooks (for logging, auth checks, rate-limit)

Design:
  Handlers are registered via `register_handler(name, fn)`.  Each handler
  is a sync or async callable that accepts (tool_input: dict) and returns
  any JSON-serialisable value.

  The executor wraps every call in try/except and always returns a
  ToolResult — callers never deal with raw exceptions.

Public API:
  ex = ToolExecutor(tool_registry)
  ex.register_handler(name, fn, *, timeout_s, max_retries)
  result = ex.call(name, tool_input, owner)   → ToolResult   (sync)
  result = await ex.acall(name, tool_input)   → ToolResult   (async)
  ex.call_batch(calls)                        → List[ToolResult]
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT  = 30.0   # seconds
_DEFAULT_RETRIES  = 2
_RETRY_BACKOFF    = 1.0    # seconds between retries


@dataclass
class ToolResult:
    name:       str
    success:    bool
    output:     Any             # JSON-serialisable value on success
    error:      Optional[str]   # error message on failure
    duration_ms: float
    retries:    int = 0
    tool_input: Optional[Dict] = None


@dataclass
class _HandlerConfig:
    fn:          Callable
    timeout_s:   float
    max_retries: int
    is_async:    bool


class ToolExecutor:
    """Dispatches tool calls with timeout, retry, and error containment."""

    def __init__(self, tool_registry=None):
        self._registry = tool_registry   # ToolRegistry instance (optional)
        self._handlers: Dict[str, _HandlerConfig] = {}
        self._pre_hooks:  List[Callable] = []
        self._post_hooks: List[Callable] = []

    # ------------------------------------------------------------------
    # Handler registration
    # ------------------------------------------------------------------

    def register_handler(
        self,
        name: str,
        fn: Callable,
        *,
        timeout_s: float = _DEFAULT_TIMEOUT,
        max_retries: int = _DEFAULT_RETRIES,
    ) -> None:
        self._handlers[name] = _HandlerConfig(
            fn=fn,
            timeout_s=timeout_s,
            max_retries=max_retries,
            is_async=inspect.iscoroutinefunction(fn),
        )
        logger.debug(f"ToolExecutor: registered handler '{name}'")

    def add_pre_hook(self, fn: Callable) -> None:
        """Pre-hook: fn(name, tool_input, owner) called before every tool call."""
        self._pre_hooks.append(fn)

    def add_post_hook(self, fn: Callable) -> None:
        """Post-hook: fn(result: ToolResult) called after every tool call."""
        self._post_hooks.append(fn)

    # ------------------------------------------------------------------
    # Sync call
    # ------------------------------------------------------------------

    def call(
        self,
        name: str,
        tool_input: Dict,
        owner: Optional[str] = None,
    ) -> ToolResult:
        """Execute a tool synchronously. Never raises — always returns ToolResult."""
        if name not in self._handlers:
            return ToolResult(
                name=name, success=False,
                output=None, error=f"No handler registered for '{name}'",
                duration_ms=0.0, tool_input=tool_input,
            )

        # Pre-hooks
        for hook in self._pre_hooks:
            try:
                hook(name, tool_input, owner)
            except Exception as e:
                logger.debug(f"ToolExecutor pre-hook failed: {e}")

        cfg     = self._handlers[name]
        retries = 0
        t0      = time.time()
        last_error = ""

        while retries <= cfg.max_retries:
            try:
                if cfg.is_async:
                    output = asyncio.get_event_loop().run_until_complete(
                        asyncio.wait_for(cfg.fn(tool_input), timeout=cfg.timeout_s)
                    )
                else:
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        fut = pool.submit(cfg.fn, tool_input)
                        output = fut.result(timeout=cfg.timeout_s)

                duration = (time.time() - t0) * 1000
                result = ToolResult(
                    name=name, success=True, output=output,
                    error=None, duration_ms=duration, retries=retries,
                    tool_input=tool_input,
                )
                if self._registry:
                    self._registry.record_success(name)
                break

            except Exception as e:
                last_error = str(e)
                retries += 1
                if retries <= cfg.max_retries:
                    logger.debug(f"ToolExecutor: retry {retries}/{cfg.max_retries} for '{name}': {e}")
                    time.sleep(_RETRY_BACKOFF * retries)
                else:
                    duration = (time.time() - t0) * 1000
                    result = ToolResult(
                        name=name, success=False, output=None,
                        error=last_error, duration_ms=duration, retries=retries - 1,
                        tool_input=tool_input,
                    )
                    if self._registry:
                        self._registry.record_error(name)

        # Post-hooks
        for hook in self._post_hooks:
            try:
                hook(result)
            except Exception as e:
                logger.debug(f"ToolExecutor post-hook failed: {e}")

        return result

    # ------------------------------------------------------------------
    # Async call
    # ------------------------------------------------------------------

    async def acall(
        self,
        name: str,
        tool_input: Dict,
        owner: Optional[str] = None,
    ) -> ToolResult:
        """Execute a tool asynchronously. Never raises."""
        if name not in self._handlers:
            return ToolResult(
                name=name, success=False,
                output=None, error=f"No handler registered for '{name}'",
                duration_ms=0.0, tool_input=tool_input,
            )

        for hook in self._pre_hooks:
            try:
                hook(name, tool_input, owner)
            except Exception:
                pass

        cfg        = self._handlers[name]
        retries    = 0
        t0         = time.time()
        last_error = ""
        result: ToolResult

        while retries <= cfg.max_retries:
            try:
                if cfg.is_async:
                    output = await asyncio.wait_for(cfg.fn(tool_input), timeout=cfg.timeout_s)
                else:
                    loop = asyncio.get_event_loop()
                    output = await asyncio.wait_for(
                        loop.run_in_executor(None, cfg.fn, tool_input),
                        timeout=cfg.timeout_s,
                    )
                duration = (time.time() - t0) * 1000
                result = ToolResult(
                    name=name, success=True, output=output,
                    error=None, duration_ms=duration, retries=retries,
                    tool_input=tool_input,
                )
                if self._registry:
                    self._registry.record_success(name)
                break
            except Exception as e:
                last_error = str(e)
                retries += 1
                if retries <= cfg.max_retries:
                    await asyncio.sleep(_RETRY_BACKOFF * retries)
                else:
                    duration = (time.time() - t0) * 1000
                    result = ToolResult(
                        name=name, success=False, output=None,
                        error=last_error, duration_ms=duration, retries=retries - 1,
                        tool_input=tool_input,
                    )
                    if self._registry:
                        self._registry.record_error(name)

        for hook in self._post_hooks:
            try:
                hook(result)
            except Exception:
                pass
        return result

    # ------------------------------------------------------------------
    # Batch
    # ------------------------------------------------------------------

    def call_batch(
        self,
        calls: List[Dict],   # [{"name": str, "input": dict, "owner": str|None}]
    ) -> List[ToolResult]:
        """Execute multiple tool calls sequentially. Returns results in order."""
        return [
            self.call(c["name"], c.get("input", {}), c.get("owner"))
            for c in calls
        ]
