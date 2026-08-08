"""API for ModelRouter decisions, routing logs, and named workflow pipelines."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from shadowrealm.model_router import build_default_router
from shadowrealm.routing_log import get_decision, list_decisions, log_decision, update_decision
from shadowrealm.self_test_gate import looks_like_coding_task, run_self_tests
from shadowrealm.workflow_pipelines import (
    WorkflowPipelineEngine,
    list_pipeline_defs,
    list_runs,
    load_run,
)
from src.auth_helpers import require_user

logger = logging.getLogger(__name__)


class RouteRequest(BaseModel):
    task: str = Field(..., min_length=1, max_length=50000)
    session_id: Optional[str] = None
    local_result: Optional[str] = None
    assess: bool = False


class AssessRequest(BaseModel):
    task: str = Field(..., min_length=1)
    local_result: str = Field(..., min_length=0)
    decision_id: Optional[str] = None
    explicit_score: Optional[float] = None


class SelfTestRequest(BaseModel):
    workspace: str = Field(..., min_length=1)
    touched_files: Optional[list[str]] = None
    task: Optional[str] = None


class PipelineStartRequest(BaseModel):
    pipeline: str
    params: Dict[str, Any] = Field(default_factory=dict)


class PipelineResumeRequest(BaseModel):
    user_input: Dict[str, Any] = Field(default_factory=dict)


class EscalateRequest(BaseModel):
    task: str = Field(..., min_length=1)
    local_result: str = Field(..., min_length=0)
    decision_id: Optional[str] = None
    model: Optional[str] = None
    local_first_pass_plan: str = ""


def setup_routing_routes() -> APIRouter:
    router = APIRouter(prefix="/api/routing", tags=["routing"])
    engine = WorkflowPipelineEngine()

    @router.post("/decide")
    def decide(body: RouteRequest, request: Request):
        """Evaluate local-vs-cloud routing for a task and persist the decision."""
        user = require_user(request)
        mr = build_default_router()
        decision = mr.route(body.task, session_id=body.session_id, owner=user or None)
        record = log_decision(decision)

        response: Dict[str, Any] = {"decision": record}
        if body.assess and body.local_result is not None:
            assessment = mr.assess_confidence(body.task, body.local_result)
            response["assessment"] = assessment.to_dict()
            if not assessment.confident and decision.cloud_allowed:
                pkg = mr.package_escalation(
                    decision,
                    task=body.task,
                    local_result=body.local_result,
                    assessment=assessment,
                )
                response["escalation"] = pkg.to_dict()
                response["escalation_prompt"] = pkg.to_prompt()
                update_decision(
                    decision.decision_id,
                    {
                        "confidence": assessment.score,
                        "confidence_notes": assessment.notes,
                        "path": "escalate_unresolved",
                        "extra_assessment": assessment.to_dict(),
                    },
                )
            else:
                update_decision(
                    decision.decision_id,
                    {
                        "confidence": assessment.score,
                        "confidence_notes": assessment.notes,
                    },
                )
        return response

    @router.post("/assess")
    def assess(body: AssessRequest, request: Request):
        require_user(request)
        mr = build_default_router()
        assessment = mr.assess_confidence(
            body.task, body.local_result, explicit_score=body.explicit_score
        )
        out: Dict[str, Any] = {"assessment": assessment.to_dict()}
        if body.decision_id:
            update_decision(
                body.decision_id,
                {
                    "confidence": assessment.score,
                    "confidence_notes": assessment.notes,
                    "unresolved": assessment.unresolved,
                },
            )
            if not assessment.confident:
                decision_rec = get_decision(body.decision_id)
                if decision_rec:
                    from shadowrealm.model_router import RoutingDecision
                    decision = RoutingDecision(
                        decision_id=decision_rec["decision_id"],
                        task_summary=decision_rec.get("task_summary", ""),
                        sensitivity=decision_rec.get("sensitivity", "ok"),
                        scope=decision_rec.get("scope", "contained"),
                        path=decision_rec.get("path", "local_first"),
                        reason=decision_rec.get("reason", ""),
                        cloud_allowed=bool(decision_rec.get("cloud_allowed")),
                    )
                    pkg = mr.package_escalation(
                        decision,
                        task=body.task,
                        local_result=body.local_result,
                        assessment=assessment,
                    )
                    out["escalation"] = pkg.to_dict()
                    out["escalation_prompt"] = pkg.to_prompt()
        return out

    @router.get("/decisions")
    def decisions(
        request: Request,
        limit: int = 100,
        session_id: Optional[str] = None,
        path: Optional[str] = None,
    ):
        require_user(request)
        return {"items": list_decisions(limit=limit, session_id=session_id, path_filter=path)}

    @router.get("/decisions/{decision_id}")
    def decision_detail(decision_id: str, request: Request):
        require_user(request)
        rec = get_decision(decision_id)
        if not rec:
            raise HTTPException(404, "decision not found")
        return rec

    @router.post("/self-test")
    def self_test(body: SelfTestRequest, request: Request):
        require_user(request)
        if body.task and not looks_like_coding_task(body.task):
            return {
                "skipped": True,
                "reason": "task does not look like a coding change",
            }
        result = run_self_tests(body.workspace, touched_files=body.touched_files)
        return {
            "result": result.to_dict(),
            "handoff_blocker": result.handoff_blocker(),
        }

    # ── Named workflow pipelines ────────────────────────────────────

    @router.get("/pipelines")
    def pipelines(request: Request):
        require_user(request)
        return {"pipelines": list_pipeline_defs()}

    @router.get("/pipelines/runs")
    def pipeline_runs(request: Request, pipeline: Optional[str] = None, limit: int = 50):
        require_user(request)
        return {"items": list_runs(pipeline=pipeline, limit=limit)}

    @router.post("/pipelines/start")
    def pipeline_start(body: PipelineStartRequest, request: Request):
        require_user(request)
        try:
            run = engine.start(body.pipeline, body.params)
        except ValueError as e:
            raise HTTPException(400, str(e))
        return run.to_dict()

    @router.get("/pipelines/runs/{run_id}")
    def pipeline_get(run_id: str, request: Request):
        require_user(request)
        run = load_run(run_id)
        if not run:
            raise HTTPException(404, "run not found")
        return run.to_dict()

    @router.post("/pipelines/runs/{run_id}/resume")
    def pipeline_resume(run_id: str, body: PipelineResumeRequest, request: Request):
        require_user(request)
        try:
            run = engine.resume(run_id, user_input=body.user_input)
        except FileNotFoundError:
            raise HTTPException(404, "run not found")
        return run.to_dict()

    @router.post("/escalate")
    def escalate(body: EscalateRequest, request: Request):
        """Escalate unresolved work to OpenRouter (no-op until key is set).

        Sensitive ``local_only`` decisions refuse cloud escalation even if a
        key exists.
        """
        require_user(request)
        from shadowrealm.model_router import PATH_LOCAL_ONLY, RoutingDecision
        from shadowrealm.openrouter import escalate_unresolved, openrouter_configured

        mr = build_default_router()
        decision_rec = get_decision(body.decision_id) if body.decision_id else None
        if decision_rec and decision_rec.get("path") == PATH_LOCAL_ONLY:
            raise HTTPException(
                403,
                "This task was marked local_only (sensitive). Cloud escalation is blocked.",
            )
        if decision_rec:
            decision = RoutingDecision(
                decision_id=decision_rec["decision_id"],
                task_summary=decision_rec.get("task_summary", ""),
                sensitivity=decision_rec.get("sensitivity", "ok"),
                scope=decision_rec.get("scope", "contained"),
                path=decision_rec.get("path", "local_first"),
                reason=decision_rec.get("reason", ""),
                cloud_allowed=bool(decision_rec.get("cloud_allowed")),
            )
        else:
            decision = mr.route(body.task)
            log_decision(decision)

        assessment = mr.assess_confidence(body.task, body.local_result)
        if assessment.confident:
            return {
                "skipped": True,
                "reason": "local result looks complete — no cloud needed",
                "assessment": assessment.to_dict(),
                "decision_id": decision.decision_id,
                "openrouter_configured": openrouter_configured(),
            }
        pkg = mr.package_escalation(
            decision,
            task=body.task,
            local_result=body.local_result,
            assessment=assessment,
            local_first_pass_plan=body.local_first_pass_plan,
        )
        result = escalate_unresolved(
            escalation_prompt=pkg.to_prompt(),
            model=body.model,
            decision_id=decision.decision_id,
        )
        return {
            "assessment": assessment.to_dict(),
            "escalation": pkg.to_dict(),
            "openrouter": result,
            "openrouter_configured": openrouter_configured(),
            "decision_id": decision.decision_id,
        }

    return router
