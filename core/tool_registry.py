"""ToolRegistry — Centralised tool catalogue with lifecycle management (C34).

Builds on top of the existing ToolSelector / ToolDescriptor infrastructure
(tool_selector.py) and adds:
  - Runtime registration / deregistration of tools
  - Tool health tracking (enabled / disabled / error state)
  - Permission gating (owner-level allow/deny lists)
  - Schema caching and token-cost bookkeeping
  - Integration with ContextProfile.max_tool_slots

The registry is a singleton per process; callers get it via
`ToolRegistry.get()`.  Tools are registered at startup from the MCP tool
list, then the agent_harness calls `select_for_task()` to get the filtered
slice passed to the LLM.

Public API:
  reg = ToolRegistry.get()
  reg.register(tool_dict, *, always_include, enabled)  → ToolDescriptor
  reg.register_many(tool_dicts)                        → List[ToolDescriptor]
  reg.deregister(name)                                 → bool
  reg.enable(name) / reg.disable(name, reason)         → bool
  reg.select_for_task(task, session_tags, owner, profile) → List[ToolDescriptor]
  reg.get_tool(name)                                   → ToolDescriptor | None
  reg.all_tools(*, enabled_only)                       → List[ToolDescriptor]
  reg.status()                                         → dict
"""

from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional, Set

from core.tool_selector import (
    ToolDescriptor,
    ToolSelector,
    build_registry,
    _infer_tags,
    _estimate_cost,
)
from core.context_profiles import ContextProfile, get_profile

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Singleton tool catalogue with selection, health, and permission gating."""

    _instance: Optional[ToolRegistry] = None
    _lock = threading.Lock()

    def __init__(self):
        self._tools:    Dict[str, ToolDescriptor] = {}   # name → descriptor
        self._enabled:  Dict[str, bool] = {}             # name → bool
        self._reasons:  Dict[str, str] = {}              # name → disable reason
        self._errors:   Dict[str, int] = {}              # name → consecutive error count
        self._allow:    Dict[str, Set[str]] = {}         # owner → allowed names (empty = all)
        self._deny:     Dict[str, Set[str]] = {}         # owner → denied names
        self._rlock     = threading.Lock()

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------

    @classmethod
    def get(cls) -> ToolRegistry:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (tests only)."""
        with cls._lock:
            cls._instance = None

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        tool_dict: Dict,
        *,
        always_include: bool = False,
        enabled: bool = True,
    ) -> ToolDescriptor:
        name = tool_dict.get("name", "")
        if not name:
            raise ValueError("tool_dict must have a 'name' field")
        desc = tool_dict.get("description", "")
        td = ToolDescriptor(
            name=name,
            description=desc,
            tags=_infer_tags(name, desc),
            always_include=always_include,
            token_cost=_estimate_cost(tool_dict),
            raw=tool_dict,
        )
        with self._rlock:
            self._tools[name]   = td
            self._enabled[name] = enabled
        logger.debug(f"ToolRegistry: registered '{name}' enabled={enabled}")
        return td

    def register_many(
        self,
        tool_dicts: List[Dict],
        *,
        always_include: Optional[List[str]] = None,
    ) -> List[ToolDescriptor]:
        pinned = set(always_include or [])
        return [self.register(t, always_include=(t.get("name") in pinned)) for t in tool_dicts]

    def deregister(self, name: str) -> bool:
        with self._rlock:
            if name in self._tools:
                del self._tools[name]
                self._enabled.pop(name, None)
                self._reasons.pop(name, None)
                self._errors.pop(name, None)
                return True
        return False

    # ------------------------------------------------------------------
    # Health / enable
    # ------------------------------------------------------------------

    def enable(self, name: str) -> bool:
        with self._rlock:
            if name in self._tools:
                self._enabled[name] = True
                self._reasons.pop(name, None)
                self._errors[name]  = 0
                return True
        return False

    def disable(self, name: str, reason: str = "") -> bool:
        with self._rlock:
            if name in self._tools:
                self._enabled[name] = False
                self._reasons[name] = reason
                logger.info(f"ToolRegistry: disabled '{name}': {reason}")
                return True
        return False

    def record_error(self, name: str, *, auto_disable_after: int = 5) -> None:
        """Increment error count; auto-disable after threshold."""
        with self._rlock:
            self._errors[name] = self._errors.get(name, 0) + 1
            if self._errors[name] >= auto_disable_after:
                self._enabled[name] = False
                self._reasons[name] = f"Auto-disabled after {self._errors[name]} consecutive errors"
                logger.warning(f"ToolRegistry: auto-disabled '{name}' after {self._errors[name]} errors")

    def record_success(self, name: str) -> None:
        with self._rlock:
            self._errors[name] = 0

    # ------------------------------------------------------------------
    # Permissions
    # ------------------------------------------------------------------

    def set_allow_list(self, owner: str, names: List[str]) -> None:
        """Only allow these tools for `owner`. Empty list = allow all."""
        self._allow[owner] = set(names)

    def set_deny_list(self, owner: str, names: List[str]) -> None:
        self._deny[owner] = set(names)

    def _permitted(self, name: str, owner: Optional[str]) -> bool:
        if not owner:
            return True
        if owner in self._deny and name in self._deny[owner]:
            return False
        if owner in self._allow and self._allow[owner]:
            return name in self._allow[owner]
        return True

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_tool(self, name: str) -> Optional[ToolDescriptor]:
        return self._tools.get(name)

    def all_tools(self, *, enabled_only: bool = False) -> List[ToolDescriptor]:
        with self._rlock:
            tools = list(self._tools.values())
        if enabled_only:
            tools = [t for t in tools if self._enabled.get(t.name, True)]
        return tools

    def select_for_task(
        self,
        task: str,
        session_tags: Optional[List[str]] = None,
        owner: Optional[str] = None,
        profile: Optional[ContextProfile] = None,
        force_include: Optional[List[str]] = None,
    ) -> List[ToolDescriptor]:
        """Return task-relevant tools respecting health, permissions and profile."""
        profile = profile or get_profile("gpt-4o")
        eligible = [
            t for t in self.all_tools(enabled_only=True)
            if self._permitted(t.name, owner)
        ]
        selector = ToolSelector(eligible, profile)
        return selector.select(task, session_tags=session_tags, force_include=force_include)

    def status(self) -> Dict:
        with self._rlock:
            tools = list(self._tools.values())
        return {
            "total":    len(tools),
            "enabled":  sum(1 for t in tools if self._enabled.get(t.name, True)),
            "disabled": sum(1 for t in tools if not self._enabled.get(t.name, True)),
            "tools": [
                {
                    "name":    t.name,
                    "enabled": self._enabled.get(t.name, True),
                    "errors":  self._errors.get(t.name, 0),
                    "reason":  self._reasons.get(t.name, ""),
                }
                for t in sorted(tools, key=lambda x: x.name)
            ],
        }
