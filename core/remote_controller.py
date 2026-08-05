"""RemoteController — iPhone and mobile remote wrapper for PC execution & session management."""

import subprocess
import os
import sys
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RemoteController:
    """Provides secure PC remote management capabilities for mobile (iPhone Safari/PWA) access."""

    def __init__(self):
        pass

    def get_system_status(self) -> Dict[str, Any]:
        """Return system status summary for mobile dashboard."""
        return {
            "status": "online",
            "os": sys.platform,
            "python_version": sys.version,
            "active_processes": self._get_process_count(),
        }

    def execute_pc_command(self, command: str) -> Dict[str, Any]:
        """Execute system command on host PC and return output."""
        try:
            res = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "command": command,
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
            }
        except Exception as e:
            return {
                "command": command,
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
            }

    def _get_process_count(self) -> int:
        try:
            if sys.platform == "win32":
                res = subprocess.run("tasklist", shell=True, capture_output=True, text=True)
                return len(res.stdout.splitlines()) - 3
            else:
                res = subprocess.run("ps aux", shell=True, capture_output=True, text=True)
                return len(res.stdout.splitlines()) - 1
        except Exception:
            return 0
