"""
routes/healing_routes.py — Self-Healing, Telemetry, and Reflection API Harness (Sprint 8B).
"""
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel

from core.database import get_db_session, SkillTrace

logger = logging.getLogger(__name__)

# In-memory improvement proposals queue (C87)
proposals_queue: Dict[str, Dict[str, Any]] = {}

class ProposalAction(BaseModel):
    patch: Optional[str] = None

def setup_healing_routes() -> APIRouter:
    router = APIRouter(prefix="/api/healing", tags=["self-healing"])

    @router.get("/traces", summary="Get execution trace logs")
    async def get_traces(limit: int = 50):
        try:
            with get_db_session() as db:
                rows = db.query(SkillTrace).order_by(SkillTrace.created_at.desc()).limit(limit).all()
                return {
                    "success": True,
                    "traces": [
                        {
                            "id": r.id,
                            "name": r.name,
                            "agent": r.agent,
                            "tokens": r.tokens,
                            "latency": r.latency.isoformat() if r.latency else None,
                            "duration": r.duration,
                            "error_type": r.error_type,
                            "prompt": r.prompt,
                            "response": r.response,
                            "owner": r.owner,
                            "created_at": r.created_at.isoformat()
                        }
                        for r in rows
                    ]
                }
        except Exception as e:
            logger.error(f"Error fetching traces: {e}")
            raise HTTPException(500, detail=str(e))

    @router.get("/proposals", summary="Get active improvement proposals")
    async def get_proposals():
        return {
            "success": True,
            "proposals": list(proposals_queue.values())
        }

    @router.post("/proposals/{proposal_id}/approve", summary="Approve improvement proposal")
    async def approve_proposal(proposal_id: str, body: ProposalAction):
        if proposal_id not in proposals_queue:
            raise HTTPException(404, "Proposal not found")
        proposal = proposals_queue[proposal_id]
        
        # Apply the proposed patch
        try:
            from services.memory.skills import SkillsManager
            from src.constants import DATA_DIR
            sm = SkillsManager(DATA_DIR)
            
            skill_name = proposal["skill_name"]
            # Save or refine the skill with proposed instructions
            new_content = body.patch or proposal["proposed_content"]
            
            # Simple overwrite/update
            skills = sm.load_all()
            found = False
            for sk in skills:
                if sk.get("name") == skill_name:
                    sk["procedure"] = new_content.split("\n")
                    found = True
                    break
            
            if not found:
                # Create a new draft
                sm.add_skill(
                    name=skill_name,
                    description=proposal.get("description", "Improved skill"),
                    when_to_use=skill_name,
                    procedure=new_content.split("\n"),
                    source="reflection_engine",
                    owner=proposal.get("owner", "admin"),
                    status="published"
                )
            else:
                sm.save(skills)
                
            proposal["status"] = "approved"
            return {"success": True, "message": f"Successfully updated skill {skill_name}"}
        except Exception as e:
            logger.error(f"Failed to approve proposal: {e}")
            raise HTTPException(500, detail=str(e))

    @router.post("/proposals/{proposal_id}/reject", summary="Reject/rollback proposal")
    async def reject_proposal(proposal_id: str):
        if proposal_id not in proposals_queue:
            raise HTTPException(404, "Proposal not found")
        proposals_queue[proposal_id]["status"] = "rejected"
        return {"success": True, "message": "Proposal rejected"}

    return router

def log_skill_trace(name: str, agent: str, prompt: str, response: str, tokens: int, duration: float, error_type: Optional[str] = None, owner: Optional[str] = None):
    """Helper to log execution trace into skill_traces table."""
    try:
        with get_db_session() as db:
            trace = SkillTrace(
                id=str(uuid.uuid4()),
                name=name,
                agent=agent,
                tokens=tokens,
                duration=duration,
                error_type=error_type,
                prompt=prompt,
                response=response,
                owner=owner or "admin"
            )
            db.add(trace)
            db.commit()
            
            # If the trace failed, generate a self-healing proposal (C86)
            if error_type:
                proposal_id = str(uuid.uuid4())
                proposals_queue[proposal_id] = {
                    "id": proposal_id,
                    "skill_name": name,
                    "error_type": error_type,
                    "description": f"Auto-heal recommendation for skill '{name}' following execution failure.",
                    "proposed_content": f"# Instructions\n1. Check input bounds\n2. Recover from {error_type} error\n3. Retry operation",
                    "status": "pending",
                    "owner": owner or "admin",
                    "created_at": datetime.utcnow().isoformat()
                }
    except Exception as e:
        logger.error(f"Failed to log skill trace: {e}")
