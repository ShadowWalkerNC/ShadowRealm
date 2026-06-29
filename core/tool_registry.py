"""
C89 — Tool Registry
Stores tool schemas, dispatches calls, and exports provider-specific formats.
"""
from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict  # JSON Schema object
    handler: Callable
    category: str = "general"
    requires_confirmation: bool = False


class ToolValidationError(Exception):
    pass


class ToolNotFoundError(Exception):
    pass


class ToolRegistry:
    """
    Central registry for agent tools.
    Supports decorator registration, direct registration, validation, and dispatch.
    """

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        handler: Callable,
        category: str = "general",
        requires_confirmation: bool = False,
    ) -> ToolDefinition:
        defn = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            category=category,
            requires_confirmation=requires_confirmation,
        )
        self._tools[name] = defn
        return defn

    def tool(
        self,
        name: Optional[str] = None,
        description: str = "",
        parameters: Optional[dict] = None,
        category: str = "general",
        requires_confirmation: bool = False,
    ):
        """Decorator for registering a function as a tool."""
        def decorator(fn: Callable) -> Callable:
            tool_name = name or fn.__name__
            tool_desc = description or (inspect.getdoc(fn) or "")
            tool_params = parameters or self._infer_parameters(fn)
            self.register(
                name=tool_name,
                description=tool_desc,
                parameters=tool_params,
                handler=fn,
                category=category,
                requires_confirmation=requires_confirmation,
            )
            return fn
        return decorator

    def _infer_parameters(self, fn: Callable) -> dict:
        """Build a minimal JSON Schema from function annotations."""
        sig = inspect.signature(fn)
        properties: dict = {}
        required: list = []
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            ann = param.annotation
            json_type = type_map.get(ann, "string")
            properties[param_name] = {"type": json_type}
            if param.default is inspect.Parameter.empty:
                required.append(param_name)
        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }

    def get(self, name: str) -> ToolDefinition:
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' not registered")
        return self._tools[name]

    def list_names(self, category: Optional[str] = None) -> list[str]:
        if category:
            return [n for n, t in self._tools.items() if t.category == category]
        return list(self._tools.keys())

    def list_tools(self, category: Optional[str] = None) -> list[ToolDefinition]:
        if category:
            return [t for t in self._tools.values() if t.category == category]
        return list(self._tools.values())

    def validate_arguments(self, name: str, arguments: dict) -> None:
        defn = self.get(name)
        schema = defn.parameters
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        for req in required:
            if req not in arguments:
                raise ToolValidationError(
                    f"Tool '{name}' missing required argument: '{req}'"
                )

        for arg_name, value in arguments.items():
            if arg_name in properties:
                expected_type = properties[arg_name].get("type")
                if expected_type and not self._check_type(value, expected_type):
                    raise ToolValidationError(
                        f"Tool '{name}' argument '{arg_name}' expected {expected_type}, "
                        f"got {type(value).__name__}"
                    )

    def _check_type(self, value: Any, json_type: str) -> bool:
        type_checks = {
            "string": lambda v: isinstance(v, str),
            "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            "boolean": lambda v: isinstance(v, bool),
            "array": lambda v: isinstance(v, list),
            "object": lambda v: isinstance(v, dict),
        }
        checker = type_checks.get(json_type)
        return checker(value) if checker else True

    def dispatch(self, name: str, arguments: dict) -> Any:
        self.validate_arguments(name, arguments)
        defn = self.get(name)
        return defn.handler(**arguments)

    async def adispatch(self, name: str, arguments: dict) -> Any:
        import asyncio
        self.validate_arguments(name, arguments)
        defn = self.get(name)
        if inspect.iscoroutinefunction(defn.handler):
            return await defn.handler(**arguments)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: defn.handler(**arguments))

    def as_openai_tools(
        self,
        category: Optional[str] = None,
        names: Optional[list[str]] = None,
    ) -> list[dict]:
        tools = self._filter(category, names)
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    def as_anthropic_tools(
        self,
        category: Optional[str] = None,
        names: Optional[list[str]] = None,
    ) -> list[dict]:
        tools = self._filter(category, names)
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for t in tools
        ]

    def as_gemini_tools(self) -> list[dict]:
        return [
            {
                "function_declarations": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    }
                ]
            }
            for t in self._tools.values()
        ]

    def _filter(
        self,
        category: Optional[str],
        names: Optional[list[str]],
    ) -> list[ToolDefinition]:
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        if names:
            tools = [t for t in tools if t.name in names]
        return tools

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
