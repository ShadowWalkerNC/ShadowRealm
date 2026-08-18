"""
WebVM (Leaningtech) integration for ShadowRealm.
Provides helpers to open, fork, and configure a WebVM Linux environment
directly from the CLI — no installation required, runs 100% in browser.

GitHub: https://github.com/leaningtech/webvm
Live demo: https://webvm.io
"""

import os
import subprocess
import webbrowser
from typing import Dict, Any

WEBVM_LIVE_URL = "https://webvm.io"
WEBVM_GITHUB = "https://github.com/leaningtech/webvm"
WEBVM_FORK_TEMPLATE = "https://github.com/leaningtech/webvm/fork"

# Prebuilt CheerpX environments available on WebVM.io
WEBVM_ENVIRONMENTS = {
    "debian": {
        "url": "https://webvm.io",
        "description": "Debian Buster x86 (default) — full shell, bash, python3, gcc",
        "use_case": "General Linux scripting, testing CLI tools",
    },
    "alpine": {
        "url": "https://webvm.io/?distro=alpine",
        "description": "Alpine Linux — minimal, fast, musl-based",
        "use_case": "Lightweight sandboxed testing",
    },
    "xorg": {
        "url": "https://webvm.io/?distro=graphical",
        "description": "Debian + Xorg graphical desktop in browser",
        "use_case": "GUI application testing without a VM",
    },
}


def open_webvm(env: str = "debian") -> Dict[str, Any]:
    """Open a WebVM Linux environment in the default browser.

    Args:
        env: One of 'debian', 'alpine', 'xorg'

    Returns:
        dict with ok, url, description
    """
    if env not in WEBVM_ENVIRONMENTS:
        env = "debian"
    info = WEBVM_ENVIRONMENTS[env]
    try:
        webbrowser.open(info["url"])
        return {
            "ok": True,
            "env": env,
            "url": info["url"],
            "description": info["description"],
            "use_case": info["use_case"],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def list_webvm_environments() -> Dict[str, Any]:
    """Return all available WebVM environments."""
    return {
        "ok": True,
        "environments": WEBVM_ENVIRONMENTS,
        "github": WEBVM_GITHUB,
        "fork_url": WEBVM_FORK_TEMPLATE,
    }


def open_webvm_github() -> Dict[str, Any]:
    """Open the WebVM GitHub repo for forking/deployment."""
    try:
        webbrowser.open(WEBVM_GITHUB)
        return {"ok": True, "url": WEBVM_GITHUB}
    except Exception as e:
        return {"ok": False, "error": str(e)}
