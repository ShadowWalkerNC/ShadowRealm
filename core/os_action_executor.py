"""
C120 — OS Action Executor
Controls sandboxed system updates with explicit permission gates.
"""
from __future__ import annotations
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OSActionExecutor:
    def __init__(self, allowed_commands: list[str]):
        self.allowed_commands = allowed_commands

    def execute_command(self, cmd: str) -> Dict[str, Any]:
        base_cmd = cmd.split(" ")[0]
        if base_cmd not in self.allowed_commands:
            logger.warning("Blocked command execution: %s", cmd)
            return {"status": "blocked", "cmd": cmd}
            
        logger.info("Executing allowed OS command: %s", cmd)
        return {"status": "executed", "cmd": cmd, "output": f"Mock output for {cmd}"}
