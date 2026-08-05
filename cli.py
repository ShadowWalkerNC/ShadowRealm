#!/usr/bin/env python3
"""
ShadowRealm / Odysseus Native CLI (odysseus-cli)

Provides full terminal access to host programs, CLI tools, GitHub repos,
skills engine, execution shell, memory system, and remote control.
"""

import sys
import os
import argparse
import subprocess
import json
import urllib.request
import urllib.parse
from pathlib import Path

DEFAULT_SERVER_URL = os.environ.get("ODYSSEUS_SERVER_URL", "http://localhost:7000")

def get_installed_cli_tools():
    """Scan system PATH for available CLI tools and git repositories."""
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    found_tools = set()
    common_tools = [
        "git", "docker", "gh", "python", "node", "npm", "npx", "pip", "uv",
        "kubectl", "terraform", "aws", "gcloud", "curl", "wget", "ffmpeg", "make", "gcc", "go", "cargo", "rustc"
    ]
    
    for tool in common_tools:
        if shutil_which(tool):
            found_tools.add(tool)

    return sorted(list(found_tools))

def shutil_which(cmd):
    """Check if command exists on system PATH."""
    for path in os.environ.get("PATH", "").split(os.pathsep):
        p = Path(path) / cmd
        if p.exists() and not p.is_dir():
            return str(p)
        if sys.platform == "win32":
            p_exe = Path(path) / f"{cmd}.exe"
            if p_exe.exists():
                return str(p_exe)
    return None

def scan_github_repos(root_dir=None):
    """Scan local directory for GitHub repositories."""
    root = Path(root_dir) if root_dir else Path.home() / "Documents"
    repos = []
    if not root.exists():
        return repos
    
    try:
        for git_dir in root.glob("**/.git"):
            if git_dir.is_dir():
                repos.append(str(git_dir.parent.resolve()))
                if len(repos) >= 50: # Cap scan
                    break
    except Exception:
        pass
    return repos

def exec_local_cmd(cmd):
    """Direct local execution of system/CLI tools."""
    print(f"\033[36m[Executing CLI]\033[0m {cmd}\n")
    res = subprocess.run(cmd, shell=True)
    return res.returncode

def main():
    parser = argparse.ArgumentParser(
        prog="odysseus",
        description="ShadowRealm CLI — Terminal harness with full local system tool access."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # exec subcommand
    exec_parser = subparsers.add_parser("exec", help="Run a CLI tool or system command directly")
    exec_parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to execute")

    # scan subcommand
    scan_parser = subparsers.add_parser("scan", help="Scan host PC for installed CLI software & GitHub repos")
    scan_parser.add_argument("--dir", help="Directory to scan for git repos")

    # skills subcommand
    skills_parser = subparsers.add_parser("skills", help="List registered skills")

    # pair subcommand
    pair_parser = subparsers.add_parser("pair", help="Show mobile pairing QR link and Tailscale IP")

    # interactive mode if no subcommand
    args = parser.parse_args()

    if args.command == "exec":
        cmd_str = " ".join(args.cmd)
        if not cmd_str:
            print("Error: No command provided.")
            sys.exit(1)
        sys.exit(exec_local_cmd(cmd_str))

    elif args.command == "scan":
        print("=== Scanning Host Environment ===")
        tools = get_installed_cli_tools()
        print(f"[+] Installed CLI Software ({len(tools)}): {', '.join(tools)}")
        print("\nScanning for GitHub repositories...")
        repos = scan_github_repos(args.dir)
        print(f"[+] Local Repositories Found ({len(repos)}):")
        for repo in repos:
            print(f"  * {repo}")

    elif args.command == "pair":
        try:
            req = urllib.request.urlopen(f"{DEFAULT_SERVER_URL}/api/remote/pairing")
            data = json.loads(req.read().decode())
            print(f"\033[36mTailscale IP:\033[0m {data.get('tailscale_ip')}")
            print(f"\033[36miPhone URL:\033[0m   {data.get('iphone_url')}")
            print(f"\033[36mAndroid URL:\033[0m  {data.get('android_url')}")
            print(f"\nOpen \033[32m{DEFAULT_SERVER_URL}/api/remote/pair\033[0m in browser for QR Code.")
        except Exception as e:
            print(f"Error connecting to ShadowRealm server at {DEFAULT_SERVER_URL}: {e}")

    elif args.command == "skills":
        try:
            req = urllib.request.urlopen(f"{DEFAULT_SERVER_URL}/api/skills")
            skills = json.loads(req.read().decode())
            print("\033[35m=== Registered Skills ===\033[0m")
            for s in skills:
                name = s.get("name", s) if isinstance(s, dict) else s
                desc = s.get("description", "") if isinstance(s, dict) else ""
                print(f"• \033[1m{name}\033[0m: {desc}")
        except Exception as e:
            print(f"Error listing skills: {e}")

    else:
        # Interactive Odysseus shell prompt
        print("\033[35m⛵ ShadowRealm / Odysseus CLI Harness (Terminal Mode)\033[0m")
        print("Type \033[32m'scan'\033[0m to list local tools, or enter any system command/prompt.\n")
        try:
            while True:
                user_in = input("\033[36modysseus>\033[0m ").strip()
                if not user_in:
                    continue
                if user_in.lower() in ("exit", "quit"):
                    break
                if user_in.lower() == "scan":
                    tools = get_installed_cli_tools()
                    print(f"CLI Tools: {', '.join(tools)}")
                    continue
                exec_local_cmd(user_in)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting CLI.")

if __name__ == "__main__":
    main()
