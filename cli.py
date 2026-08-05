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

    # devsuite subcommand
    devsuite_parser = subparsers.add_parser("devsuite", help="Master CLI Dev Suite — access and orchestrate local CLI tools")
    devsuite_parser.add_argument("action", choices=["list", "run", "status"], nargs="?", default="list", help="DevSuite action")
    devsuite_parser.add_argument("--tool", help="Specific tool to invoke")
    devsuite_parser.add_argument("--args", nargs=argparse.REMAINDER, help="Arguments for the tool")

    # interactive mode if no subcommand
    args = parser.parse_args()

    if args.command == "devsuite":
        print("=== Master CLI Dev Suite ===")
        tools = get_installed_cli_tools()
        if args.action == "list" or not args.action:
            print(f"[+] Master Dev Suite Toolset ({len(tools)} tools active):")
            for t in tools:
                loc = shutil_which(t)
                print(f"  * {t:<12} -> {loc}")
        elif args.action == "run":
            if not args.tool:
                print("Error: --tool required for run action.")
                sys.exit(1)
            tool_path = shutil_which(args.tool)
            if not tool_path:
                print(f"Error: Tool '{args.tool}' not found on system PATH.")
                sys.exit(1)
            tool_args = " ".join(args.args) if args.args else ""
            full_cmd = f"{tool_path} {tool_args}".strip()
            sys.exit(exec_local_cmd(full_cmd))
        elif args.action == "status":
            print(f"[+] DevSuite Engine: Operational")
            print(f"[+] Connected Odysseus Server: {DEFAULT_SERVER_URL}")
            print(f"[+] Available Tool Integrations: {len(tools)}")

    elif args.command == "exec":
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
            print(f"Tailscale IP: {data.get('tailscale_ip')}")
            print(f"iPhone URL:   {data.get('iphone_url')}")
            print(f"Android URL:  {data.get('android_url')}")
            print(f"\nOpen {DEFAULT_SERVER_URL}/api/remote/pair in browser for QR Code.")
        except Exception as e:
            print(f"Error connecting to ShadowRealm server at {DEFAULT_SERVER_URL}: {e}")

    elif args.command == "skills":
        try:
            req = urllib.request.urlopen(f"{DEFAULT_SERVER_URL}/api/skills")
            skills = json.loads(req.read().decode())
            print("=== Registered Skills ===")
            for s in skills:
                name = s.get("name", s) if isinstance(s, dict) else s
                desc = s.get("description", "") if isinstance(s, dict) else ""
                print(f"* {name}: {desc}")
        except Exception as e:
            print(f"Error listing skills: {e}")

    else:
        # Interactive Odysseus shell prompt
        print("⛵ ShadowRealm / Odysseus CLI Harness (Master Dev Suite Mode)")
        print("Type 'devsuite' or 'scan' to list local tools, or enter any system command/prompt.\n")
        try:
            while True:
                user_in = input("odysseus> ").strip()
                if not user_in:
                    continue
                if user_in.lower() in ("exit", "quit"):
                    break
                if user_in.lower() == "devsuite":
                    tools = get_installed_cli_tools()
                    print(f"Master Dev Suite Tools: {', '.join(tools)}")
                    continue
                if user_in.lower() == "scan":
                    tools = get_installed_cli_tools()
                    print(f"CLI Tools: {', '.join(tools)}")
                    continue
                exec_local_cmd(user_in)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting CLI.")

if __name__ == "__main__":
    main()
