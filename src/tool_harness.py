"""
Dynamic Tool Discovery & Error Diagnostic Harness for Odysseus.
Automatically inspects host CLI toolchains (docker, pytest, cargo, npm, gh, python)
and provides automated error traceback extraction for self-healing agent loops.
"""

import os
import shutil
import subprocess
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

SUPPORTED_TOOLS = [
    "git", "docker", "pytest", "python", "node", "npm", "cargo", "go", "gh", 
    "tailscale", "strix", "semgrep", "trivy", "bandit", "pipelock", "agent-audit"
]

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

def execute_cli_anything(command_str: str, cwd: str = "") -> Dict[str, Any]:
    """Execute ANY host program, CLI tool, or custom script with auto-diagnostics.
    Allows Odysseus agents and users to execute any arbitrary executable installed on PATH.
    """
    if not command_str or not command_str.strip():
        return {"ok": False, "error": "Empty command provided."}
        
    target_cwd = cwd if cwd and os.path.exists(cwd) else None
    
    try:
        res = subprocess.run(
            command_str,
            shell=True,
            capture_output=True,
            text=True,
            cwd=target_cwd,
            timeout=120
        )
        stdout = res.stdout.strip()
        stderr = res.stderr.strip()
        combined_output = f"{stdout}\n{stderr}".strip()
        diagnostics = parse_error_diagnostics(combined_output)
        
        return {
            "ok": res.returncode == 0,
            "returncode": res.returncode,
            "command": command_str,
            "stdout": stdout,
            "stderr": stderr,
            "diagnostics": diagnostics
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Command '{command_str}' timed out after 120 seconds."}
    except Exception as e:
        return {"ok": False, "error": f"Execution error: {e}"}
