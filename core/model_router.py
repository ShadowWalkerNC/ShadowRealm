"""
C118 — Model Router
Routes prompts dynamically to hosted providers or local Ollama fallbacks.
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

class ModelRouter:
    def __init__(self, offline: bool = False):
        self.offline = offline

    def route_query(self, query: str) -> str:
        if self.offline:
            logger.info("Routing query to local offline Ollama provider")
            return "ollama"
        logger.info("Routing query to default API host")
        return "openai"
