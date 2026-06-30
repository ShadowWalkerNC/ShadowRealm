"""C89 — Tool Registry

Maintains a catalogue of callable tools expressed as OpenAI function-calling
spec JSON schemas. Supports tool registration, lookup, validation of
incoming tool-call arguments, and execution dispatch.

Design principles
-----------------
* Zero external dependencies (stdlib only at the schema/dispatch layer).
* Tools are plain Python callables decorated with ``@tool_registry.register``.
* Schema is auto-derived from the decorator, or can be supplied manually.
* Argument validation uses jsonschema-lite (built-in ``types`` module) so no
  third-party package is required at runtime — full jsonschema validation
  is opt-in via a plugin hook.
"""
from __future__ import annotations

import inspect
import json
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from core.structured_logger import get_logger
from core.audit_logger import AuditLogger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Type-hint → JSON Schema primitive map
# ---------------------------------------------------------------------------
_PY_TO_JSON: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _annotation_to_json_type(annotation: Any) -> str:
    """Best-effort type annotation → JSON Schema type string."""
    if annotation is inspect.Parameter.empty:
        return "string"
    origin = getattr(annotation, "__origin__", None)
    if origin is list:
        return "array"
    if origin is dict:
        return "object"
    return _PY_TO_JSON.get(annotation, "string")


