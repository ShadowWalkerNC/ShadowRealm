"""
CustomBotManager — Discovers, loads, and manages Buzz-style custom agent bots.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class CustomBotManager:
    """Manages custom agent bots mapped to skills, MCP tools, and workflow boundaries."""

    def __init__(self, bots_dir: Optional[str] = None):
        if bots_dir:
            self.bots_dir = Path(bots_dir)
        else:
            self.bots_dir = Path(__file__).parent.parent / "bots"
        self.bots_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_default_bots()

    def _ensure_default_bots(self):
        """Scaffold default Buzz-style custom bots if none exist."""
        qa_bot_dir = self.bots_dir / "qa_auditor_bot"
        if not qa_bot_dir.exists():
            qa_bot_dir.mkdir(parents=True, exist_ok=True)
            (qa_bot_dir / "bot.json").write_text(json.dumps({
                "bot_id": "qa_auditor_bot",
                "name": "QA Audit Bot",
                "description": "Performs 4-stage repository plan, code, build, and user tests.",
                "skills": ["repo_audit", "code_review"],
                "allowed_mcps": ["filesystem", "exec"]
            }, indent=2), encoding="utf-8")

        release_bot_dir = self.bots_dir / "release_bot"
        if not release_bot_dir.exists():
            release_bot_dir.mkdir(parents=True, exist_ok=True)
            (release_bot_dir / "bot.json").write_text(json.dumps({
                "bot_id": "release_bot",
                "name": "Release Bot",
                "description": "Automates documentation generation, version tagging, and packaging.",
                "skills": ["doc_write", "git_ops"],
                "allowed_mcps": ["filesystem", "git"]
            }, indent=2), encoding="utf-8")

    def list_bots(self) -> List[Dict[str, Any]]:
        """List all custom agent bots."""
        bots = []
        for b_dir in self.bots_dir.iterdir():
            if b_dir.is_dir():
                cfg_file = b_dir / "bot.json"
                if cfg_file.exists():
                    try:
                        data = json.loads(cfg_file.read_text(encoding="utf-8"))
                        data["path"] = str(b_dir.resolve())
                        bots.append(data)
                    except Exception as e:
                        logger.error(f"Error reading bot config {cfg_file}: {e}")
        return bots
