"""
C116 — Goal Budget
Restricts dynamic loops and limits tokens consumed in multi-agent sessions.
"""
from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

class GoalBudget:
    def __init__(self, max_turns: int = 10, mode: str = "balanced"):
        self.max_turns = max_turns
        self.mode = mode
        self.current_turns = 0

    def consume_turn(self) -> bool:
        if self.current_turns >= self.max_turns:
            logger.warning("Goal budget exceeded for mode: %s", self.mode)
            return False
        self.current_turns += 1
        return True
