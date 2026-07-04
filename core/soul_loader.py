"""
C109 — Soul Loader
Loads and parses soul.md personas to configure dynamic system prompts.
"""
from __future__ import annotations
import os
from typing import Dict, Any

class SoulLoader:
    @staticmethod
    def load_soul(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {"name": "ShadowRealm Agent", "description": "Default blueprint persona"}
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return {
            "name": file_path.split("/")[-1].replace(".md", ""),
            "raw_content": content
        }
