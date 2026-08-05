"""Remote routes — endpoints for iPhone/Mobile remote control wrapper."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
from core.remote_controller import RemoteController

router = APIRouter(prefix="/api/remote", tags=["remote"])
controller = RemoteController()

class CommandRequest(BaseModel):
    command: str

@router.get("/status")
def get_remote_status():
    """Get system health and state for mobile app."""
    return controller.get_system_status()

@router.post("/execute")
def execute_remote_command(req: CommandRequest):
    """Execute command on host PC remotely."""
    if not req.command or not req.command.strip():
        raise HTTPException(status_code=400, detail="Command cannot be empty")
    return controller.execute_pc_command(req.command)
