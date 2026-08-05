"""AgentHarness — session management, tool selection, skill injection, and PC control."""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from core.skill_registry import SkillRegistry

logger = logging.getLogger(__name__)

class AgentHarness:
    """Orchestrates agent execution, skill selection, and full system/PC tool execution."""

    def __init__(self, skill_registry: Optional[SkillRegistry] = None):
        self.skill_registry = skill_registry or SkillRegistry()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, session_id: str, agent_type: str = "shadowcoder") -> Dict[str, Any]:
        """Initialize a session with Progressive Disclosure skill index."""
        skills_summary = self.skill_registry.get_progressive_context()
        session = {
            "session_id": session_id,
            "agent_type": agent_type,
            "skills_index": skills_summary,
            "active_skills": [],
            "trace_log": [],
        }
        self.active_sessions[session_id] = session
        return session

    def select_skill(self, session_id: str, skill_name: str) -> Optional[Dict[str, Any]]:
        """Load full skill instructions into active context for the session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None

        skill_data = self.skill_registry.get_full_skill(skill_name)
        if skill_data:
            if skill_name not in session["active_skills"]:
                session["active_skills"].append(skill_name)
            logger.info(f"Loaded full skill '{skill_name}' for session {session_id}")
        return skill_data

    def log_execution_trace(
        self,
        session_id: str,
        action: str,
        details: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record execution step in session trace log for Skill Factory & ReflectionEngine."""
        session = self.active_sessions.get(session_id)
        trace_entry = {
            "session_id": session_id,
            "action": action,
            "details": details,
            "success": success,
            "error": error,
        }
        if session:
            session["trace_log"].append(trace_entry)
        return trace_entry