def _derive_schema(fn: Callable) -> dict[str, Any]:
    """Auto-derive an OpenAI function-calling spec schema from a callable."""
    sig = inspect.signature(fn)
    doc = (fn.__doc__ or "").strip().splitlines()[0] if fn.__doc__ else ""
    properties: dict[str, Any] = {}
    required: list[str] = []

    for name, param in sig.parameters.items():
        if name in ("self", "cls"):
            continue
        json_type = _annotation_to_json_type(param.annotation)
        prop: dict[str, Any] = {"type": json_type}
        # Pull inline description from param default if it is a ToolParam
        if isinstance(param.default, ToolParam):
            prop["description"] = param.default.description
            if param.default.enum:
                prop["enum"] = param.default.enum
        else:
            if param.default is inspect.Parameter.empty:
                required.append(name)
        properties[name] = prop

    return {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": doc,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


@dataclass
class ToolParam:
    """Metadata for a tool parameter; use as a default value in signatures."""
    description: str = ""
    enum: list[str] = field(default_factory=list)
    default: Any = inspect.Parameter.empty


@dataclass
class ToolDefinition:
    name: str
    fn: Callable
    schema: dict[str, Any]
    tags: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class ToolResult:
    name: str
    call_id: str
    output: Any
    error: Optional[str] = None
    latency_ms: float = 0.0
    success: bool = True


class ToolRegistry:
    """Central registry for all callable tools.

    Usage::

        registry = ToolRegistry()

        @registry.register(tags=["search"])
        def web_search(query: str, max_results: int = 5) -> list[dict]:
            \"\"\"Search the web and return a list of results.\"\"\"
            ...

        # Get schema list for LLM
        tools_json = registry.list_schemas()

        # Dispatch a tool call from LLM output
        result = registry.call("web_search", {"query": "python typing"}, call_id="tc_1")
    """

    def __init__(self, audit: Optional[AuditLogger] = None) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._audit = audit

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        fn: Optional[Callable] = None,
        *,
        name: Optional[str] = None,
        schema: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
        enabled: bool = True,
    ) -> Callable:
        """Decorator / direct registration.

        Can be used as::

            @registry.register
            def my_tool(): ...

            @registry.register(tags=["io"])
            def my_tool(): ...

            registry.register(my_fn, schema=my_schema)
        """
        def _inner(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_schema = schema or _derive_schema(func)
            defn = ToolDefinition(
                name=tool_name,
                fn=func,
                schema=tool_schema,
                tags=tags or [],
                enabled=enabled,
            )
            self._tools[tool_name] = defn
            log.debug("tool_registry.registered", tool=tool_name)
            return func

        if fn is not None:
            return _inner(fn)
        return _inner

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)
        log.debug("tool_registry.unregistered", tool=name)

    def enable(self, name: str) -> None:
        self._tools[name].enabled = True

    def disable(self, name: str) -> None:
        self._tools[name].enabled = False

    # ------------------------------------------------------------------
    # Schema access
    # ------------------------------------------------------------------

    def list_schemas(
        self,
        tags: Optional[list[str]] = None,
        enabled_only: bool = True,
    ) -> list[dict[str, Any]]:
        """Return a list of JSON schemas suitable for the LLM 'tools' parameter."""
        out = []
        for defn in self._tools.values():
            if enabled_only and not defn.enabled:
                continue
            if tags and not any(t in defn.tags for t in tags):
                continue
            out.append(defn.schema)
        return out

    def get_schema(self, name: str) -> dict[str, Any]:
        return self._tools[name].schema

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_arguments(
        self, name: str, arguments: dict[str, Any]
    ) -> list[str]:
        """Return a list of validation error strings (empty == valid)."""
        if name not in self._tools:
            return [f"Unknown tool: {name}"]
        errors: list[str] = []
        params_schema = (
            self._tools[name]
            .schema["function"]["parameters"]
        )
        required = params_schema.get("required", [])
        properties = params_schema.get("properties", {})

        for req_field in required:
            if req_field not in arguments:
                errors.append(f"Missing required argument: '{req_field}'")

        for arg_name, arg_value in arguments.items():
            if arg_name not in properties:
                errors.append(f"Unexpected argument: '{arg_name}'")
                continue
            expected_type = properties[arg_name].get("type")
            actual_type = _PY_TO_JSON.get(type(arg_value), "string")
            if expected_type and expected_type != actual_type:
                # Allow int where number expected
                if not (expected_type == "number" and actual_type == "integer"):
                    errors.append(
                        f"Argument '{arg_name}' expected type '{expected_type}', "
                        f"got '{actual_type}'"
                    )
            enum_vals = properties[arg_name].get("enum")
            if enum_vals and arg_value not in enum_vals:
                errors.append(
                    f"Argument '{arg_name}' value {arg_value!r} not in "
                    f"allowed values: {enum_vals}"
                )

        return errors

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def call(
        self,
        name: str,
        arguments: dict[str, Any],
        call_id: str = "",
        validate: bool = True,
    ) -> ToolResult:
        """Execute a tool by name with the given arguments."""
        call_id = call_id or f"tc_{int(time.time_ns())}"
        if name not in self._tools:
            return ToolResult(
                name=name, call_id=call_id,
                output=None, error=f"Tool '{name}' not found.", success=False,
            )
        defn = self._tools[name]
        if not defn.enabled:
            return ToolResult(
                name=name, call_id=call_id,
                output=None, error=f"Tool '{name}' is disabled.", success=False,
            )
        if validate:
            errs = self.validate_arguments(name, arguments)
            if errs:
                return ToolResult(
                    name=name, call_id=call_id,
                    output=None, error=" | ".join(errs), success=False,
                )
        t0 = time.monotonic()
        try:
            output = defn.fn(**arguments)
            latency = (time.monotonic() - t0) * 1000
            if self._audit:
                self._audit.record(
                    action="tool_call",
                    subject=name,
                    metadata={"call_id": call_id, "latency_ms": round(latency, 1)},
                )
            log.info(
                "tool_registry.called",
                tool=name, call_id=call_id, latency_ms=round(latency, 1),
            )
            return ToolResult(
                name=name, call_id=call_id,
                output=output, latency_ms=latency, success=True,
            )
        except Exception as exc:  # noqa: BLE001
            latency = (time.monotonic() - t0) * 1000
            tb = traceback.format_exc()
            log.error(
                "tool_registry.error",
                tool=name, call_id=call_id, error=str(exc),
            )
            return ToolResult(
                name=name, call_id=call_id,
                output=None,
                error=f"{exc}\n{tb}",
                latency_ms=latency,
                success=False,
            )

    def call_from_llm(
        self,
        tool_calls: list[dict[str, Any]],
        validate: bool = True,
    ) -> list[ToolResult]:
        """Dispatch a list of tool calls as returned by an LLM response.

        Expected format (OpenAI-compatible)::

            [
                {"id": "tc_1", "function": {"name": "...", "arguments": "{..."}}
            ]
        """
        results = []
        for tc in tool_calls:
            name = tc["function"]["name"]
            raw_args = tc["function"]["arguments"]
            call_id = tc.get("id", "")
            if isinstance(raw_args, str):
                try:
                    arguments = json.loads(raw_args)
                except json.JSONDecodeError as exc:
                    results.append(ToolResult(
                        name=name, call_id=call_id,
                        output=None,
                        error=f"Invalid JSON in arguments: {exc}",
                        success=False,
                    ))
                    continue
            else:
                arguments = raw_args
            results.append(self.call(name, arguments, call_id=call_id, validate=validate))
        return results

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
