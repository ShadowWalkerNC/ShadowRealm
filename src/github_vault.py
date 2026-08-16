"""
GitHub Data Vault Harvester for ShadowRealm.
Uses stored GitHub PAT token to harvest, index, and organize owned, starred,
and liked GitHub repositories into a local data vault for offline study and tool building.
"""

import json
import logging
import urllib.request
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

VAULT_FILE = Path(__file__).resolve().parent.parent / "data" / "vault.json"

def _make_github_request(url: str, token: str) -> List[Dict[str, Any]]:
    """Helper to perform authenticated GitHub API requests."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "ShadowRealm-Vault-Harvester")
    req.add_header("Accept", "application/vnd.github.v3+json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
        
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return data if isinstance(data, list) else [data]
    except Exception as e:
        logger.warning(f"GitHub API request failed for {url}: {e}")
    return []

def harvest_github_vault() -> Dict[str, Any]:
    """Harvest owned and starred repositories into data/vault.json."""
    from src.settings import get_setting
    token = get_setting("github_token", "")
    
    if not token:
        return {"ok": False, "error": "No GitHub PAT token configured in settings."}

    # 1. Fetch authenticated user profile
    user_data = _make_github_request("https://api.github.com/user", token)
    username = user_data[0].get("login", "shadowwalkernc") if user_data else "shadowwalkernc"
    
    # 2. Fetch user's owned repositories
    owned_repos = _make_github_request(f"https://api.github.com/users/{username}/repos?per_page=100", token)
    
    # 3. Fetch user's starred repositories
    starred_repos = _make_github_request(f"https://api.github.com/users/{username}/starred?per_page=100", token)

    vault_data = {
        "last_updated": str(Path(__file__).stat().st_mtime),
        "username": username,
        "owned_count": len(owned_repos),
        "starred_count": len(starred_repos),
        "owned_repositories": [
            {
                "name": r.get("name"),
                "full_name": r.get("full_name"),
                "description": r.get("description"),
                "html_url": r.get("html_url"),
                "language": r.get("language"),
                "stargazers_count": r.get("stargazers_count")
            } for r in owned_repos
        ],
        "starred_repositories": [
            {
                "name": r.get("name"),
                "full_name": r.get("full_name"),
                "description": r.get("description"),
                "html_url": r.get("html_url"),
                "language": r.get("language"),
                "stargazers_count": r.get("stargazers_count")
            } for r in starred_repos
        ]
    }
    
    VAULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    VAULT_FILE.write_text(json.dumps(vault_data, indent=2), encoding="utf-8")
    
    return {
        "ok": True,
        "username": username,
        "owned_count": len(owned_repos),
        "starred_count": len(starred_repos),
        "vault_path": str(VAULT_FILE.resolve())
    }

def get_vault_summary() -> Dict[str, Any]:
    """Retrieve summary of local GitHub vault."""
    if not VAULT_FILE.exists():
        return {"harvested": False, "owned_count": 0, "starred_count": 0}
    try:
        data = json.loads(VAULT_FILE.read_text(encoding="utf-8"))
        return {
            "harvested": True,
            "username": data.get("username"),
            "owned_count": data.get("owned_count", 0),
            "starred_count": data.get("starred_count", 0),
            "owned_repositories": data.get("owned_repositories", []),
            "starred_repositories": data.get("starred_repositories", [])
        }
    except Exception as e:
        return {"harvested": False, "error": str(e)}
