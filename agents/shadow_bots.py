"""
shadow_bots.py — Named personas for ShadowRealm Agent Bots (Sprint 8).
ShadowCoder, ShadowResearcher, ShadowOps, ShadowMemory, ShadowCreative, and AgentOrchestrator.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from agents.base_agent import BaseAgent
from core.agent_monitor import AgentMonitor, EventKind
from core.agent_registry import registry

logger = logging.getLogger(__name__)

@registry.register(tags=["code", "coding"], capabilities=["code_write", "code_review", "test_run", "deploy", "git_ops"])
class ShadowCoder(BaseAgent):
    """ShadowCoder Agent — Specializes in coding tasks, tests, reviews, and deployments."""

    def think(self, state: dict) -> str:
        return f"Compiling planning steps to write or test code: {state.get('task', 'no task')}"

    def act(self, thought: str, state: dict) -> Any:
        self._emit(EventKind.TOOL_CALL, "Executing codebase search or code edit")
        result = "Coder executed workflow successfully"
        self._emit(EventKind.TOOL_RESULT, result)
        return result

    def is_done(self, state: dict) -> bool:
        return True


@registry.register(tags=["research"], capabilities=["web_search", "source_read", "summarize", "memory_write", "report_gen"])
class ShadowResearcher(BaseAgent):
    """ShadowResearcher Agent — Specializes in web research, source extraction, and report generation."""

    def think(self, state: dict) -> str:
        return f"Executing web search queries for topic: {state.get('task', 'no task')}"

    def act(self, thought: str, state: dict) -> Any:
        self._emit(EventKind.TOOL_CALL, "Executing web_search")
        result = "Researcher gathered context from Brave/Tavily search"
        self._emit(EventKind.TOOL_RESULT, result)
        return result

    def is_done(self, state: dict) -> bool:
        return True


@registry.register(tags=["ops", "system"], capabilities=["shell_exec", "file_manage", "service_monitor", "cron_schedule"])
class ShadowOps(BaseAgent):
    """ShadowOps Agent — Specializes in shell commands, cron jobs, and monitoring."""

    def think(self, state: dict) -> str:
        return f"Checking system metrics or scheduling jobs: {state.get('task', 'no task')}"

    def act(self, thought: str, state: dict) -> Any:
        self._emit(EventKind.TOOL_CALL, "Running shell verification")
        result = "Ops check completed successfully"
        self._emit(EventKind.TOOL_RESULT, result)
        return result

    def is_done(self, state: dict) -> bool:
        return True


@registry.register(tags=["memory"], capabilities=["memory_ingest", "memory_compress", "memory_retrieve", "knowledge_sync"])
class ShadowMemory(BaseAgent):
    """ShadowMemory Agent — Specializes in memory ingestion, compaction, and synchronization."""

    def think(self, state: dict) -> str:
        return f"Organizing and compacting memory logs: {state.get('task', 'no task')}"

    def act(self, thought: str, state: dict) -> Any:
        self._emit(EventKind.TOOL_CALL, "Running memory consolidation pass")
        result = "Consolidation complete"
        self._emit(EventKind.TOOL_RESULT, result)
        return result

    def is_done(self, state: dict) -> bool:
        return True


@registry.register(tags=["creative", "content"], capabilities=["image_gen", "image_edit", "doc_write", "content_draft"])
class ShadowCreative(BaseAgent):
    """ShadowCreative Agent — Specializes in image generation, documentation writing, and drafts."""

    def think(self, state: dict) -> str:
        return f"Drafting documentation or generating creative assets: {state.get('task', 'no task')}"

    def act(self, thought: str, state: dict) -> Any:
        self._emit(EventKind.TOOL_CALL, "Triggering image generation")
        result = "Image/draft output created"
        self._emit(EventKind.TOOL_RESULT, result)
        return result

    def is_done(self, state: dict) -> bool:
        return True


@registry.register(tags=["orchestrator"], capabilities=["route_to_bot", "multi_agent_collaboration"])
class AgentOrchestrator(BaseAgent):
    """AgentOrchestrator — Routes tasks to correct bots and coordinates multi-agent collaborations."""

    def think(self, state: dict) -> str:
        return f"Decomposing task and routing to specialized agent bot: {state.get('task', 'no task')}"

    def act(self, thought: str, state: dict) -> Any:
        self._emit(EventKind.TOOL_CALL, "Routing action")
        result = "Orchestrated dispatch done"
        self._emit(EventKind.TOOL_RESULT, result)
        return result

    def is_done(self, state: dict) -> bool:
        return True
