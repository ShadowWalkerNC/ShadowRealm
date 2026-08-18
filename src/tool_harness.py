"""
Dynamic Tool Discovery & Error Diagnostic Harness for Odysseus.
Automatically inspects host CLI toolchains (docker, pytest, cargo, npm, gh, python)
and provides automated error traceback extraction for self-healing agent loops.
"""

import os
import shutil
import subprocess
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

SUPPORTED_TOOLS = [
    # Core Developer & Build Tools
    "git", "docker", "python", "pip", "uv", "node", "npm", "npx", "yarn", "pnpm",
    "cargo", "go", "rustc", "cmake", "make", "gh", "tailscale",
    # Security, Auditing & SAST
    "strix", "semgrep", "trivy", "bandit", "pipelock", "agent-audit",
    "gitleaks", "syft", "grype",
    # Linters & Formatters
    "ruff", "black", "eslint", "prettier",
    # Local AI Inference (Zero Token Cost)
    "needle",
    # AI Token Cost Analytics
    "codeburn",
    # API Client (git-native Postman alternative)
    "yaak",
    # Rust-powered CLI Power Tools
    "rg", "fzf", "zoxide", "bat", "eza", "fd", "starship",
]

def mass_update_toolchains() -> Dict[str, Any]:
    """Massively perform updates across all installed developer tools and package managers."""
    results = {}
    
    # 1. Update Python packages via pip / uv
    if shutil.which("uv"):
        res = subprocess.run("uv self update", shell=True, capture_output=True, text=True)
        results["uv"] = res.stdout.strip() or "uv updated"
    elif shutil.which("pip"):
        res = subprocess.run("python -m pip install --upgrade pip setuptools wheel", shell=True, capture_output=True, text=True)
        results["pip"] = "pip updated"
        
    # 2. Update Node.js global packages
    if shutil.which("npm"):
        res = subprocess.run("npm update -g", shell=True, capture_output=True, text=True)
        results["npm_globals"] = "npm global packages updated"

    # 3. Update Rust cargo binaries
    if shutil.which("cargo"):
        res = subprocess.run("cargo install-update -a", shell=True, capture_output=True, text=True)
        results["cargo"] = "cargo binaries updated"

    # 4. Update GitHub CLI extensions
    if shutil.which("gh"):
        res = subprocess.run("gh extension upgrade --all", shell=True, capture_output=True, text=True)
        results["gh_extensions"] = "gh extensions upgraded"

    return {
        "ok": True,
        "updated_components": len(results),
        "details": results
    }

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


# ---------------------------------------------------------------------------
# 🌵 CactusNeedle — Local AI Tool-Call Inference (Zero Cloud, Zero Token Cost)
# ---------------------------------------------------------------------------

def install_needle() -> Dict[str, Any]:
    """Install cactus-needle Python package if not already present."""
    try:
        import needle  # type: ignore
        return {"ok": True, "status": "already_installed"}
    except ImportError:
        res = subprocess.run(
            "pip install cactus-needle --quiet",
            shell=True, capture_output=True, text=True
        )
        if res.returncode == 0:
            return {"ok": True, "status": "installed"}
        return {"ok": False, "error": res.stderr.strip()}


def run_needle_inference(prompt: str, tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """Run a local AI inference via CactusNeedle for tool-call dispatch.

    CactusNeedle converts a natural-language prompt into a structured JSON
    tool call using a 14MB on-device model — no cloud, no API key, no token cost.

    Args:
        prompt: Natural language instruction (e.g. "Search for Python files modified today")
        tools:  List of tool schema dicts (OpenAI-style function definitions). If None,
                falls back to a raw text completion.

    Returns:
        dict with keys: ok, result (the JSON tool call or text), model, tokens_used
    """
    # Ensure needle is installed
    install_result = install_needle()
    if not install_result["ok"]:
        return {"ok": False, "error": f"needle not installed: {install_result.get('error')}"}

    try:
        import needle as nd  # type: ignore

        checkpoint = nd.load_checkpoint()
        result = nd.generate(
            checkpoint=checkpoint,
            prompt=prompt,
            tools=tools or [],
            max_tokens=512,
        )
        return {
            "ok": True,
            "model": "needle-2 (14MB local, zero cloud)",
            "prompt": prompt,
            "result": result,
            "tokens_used": 0,   # On-device: no API tokens consumed
            "cloud_calls": 0,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

