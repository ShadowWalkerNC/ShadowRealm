"""
Dynamic Tool Discovery & Error Diagnostic Harness for Odysseus.
Automatically inspects host CLI toolchains (docker, pytest, cargo, npm, gh, python)
and provides automated error traceback extraction for self-healing agent loops.
"""

import shutil
import subprocess
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

SUPPORTED_TOOLS = ["git", "docker", "pytest", "python", "node", "npm", "cargo", "go", "gh", "tailscale"]

def discover_host_tools() -> Dict[str, Any]:
    """Scan host OS for installed developer CLI tools."""
    discovered = {}
    for tool in SUPPORTED_TOOLS:
        path = shutil.which(tool)
        discovered[tool] = {
            "installed": bool(path),
            "path": path or ""
        }
    return {
        "count": sum(1 for t in discovered.values() if t["installed"]),
        "tools": discovered
    }

def parse_error_diagnostics(cmd_output: str) -> Dict[str, Any]:
    """Extract actionable tracebacks and failure causes from raw terminal output."""
    lines = cmd_output.splitlines()
    error_summary = []
    
    for line in lines:
        if "Error:" in line or "FAILED" in line or "Traceback" in line or "Exception" in line:
            error_summary.append(line.strip())
            
    return {
        "has_error": len(error_summary) > 0,
        "error_lines_count": len(error_summary),
        "primary_errors": error_summary[:5]
    }
