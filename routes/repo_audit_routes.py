"""
REST API routes for Custom Bots and 4-Stage Repo Audit Pipeline (/api/audit & /api/bots).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from core.repo_audit_engine import RepoAuditEngine
from core.custom_bot_manager import CustomBotManager

router = APIRouter(tags=["audit_bots"])
bot_manager = CustomBotManager()

class RunAuditRequest(BaseModel):
    repo_path: Optional[str] = None

@router.get("/api/bots")
async def list_custom_bots():
    """List all registered Buzz-style custom agent bots."""
    return {"bots": bot_manager.list_bots()}

@router.post("/api/audit/run")
async def run_repo_audit(body: RunAuditRequest):
    """Execute 4-stage audit pipeline on target repo path."""
    engine = RepoAuditEngine(body.repo_path)
    report = engine.run_full_audit()
    return report

@router.post("/api/evolution/cycle")
async def trigger_evolution_cycle():
    """Trigger an on-demand continuous self-learning & audit evolution cycle."""
    from core.continuous_evolution import ContinuousEvolutionEngine
    evolution = ContinuousEvolutionEngine()
    result = await evolution.run_evolution_cycle()
    return result
