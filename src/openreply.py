"""
OpenReply — Self-hosted Instagram comment-to-DM automation for ShadowRealm.
Replaces ManyChat with a free, privacy-first alternative using the official Meta API.

GitHub: https://github.com/diwenne/openreply
Stack: Next.js, Postgres, Redis, BullMQ
Requirements: Docker, Meta Business Account, Instagram Basic Display API credentials

This module provides:
- Docker Compose launcher for the OpenReply stack
- Status checking for the running service
- Setup guide generator for Meta API credentials
"""

import os
import shutil
import subprocess
import webbrowser
from typing import Dict, Any

OPENREPLY_GITHUB = "https://github.com/diwenne/openreply"
META_DEVELOPER_PORTAL = "https://developers.facebook.com/apps/"
OPENREPLY_DEFAULT_PORT = 3000
OPENREPLY_COMPOSE_DIR = os.path.expanduser("~/.shadowrealm/openreply")

OPENREPLY_COMPOSE = """
version: '3.8'
services:
  openreply:
    image: node:20-alpine
    working_dir: /app
    volumes:
      - ./app:/app
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://openreply:openreply@db:5432/openreply
      - REDIS_URL=redis://redis:6379
      - META_ACCESS_TOKEN=${META_ACCESS_TOKEN}
      - META_VERIFY_TOKEN=${META_VERIFY_TOKEN}
      - INSTAGRAM_ACCOUNT_ID=${INSTAGRAM_ACCOUNT_ID}
    depends_on:
      - db
      - redis
    command: sh -c "npm install && npm run dev"

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: openreply
      POSTGRES_PASSWORD: openreply
      POSTGRES_DB: openreply
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
"""

OPENREPLY_ENV_TEMPLATE = """# OpenReply — Meta API Credentials
# Get these from: https://developers.facebook.com/apps/

META_ACCESS_TOKEN=your_meta_long_lived_token_here
META_VERIFY_TOKEN=any_random_string_you_choose
INSTAGRAM_ACCOUNT_ID=your_instagram_business_account_id
"""


def setup_openreply() -> Dict[str, Any]:
    """Clone OpenReply repo and write Docker Compose config to ~/.shadowrealm/openreply."""
    if not shutil.which("docker"):
        return {
            "ok": False,
            "error": "Docker not found. Install Docker Desktop first.",
            "docker_url": "https://docs.docker.com/desktop/",
        }

    os.makedirs(OPENREPLY_COMPOSE_DIR, exist_ok=True)
    compose_path = os.path.join(OPENREPLY_COMPOSE_DIR, "docker-compose.yml")
    env_path = os.path.join(OPENREPLY_COMPOSE_DIR, ".env")

    # Write compose file
    with open(compose_path, "w") as f:
        f.write(OPENREPLY_COMPOSE)

    # Write env template if not already present
    if not os.path.exists(env_path):
        with open(env_path, "w") as f:
            f.write(OPENREPLY_ENV_TEMPLATE)

    # Clone the OpenReply repo into the app subdirectory
    app_dir = os.path.join(OPENREPLY_COMPOSE_DIR, "app")
    if not os.path.exists(app_dir):
        res = subprocess.run(
            f"git clone {OPENREPLY_GITHUB} {app_dir}",
            shell=True, capture_output=True, text=True
        )
        if res.returncode != 0:
            return {"ok": False, "error": f"Git clone failed: {res.stderr.strip()}"}

    return {
        "ok": True,
        "status": "setup_complete",
        "compose_dir": OPENREPLY_COMPOSE_DIR,
        "next_steps": [
            f"1. Edit {env_path} with your Meta API credentials",
            f"2. Get credentials at: {META_DEVELOPER_PORTAL}",
            "3. Run Option [16] → Start OpenReply to launch the stack",
        ],
        "env_file": env_path,
        "meta_portal": META_DEVELOPER_PORTAL,
    }


def start_openreply() -> Dict[str, Any]:
    """Launch the OpenReply Docker Compose stack."""
    if not shutil.which("docker"):
        return {"ok": False, "error": "Docker not found."}

    compose_path = os.path.join(OPENREPLY_COMPOSE_DIR, "docker-compose.yml")
    if not os.path.exists(compose_path):
        return {
            "ok": False,
            "error": "OpenReply not set up yet. Run setup_openreply() first.",
        }

    res = subprocess.run(
        "docker compose up -d",
        shell=True, cwd=OPENREPLY_COMPOSE_DIR,
        capture_output=True, text=True
    )
    if res.returncode == 0:
        return {
            "ok": True,
            "status": "running",
            "url": f"http://localhost:{OPENREPLY_DEFAULT_PORT}",
            "message": "OpenReply stack started! Open in browser.",
        }
    return {"ok": False, "error": res.stderr.strip()}


def stop_openreply() -> Dict[str, Any]:
    """Stop the OpenReply Docker Compose stack."""
    if not os.path.exists(OPENREPLY_COMPOSE_DIR):
        return {"ok": False, "error": "OpenReply not set up."}
    res = subprocess.run(
        "docker compose down",
        shell=True, cwd=OPENREPLY_COMPOSE_DIR,
        capture_output=True, text=True
    )
    return {"ok": res.returncode == 0, "output": res.stdout.strip()}


def get_openreply_status() -> Dict[str, Any]:
    """Check if OpenReply services are running."""
    if not shutil.which("docker"):
        return {"ok": False, "docker": False}
    res = subprocess.run(
        "docker compose ps --format json",
        shell=True, cwd=OPENREPLY_COMPOSE_DIR,
        capture_output=True, text=True
    )
    setup_done = os.path.exists(os.path.join(OPENREPLY_COMPOSE_DIR, "docker-compose.yml"))
    return {
        "ok": True,
        "setup_done": setup_done,
        "compose_dir": OPENREPLY_COMPOSE_DIR,
        "services": res.stdout.strip() or "Not running",
        "url": f"http://localhost:{OPENREPLY_DEFAULT_PORT}" if setup_done else None,
        "github": OPENREPLY_GITHUB,
        "meta_portal": META_DEVELOPER_PORTAL,
    }
