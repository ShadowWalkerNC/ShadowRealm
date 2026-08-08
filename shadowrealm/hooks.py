"""Thin integration helpers called from Odysseus core via SHADOWREALM hooks.

Keep Odysseus call sites to a few lines; put behavior here.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


def apply_model_routing(
    message: str,
    sess: Any,
    *,
    session_id: str,
    owner: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Run ModelRouter, log the decision, optionally force a local endpoint."""
    try:
        from shadowrealm.model_router import (
            PATH_LOCAL_FIRST,
            PATH_LOCAL_ONLY,
            PATH_LOCAL_PLAN_THEN_CLOUD,
            build_default_router,
        )
        from shadowrealm.routing_log import log_decision
        from core.database import SessionLocal, ModelEndpoint

        router = build_default_router()
        decision = router.route(message or "", session_id=session_id, owner=owner)
        record = log_decision(decision)

        if decision.path in {PATH_LOCAL_ONLY, PATH_LOCAL_FIRST, PATH_LOCAL_PLAN_THEN_CLOUD}:
            db = SessionLocal()
            try:
                endpoints = db.query(ModelEndpoint).filter(ModelEndpoint.is_enabled == True).all()
                local_ep, local_model = router.pick_local_endpoint(
                    endpoints, preferred_model=decision.local_model
                )
            finally:
                db.close()
            if local_ep is not None:
                from src.endpoint_resolver import build_chat_url, build_headers, normalize_base
                from src.teacher_escalation import is_self_hosted

                current_url = getattr(sess, "endpoint_url", "") or ""
                must_force = decision.path == PATH_LOCAL_ONLY or not is_self_hosted(current_url)
                if must_force or not current_url:
                    base = normalize_base(local_ep.base_url or "")
                    sess.endpoint_url = build_chat_url(base)
                    if local_model:
                        sess.model = local_model
                    key = getattr(local_ep, "api_key", None) or ""
                    sess.headers = build_headers(key, base) if key else (sess.headers or {})
                    record["applied_endpoint"] = {
                        "id": local_ep.id,
                        "base_url": local_ep.base_url,
                        "model": local_model,
                    }
                    logger.info(
                        "shadowrealm routing → local endpoint id=%s model=%s path=%s",
                        local_ep.id,
                        local_model,
                        decision.path,
                    )
        try:
            setattr(sess, "_routing_decision_id", decision.decision_id)
            setattr(sess, "_routing_path", decision.path)
        except Exception:
            pass
        return record
    except Exception as e:
        logger.warning("shadowrealm model routing skipped: %s", e)
        return None


def routing_sse_event(decision: Optional[Dict[str, Any]]) -> Optional[str]:
    """Return an SSE line for a routing decision, or None."""
    if not decision:
        return None
    payload = {
        "type": "routing",
        "data": {
            "decision_id": decision.get("decision_id"),
            "path": decision.get("path"),
            "reason": decision.get("reason"),
            "scope": decision.get("scope"),
            "sensitivity": decision.get("sensitivity"),
            "local_model": decision.get("local_model"),
            "cloud_allowed": decision.get("cloud_allowed"),
            "applied_endpoint": decision.get("applied_endpoint"),
        },
    }
    return f"data: {json.dumps(payload)}\n\n"


