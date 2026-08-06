"""
ToolCondenser — Condenses raw MCP tool definitions into task-scoped lightweight packages.
"""

import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ToolCondenser:
    """Filters and condenses available system tools & MCP servers per task directory."""

    def __init__(self, mcp_manager: Optional[Any] = None):
        self.mcp_manager = mcp_manager

    def condense_tools_for_task(self, requested_tools: List[str], available_mcps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Produce a condensed tool bundle (~100 tokens max) for an active task node."""
        active_tools = []
        for tool in requested_tools:
            active_tools.append({
                "name": tool,
                "status": "ready",
                "scope": "task_local"
            })

        return {
            "task_tools_count": len(active_tools),
            "condensed_tools": active_tools,
        }
