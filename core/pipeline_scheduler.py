"""
C96 — Pipeline Scheduler
Schedules, tracks, and executes data processing pipelines based on cron schedules.
"""
from __future__ import annotations
import logging
from typing import Dict, Any
from core.pipeline_builder import PipelineBuilder

logger = logging.getLogger(__name__)

class PipelineScheduler:
    def __init__(self):
        self._schedules: Dict[str, str] = {}
        self._pipelines: Dict[str, PipelineBuilder] = {}

    def schedule(self, name: str, cron_expr: str, pipeline: PipelineBuilder) -> None:
        self._schedules[name] = cron_expr
        self._pipelines[name] = pipeline
        logger.info("Scheduled pipeline '%s' with cron '%s'", name, cron_expr)

    def trigger(self, name: str, input_data: Any) -> Any:
        if name not in self._pipelines:
            raise KeyError(f"Pipeline '{name}' not found")
        logger.info("Triggering pipeline '%s'", name)
        return self._pipelines[name].execute(input_data)