def chat_routing_summary(decision: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not decision:
        return None
    return {
        "decision_id": decision.get("decision_id"),
        "path": decision.get("path"),
        "reason": decision.get("reason"),
        "scope": decision.get("scope"),
        "sensitivity": decision.get("sensitivity"),
    }


def after_local_reply(
    *,
    task: str,
    local_result: str,
    decision: Optional[Dict[str, Any]],
    auto_escalate: bool = True,
) -> Dict[str, Any]:
    """Assess local output; escalate unresolved to OpenRouter when allowed.

    Always updates the routing log with confidence. Never escalates
    ``local_only`` / sensitive decisions. If OpenRouter is not configured,
    returns a skipped escalate package the UI can show later.
    """
    out: Dict[str, Any] = {
        "assessed": False,
        "confident": None,
        "escalated": False,
        "openrouter_configured": False,
    }
    try:
        from shadowrealm.model_router import (
            PATH_LOCAL_ONLY,
            RoutingDecision,
            build_default_router,
        )
        from shadowrealm.openrouter import escalate_unresolved, openrouter_configured
        from shadowrealm.routing_log import update_decision

        out["openrouter_configured"] = openrouter_configured()
        if not decision:
            return out

        mr = build_default_router()
        assessment = mr.assess_confidence(task or "", local_result or "")
        out["assessed"] = True
        out["confident"] = assessment.confident
        out["assessment"] = assessment.to_dict()

        update_decision(
            decision.get("decision_id") or "",
            {
                "confidence": assessment.score,
                "confidence_notes": assessment.notes,
                "unresolved": assessment.unresolved,
            },
        )

        if assessment.confident:
            out["status"] = "local_complete"
            return out

        if decision.get("path") == PATH_LOCAL_ONLY or decision.get("sensitivity") == "force_local":
            out["status"] = "blocked_sensitive"
            out["reason"] = "Sensitive task — cloud escalation blocked; local gaps logged."
            return out

        rd = RoutingDecision(
            decision_id=decision.get("decision_id") or "",
            task_summary=decision.get("task_summary") or "",
            sensitivity=decision.get("sensitivity") or "ok",
            scope=decision.get("scope") or "contained",
            path=decision.get("path") or "local_first",
            reason=decision.get("reason") or "",
            cloud_allowed=bool(decision.get("cloud_allowed")),
        )
        pkg = mr.package_escalation(
            rd,
            task=task or "",
            local_result=local_result or "",
            assessment=assessment,
        )
        out["escalation"] = pkg.to_dict()
        out["escalation_prompt"] = pkg.to_prompt()

        if not auto_escalate or not out["openrouter_configured"]:
            out["status"] = "awaiting_cloud"
            out["reason"] = (
                "Local result incomplete — unresolved package ready. "
                "Set OPENROUTER_API_KEY to auto-escalate, or POST /api/routing/escalate."
            )
            update_decision(
                rd.decision_id,
                {"path": "escalate_unresolved", "confidence_notes": assessment.notes},
            )
            return out

        result = escalate_unresolved(
            escalation_prompt=pkg.to_prompt(),
            decision_id=rd.decision_id,
        )
        out["openrouter"] = result
        out["escalated"] = bool(result.get("ok"))
        out["status"] = "escalated" if result.get("ok") else "escalate_failed"
        if result.get("ok") and result.get("content"):
            out["cloud_content"] = result["content"]
        return out
    except Exception as e:
        logger.warning("shadowrealm after_local_reply skipped: %s", e)
        out["error"] = str(e)
        return out


def after_local_reply_sse(result: Dict[str, Any]) -> Optional[str]:
    """SSE line for post-reply assessment / escalation."""
    if not result or not result.get("assessed"):
        return None
    payload = {
        "type": "routing_assessment",
        "data": {
            "status": result.get("status"),
            "confident": result.get("confident"),
            "assessment": result.get("assessment"),
            "escalated": result.get("escalated"),
            "openrouter_configured": result.get("openrouter_configured"),
            "reason": result.get("reason"),
            "decision_id": (result.get("escalation") or {}).get("routing_decision_id"),
        },
    }
    return f"data: {json.dumps(payload)}\n\n"


def append_self_test_directive(parts: List[str]) -> None:
    """Append the coding self-test system prompt section (mutates ``parts``)."""
    try:
        from shadowrealm.self_test_gate import SELF_TEST_DIRECTIVE
        parts.append(SELF_TEST_DIRECTIVE)
    except Exception:
        pass


def maybe_self_test_handoff(
    *,
    messages: Sequence[Dict[str, Any]],
    tool_events: Sequence[Dict[str, Any]],
    effectful_used: bool,
    force_answer: bool,
    claimed_done: bool,
    already_ran: bool,
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """Evaluate the coding self-test gate.

    Returns ``(ran, result_dict, sse_line, blocker_system_message)``.
    """
    if already_ran or not effectful_used or force_answer or not claimed_done:
        return already_ran, None, None, None
    try:
        from shadowrealm.self_test_gate import looks_like_coding_task, run_self_tests

        tool_names = [
            str(ev.get("tool") or ev.get("name") or "")
            for ev in (tool_events or [])
            if isinstance(ev, dict)
        ]
        user_task = ""
        for m in reversed(messages or []):
            if isinstance(m, dict) and m.get("role") == "user":
                user_task = str(m.get("content") or "")
                break
        if not looks_like_coding_task(user_task, tools_used=tool_names):
            return True, None, None, None

        workspace = None
        try:
            from src.tool_execution import get_active_workspace
            workspace = get_active_workspace()
        except Exception:
            workspace = None

        result = run_self_tests(workspace or ".")
        sse = f'data: {json.dumps({"type": "self_test", "data": result.to_dict()})}\n\n'
        blocker = result.handoff_blocker()
        system_msg = None
        if blocker:
            system_msg = (
                "Self-testing before hand-off failed or could not run:\n"
                f"{result.summary}\n{result.output[:2000]}\n\n"
                "Fix the issues with tools, or explicitly tell the user "
                "tests could not be verified. Do NOT claim the work is done."
            )
            logger.info("shadowrealm self-test blocked handoff: %s", blocker)
        return True, result.to_dict(), sse, system_msg
    except Exception as e:
        logger.debug("shadowrealm self-test gate skipped: %s", e)
        return True, None, None, None
