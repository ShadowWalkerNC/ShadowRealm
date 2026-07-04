"""
C111 — Pantheon Router
Scores and routes tasks to the best-fit agent bot.
"""
from __future__ import annotations
from typing import List, Dict, Any

class PantheonRouter:
    @staticmethod
    def route_task(task: str, agents: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Return best match agent based on tag matching
        q = task.lower()
        for agent in agents:
            if any(tag in q for tag in agent.get("tags", [])):
                return agent
        return agents[0] if agents else {}
