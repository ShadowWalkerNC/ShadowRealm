"""
C101 — Mock Tool Registry
Deterministic mock tools for testing agent interactions in isolation.
"""
from __future__ import annotations
from typing import Dict, Any, Callable

class MockToolRegistry:
    def __init__(self):
        self._mocks: Dict[str, Callable[..., Any]] = {}

    def register_mock(self, tool_name: str, fn: Callable[..., Any]) -> None:
        self._mocks[tool_name] = fn

    def call_mock(self, tool_name: str, *args: Any, **kwargs: Any) -> Any:
        if tool_name not in self._mocks:
            raise KeyError(f"Mock tool '{tool_name}' not registered")
        return self._mocks[tool_name](*args, **kwargs)
