import socket
import subprocess
import urllib.parse
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel
from typing import Dict, Any
from pathlib import Path
from core.remote_controller import RemoteController

router = APIRouter(prefix="/api/remote", tags=["remote"])
controller = RemoteController()

class CommandRequest(BaseModel):
    command: str

def _get_tailscale_ip() -> str:
    """Retrieve local Tailscale IP address if running."""
    try:
        res = subprocess.run("tailscale ip -4", shell=True, capture_output=True, text=True, timeout=3)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    # Fallback to local network IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@router.get("/pairing")
def get_pairing_info():
    """Return Tailscale IP and mobile pairing URLs."""
    ip = _get_tailscale_ip()
    iphone_url = f"http://{ip}:5000/api/remote/app"
    android_url = f"http://{ip}:5000/api/remote/android"
    return {
        "tailscale_ip": ip,
        "iphone_url": iphone_url,
        "android_url": android_url,
        "qr_iphone_api": f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={urllib.parse.quote(iphone_url)}",
        "qr_android_api": f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={urllib.parse.quote(android_url)}",
    }

@router.get("/pair", response_class=HTMLResponse)
def get_pairing_page():
    """Serve QR code mobile pairing page."""
    html_path = Path(__file__).parent.parent / "static" / "pairing.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Pairing template missing")
    return html_path.read_text(encoding="utf-8")

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
