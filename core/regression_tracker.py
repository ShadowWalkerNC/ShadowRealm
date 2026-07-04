"""
C102 — Regression Tracker
Tracks success rates and benchmarks across multiple model versions.
"""
from __future__ import annotations
from typing import Dict, List

class RegressionTracker:
    def __init__(self):
        self._history: Dict[str, List[bool]] = {}

    def log_result(self, task_name: str, passed: bool) -> None:
        if task_name not in self._history:
            self._history[task_name] = []
        self._history[task_name].append(passed)

    def get_success_rate(self, task_name: str) -> float:
        if task_name not in self._history or not self._history[task_name]:
            return 1.0
        results = self._history[task_name]
        return sum(1 for r in results if r) / len(results)
