"""
WorkflowTreeEngine — Maps AI tasks to directory trees (prompts, tools, data, subagents).
Enforces file-tree native execution and progressive disclosure.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class TaskNode:
    """Represents a single task node in a file tree workflow."""

    def __init__(self, task_dir: Path):
        self.task_dir = task_dir
        self.name = task_dir.name
        self.prompts_dir = task_dir / "prompts"
        self.tools_dir = task_dir / "tools"
        self.data_dir = task_dir / "data"
        self.subagents_dir = task_dir / "subagents"

    def load_prompts(self) -> Dict[str, str]:
        """Load all system/user prompt templates from prompts/ folder."""
        prompts = {}
        if self.prompts_dir.exists():
            for p_file in self.prompts_dir.glob("*.md"):
                prompts[p_file.stem] = p_file.read_text(encoding="utf-8")
        return prompts

    def load_tool_selectors(self) -> List[str]:
        """Load required MCP / local tool selectors from tools/ folder."""
        tools = []
        if self.tools_dir.exists():
            selector_file = self.tools_dir / "mcp_selector.json"
            if selector_file.exists():
                try:
                    data = json.loads(selector_file.read_text(encoding="utf-8"))
                    tools.extend(data.get("tools", []))
                except Exception as e:
                    logger.error(f"Error reading tool selector {selector_file}: {e}")
        return tools

    def load_subagent_configs(self) -> List[Dict[str, Any]]:
        """Load subagent definitions from subagents/ folder."""
        agents = []
        if self.subagents_dir.exists():
            for a_file in self.subagents_dir.glob("*.json"):
                try:
                    data = json.loads(a_file.read_text(encoding="utf-8"))
                    agents.append(data)
                except Exception as e:
                    logger.error(f"Error loading subagent {a_file}: {e}")
        return agents

    def to_dict(self) -> Dict[str, Any]:
        """Return lightweight directory summary for progressive disclosure."""
        return {
            "name": self.name,
            "path": str(self.task_dir.resolve()),
            "has_prompts": self.prompts_dir.exists(),
            "has_tools": self.tools_dir.exists(),
            "has_data": self.data_dir.exists(),
            "has_subagents": self.subagents_dir.exists(),
        }


class WorkflowTreeEngine:
    """Manages workspace directory workflow trees."""

    def __init__(self, workflows_root: Optional[str] = None):
        if workflows_root:
            self.workflows_root = Path(workflows_root)
        else:
            self.workflows_root = Path(__file__).parent.parent / "workflows"
        self.workflows_root.mkdir(parents=True, exist_ok=True)

    def scan_workflows(self) -> List[Dict[str, Any]]:
        """Discover all workflows and sub-task directory nodes."""
        workflows = []
        if not self.workflows_root.exists():
            return workflows

        for wf_dir in self.workflows_root.iterdir():
            if wf_dir.is_dir():
                tasks = []
                for child in wf_dir.iterdir():
                    if child.is_dir() and not child.name.startswith("."):
                        node = TaskNode(child)
                        tasks.append(node.to_dict())
                workflows.append({
                    "workflow": wf_dir.name,
                    "path": str(wf_dir.resolve()),
                    "tasks": tasks,
                })

        return workflows

    def create_task_node(self, workflow_name: str, task_name: str) -> Dict[str, Any]:
        """Initialize a new task folder with prompts/, tools/, data/, and subagents/."""
        task_dir = self.workflows_root / workflow_name / task_name
        (task_dir / "prompts").mkdir(parents=True, exist_ok=True)
        (task_dir / "tools").mkdir(parents=True, exist_ok=True)
        (task_dir / "data").mkdir(parents=True, exist_ok=True)
        (task_dir / "subagents").mkdir(parents=True, exist_ok=True)

        # Default system prompt stub
        system_prompt = task_dir / "prompts" / "system.md"
        if not system_prompt.exists():
            system_prompt.write_text(f"# Task: {task_name}\nSystem prompt instructions...", encoding="utf-8")

        # Default tool selector stub
        tool_selector = task_dir / "tools" / "mcp_selector.json"
        if not tool_selector.exists():
            tool_selector.write_text(json.dumps({"tools": ["git", "exec"]}, indent=2), encoding="utf-8")

        node = TaskNode(task_dir)
        return node.to_dict()
