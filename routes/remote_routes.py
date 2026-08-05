from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Dict, Any
from pathlib import Path
from core.remote_controller import RemoteController

router = APIRouter(prefix="/api/remote", tags=["remote"])
controller = RemoteController()

class CommandRequest(BaseModel):
    command: str

@router.get("/app", response_class=HTMLResponse)
def get_remote_app():
    """Serve native iOS/iPhone web remote controller view."""
    html_path = Path(__file__).parent.parent / "static" / "remote.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Remote app template missing")
    return html_path.read_text(encoding="utf-8")

@router.get("/android", response_class=HTMLResponse)
def get_remote_android_app():
    """Serve native Android Material UI web remote controller view."""
    html_path = Path(__file__).parent.parent / "static" / "remote_android.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Android remote app template missing")
    return html_path.read_text(encoding="utf-8")

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
