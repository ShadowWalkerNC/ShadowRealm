"""
C93 — Workflow Registry
Registers, versions, and manages status transitions of workflow definitions.
"""
from __future__ import annotations
from typing import Dict, Optional
from core.workflow_definition import WorkflowDefinition

class WorkflowRegistry:
    def __init__(self):
        self._workflows: Dict[str, WorkflowDefinition] = {}

    def register(self, wf: WorkflowDefinition) -> None:
        self._workflows[wf.id] = wf

    def get(self, wf_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(wf_id)

    def list_all(self) -> Dict[str, WorkflowDefinition]:
        return self._workflows
