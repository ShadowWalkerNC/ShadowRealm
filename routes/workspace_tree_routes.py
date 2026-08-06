"""
REST API routes for File-Tree Workflows (/api/workflows).
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from core.workflow_tree_engine import WorkflowTreeEngine

router = APIRouter(prefix="/api/workflows", tags=["workflows"])
engine = WorkflowTreeEngine()

class CreateTaskRequest(BaseModel):
    workflow_name: str
    task_name: str

@router.get("")
async def list_workflows():
    """List all workflows and task folder trees."""
    return {"workflows": engine.scan_workflows()}

@router.post("/task")
async def create_task(body: CreateTaskRequest):
    """Create a new task folder node with prompts/, tools/, data/, subagents/."""
    node = engine.create_task_node(body.workflow_name, body.task_name)
    return {"ok": True, "task": node}
