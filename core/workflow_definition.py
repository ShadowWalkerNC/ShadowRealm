"""
C91 — Workflow Definition
Defines trigger nodes, condition gates, and action steps definition.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class WorkflowNode:
    id: str
    type: str  # 'trigger' | 'condition' | 'action'
    config: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowEdge:
    from_node: str
    to_node: str
    condition_value: Optional[Any] = None

@dataclass
class WorkflowDefinition:
    id: str
    name: str
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
