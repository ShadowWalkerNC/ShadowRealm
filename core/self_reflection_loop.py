"""
C124 — Self-Reflection Loop
Detects compile/runtime errors and automatically triggers patches.
"""
from __future__ import annotations
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SelfReflectionLoop:
    @staticmethod
    def evaluate_execution(exit_code: int, stderr: str) -> Dict[str, Any]:
        if exit_code != 0:
            logger.warning("Error detected in execution: %s", stderr)
            return {
                "status": "unstable",
                "proposed_fix": "Adjust command options or verify arguments."
            }
        return {"status": "stable"}
