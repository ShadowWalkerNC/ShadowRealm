"""
Odysseus Native CLI Harness & Master Dev Suite (`cli.py`).
Provides full access to installed CLI tools, local repositories, and project orchestration.
"""

import sys
import os
import json
import shutil
import subprocess
from pathlib import Path

def scan_installed_cli_tools():
    """Scan and list common installed CLI software on host."""
    tools = ["git", "docker", "python", "py", "node", "npm", "npx", "cargo", "go", "rustc", "tailscale", "gh", "code", "kubectl"]
    found = {}
    for tool in tools:
        path = shutil.which(tool)
        if path:
            found[tool] = path
    return found

def scan_local_repositories():
    """Scan parent directory for local git repositories and projects."""
    projects_dir = Path.cwd().parent
    repos = []
    if projects_dir.exists():
        for item in projects_dir.iterdir():
            if item.is_dir() and (item / ".git").exists():
                repos.append({
                    "name": item.name,
                    "path": str(item.resolve()),
                })
    return repos

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "scan":
        print("=== Odysseus Local Environment & Master CLI Dev Suite Scan ===")
        print("\nInstalled CLI Tools:")
        for tool, path in scan_installed_cli_tools().items():
            print(f"  - {tool:12s}: {path}")

        print("\nLocal Repositories & Projects:")
        for repo in scan_local_repositories():
            print(f"  - {repo['name']:20s}: {repo['path']}")

    elif sys.argv[1] == "run" and len(sys.argv) > 2:
        cmd = " ".join(sys.argv[2:])
        print(f"Executing CLI tool command: {cmd}")
        subprocess.run(cmd, shell=True)
    else:
        print("Usage:")
        print("  py cli.py scan       - Scan all installed CLI tools & projects")
        print("  py cli.py run <cmd>  - Run any installed CLI tool directly")

if __name__ == "__main__":
    main()
