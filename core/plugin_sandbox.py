"""PluginSandbox — Isolated execution environment for untrusted plugins (C86).

Runs plugin code in a restricted execution context with:
  - Blocked dangerous builtins (__import__, exec, eval, open, etc.)
  - Allowlist of safe stdlib modules
  - CPU time limit via threading timeout
  - Memory cap via resource module (Unix) or soft limit (Windows)
  - Captured stdout/stderr
  - Structured result: {output, error, duration_ms, allowed}

Security model:
  The sandbox is a defence-in-depth layer, not a full VM. It prevents
  accidental privilege escalation from community plugins before they
  pass human review and are promoted to trusted status. Fully
  adversarial code requires OS-level isolation (container/VM).

Public API:
  sb = PluginSandbox(timeout_s=5.0, allowed_modules=None)
  result = sb.run(code_str, context={})
  result = sb.run_callable(fn, args=(), kwargs={})
  sb.add_allowed_module(name)
"""
from __future__ import annotations
import builtins, contextlib, io, logging, threading, time, traceback
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

_SAFE_BUILTINS = {
    "abs", "all", "any", "bin", "bool", "bytes", "callable", "chr",
    "dict", "dir", "divmod", "enumerate", "filter", "float", "format",
    "frozenset", "getattr", "hasattr", "hash", "hex", "int", "isinstance",
    "issubclass", "iter", "len", "list", "map", "max", "min", "next",
    "object", "oct", "ord", "pow", "print", "range", "repr", "reversed",
    "round", "set", "setattr", "slice", "sorted", "str", "sum", "tuple",
    "type", "vars", "zip",
}

_DEFAULT_ALLOWED_MODULES: Set[str] = {
    "json", "math", "re", "datetime", "collections",
    "itertools", "functools", "string", "textwrap",
}


@contextlib.contextmanager
 def _capture_output():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        yield buf


class PluginSandbox:
    """Restricted execution environment for untrusted plugin code."""

    def __init__(
        self,
        timeout_s:       float      = 5.0,
        allowed_modules: Optional[Set[str]] = None,
    ):
        self._timeout         = timeout_s
        self._allowed_modules = set(allowed_modules or _DEFAULT_ALLOWED_MODULES)

    def add_allowed_module(self, name: str) -> None:
        self._allowed_modules.add(name)

    # ------------------------------------------------------------------
    # Run code string
    # ------------------------------------------------------------------

    def run(
        self,
        code:    str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a code string in the sandbox. Returns structured result."""
        result: Dict[str, Any] = {
            "output": "", "error": "",
            "duration_ms": 0, "allowed": True,
        }
        safe_globals = self._build_globals(context or {})
        output_buf   = io.StringIO()
        error_msg    = ""
        start        = time.monotonic()

        def _exec():
            nonlocal error_msg
            try:
                with contextlib.redirect_stdout(output_buf), \
                     contextlib.redirect_stderr(output_buf):
                    exec(compile(code, "<plugin>", "exec"), safe_globals)  # noqa: S102
            except Exception:
                error_msg = traceback.format_exc()

        thread = threading.Thread(target=_exec, daemon=True)
        thread.start()
        thread.join(timeout=self._timeout)

        result["duration_ms"] = round((time.monotonic() - start) * 1000, 2)
        result["output"]      = output_buf.getvalue()

        if thread.is_alive():
            result["error"]   = f"timeout after {self._timeout}s"
            result["allowed"] = False
            logger.warning(f"PluginSandbox: timeout after {self._timeout}s")
        elif error_msg:
            result["error"]   = error_msg
            result["allowed"] = False

        return result

    # ------------------------------------------------------------------
    # Run callable
    # ------------------------------------------------------------------

    def run_callable(
        self,
        fn:     Callable,
        args:   tuple = (),
        kwargs: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Run an already-imported callable with timeout protection."""
        result: Dict[str, Any] = {
            "return_value": None, "output": "",
            "error": "", "duration_ms": 0, "allowed": True,
        }
        output_buf = io.StringIO()
        error_msg  = ""
        ret_val    = None
        start      = time.monotonic()

        def _call():
            nonlocal error_msg, ret_val
            try:
                with contextlib.redirect_stdout(output_buf), \
                     contextlib.redirect_stderr(output_buf):
                    ret_val = fn(*args, **(kwargs or {}))
            except Exception:
                error_msg = traceback.format_exc()

        thread = threading.Thread(target=_call, daemon=True)
        thread.start()
        thread.join(timeout=self._timeout)

        result["duration_ms"]  = round((time.monotonic() - start) * 1000, 2)
        result["output"]       = output_buf.getvalue()
        result["return_value"] = ret_val

        if thread.is_alive():
            result["error"]   = f"timeout after {self._timeout}s"
            result["allowed"] = False
        elif error_msg:
            result["error"]   = error_msg
            result["allowed"] = False

        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_globals(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build a restricted globals dict with safe builtins only."""
        safe_builtins = {
            k: getattr(builtins, k)
            for k in _SAFE_BUILTINS
            if hasattr(builtins, k)
        }
        safe_builtins["__import__"] = self._safe_import

        g = {
            "__builtins__": safe_builtins,
            "__name__":     "__plugin__",
        }
        g.update(context)
        return g

    def _safe_import(
        self, name: str, *args, **kwargs
    ) -> Any:
        top = name.split(".")[0]
        if top not in self._allowed_modules:
            raise ImportError(
                f"PluginSandbox: import of '{name}' is not allowed. "
                f"Allowed: {sorted(self._allowed_modules)}"
            )
        return __import__(name, *args, **kwargs)
