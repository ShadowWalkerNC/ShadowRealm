"""
C110 — Agent Identity
Attaches target persona and identity metadata to LLM prompt wrappers.
"""
from __future__ import annotations
from typing import Dict, Any

class AgentIdentity:
    def __init__(self, name: str, capabilities: list[str]):
        self.name = name
        self.capabilities = capabilities

    def format_system_prompt(self, base_prompt: str) -> str:
        caps_str = ", ".join(self.capabilities)
        return f"Identity: {self.name}\nCapabilities: {caps_str}\n\n{base_prompt}"
