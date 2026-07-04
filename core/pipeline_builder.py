"""
C94 — Pipeline Builder
Creates composable ETL steps for processing datasets in sequence.
"""
from __future__ import annotations
from typing import Callable, Any, List

class PipelineBuilder:
    def __init__(self):
        self.steps: List[Callable[[Any], Any]] = []

    def add_step(self, step: Callable[[Any], Any]) -> PipelineBuilder:
        self.steps.append(step)
        return self

    def execute(self, initial_data: Any) -> Any:
        current = initial_data
        for step in self.steps:
            current = step(current)
        return current
