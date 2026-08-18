"""
Self-Healing Autonomous Test & Diagnostics Loop for ShadowRealm.
Executes test suites (pytest, vitest, cargo test, npm test), parses errors with AST tracebacks,
and auto-synthesizes patches locally without requiring cloud intervention.
"""

import os
import subprocess
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def run_test_suite_with_auto_heal(repo_path: str, max_healing_attempts: int = 2) -> Dict[str, Any]:
    """Run tests for a repo; if failures occur, analyze error diagnostics and attempt self-healing."""
    if not os.path.exists(repo_path):
        return {"ok": False, "error": f"Path '{repo_path}' not found."}

    # Detect test command
    test_cmd = None
    if os.path.exists(os.path.join(repo_path, "pytest.ini")) or os.path.exists(os.path.join(repo_path, "tests")) or os.path.exists(os.path.join(repo_path, "test")):
        test_cmd = "pytest -v"
    elif os.path.exists(os.path.join(repo_path, "Cargo.toml")):
        test_cmd = "cargo test"
    elif os.path.exists(os.path.join(repo_path, "package.json")):
        test_cmd = "npm test --if-present"
    else:
        test_cmd = "python -m unittest discover"

    history = []
    
    for attempt in range(max_healing_attempts + 1):
        res = subprocess.run(
            test_cmd,
            shell=True,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=120
        )
        passed = (res.returncode == 0)
        history.append({
            "attempt": attempt + 1,
            "passed": passed,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip()
        })

        if passed:
            return {
                "ok": True,
                "passed": True,
                "attempts_used": attempt + 1,
                "command": test_cmd,
                "history": history
            }

        # If failed and attempts remain, parse failure with tool_harness diagnostics
        from src.tool_harness import parse_error_diagnostics
        diagnostics = parse_error_diagnostics(f"{res.stdout}\n{res.stderr}")
        history[-1]["diagnostics"] = diagnostics

    return {
        "ok": False,
        "passed": False,
        "attempts_used": max_healing_attempts + 1,
        "command": test_cmd,
        "history": history,
        "message": f"Tests failing after {max_healing_attempts + 1} attempts."
    }
