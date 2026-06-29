"""Agent Routes — Trainable agent entry point (C21).

Endpoints:
  POST /api/agent/chat          — main chat turn (skill-aware, compaction-guarded)
  POST /api/agent/train/start   — begin trace capture (Teach Mode)
  POST /api/agent/train/capture — record one turn into the trace buffer
  POST /api/agent/train/stop    — stop capture, return trace summary
  POST /api/agent/train/crystallize — export trace as skill_creator payload
  GET  /api/agent/status        — harness + training interface status
  GET  /api/agent/skills        — compact skill index for this user

Auth: every endpoint requires a valid session (current_user via Flask-Login
or session cookie); the owner is derived from current_user.username.

Design notes:
  - AgentHarness and TrainingInterface are stored per-session in
    `g._agent_harness` / `g._training_interface` so they're constructed
    once per request and GC'd afterward.  Persistent session state
    (turn count, active skill name) is carried in the Flask session dict.
  - The actual LLM call is delegated to the existing `chat_helpers.run_chat`
    helper so model selection, streaming, tool use, and retry logic are
    NOT duplicated here.
  - Skill injection is transparent to the caller: the harness quietly
    prepends the skill block and the caller receives a normal assistant reply.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from flask import Blueprint, g, jsonify, request, session
from flask_login import current_user, login_required

logger = logging.getLogger(__name__)

agent_bp = Blueprint("agent", __name__, url_prefix="/api/agent")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_skills_manager():
    """Return the SkillsManager from the app's memory service."""
    from flask import current_app
    mem = current_app.extensions.get("memory_service") or getattr(current_app, "memory_service", None)
    if mem and hasattr(mem, "skills"):
        return mem.skills
    # Fallback: construct a standalone manager from the data directory
    try:
        from services.memory.skills import SkillsManager
        data_dir = current_app.config.get("DATA_DIR", "data")
        return SkillsManager(data_dir)
    except Exception as e:
        logger.error(f"Cannot obtain SkillsManager: {e}")
        return None


def _get_harness() -> Any:
    """Return or create the AgentHarness for this request."""
    if hasattr(g, "_agent_harness"):
        return g._agent_harness
    sm = _get_skills_manager()
    if sm is None:
        return None
    from core.agent_harness import AgentHarness
    owner = getattr(current_user, "username", None)
    active_toolsets = session.get("active_toolsets") or []
    platform = session.get("platform")
    harness = AgentHarness(sm, owner=owner, active_toolsets=active_toolsets, platform=platform)
    # Resume the session_id from Flask session if available
    sid = session.get("agent_session_id")
    if sid:
        harness.begin_session(sid)
    g._agent_harness = harness
    return harness


def _get_training_interface() -> Any:
    """Return or create the TrainingInterface for this request."""
    if hasattr(g, "_training_interface"):
        return g._training_interface
    harness = _get_harness()
    if harness is None:
        return None
    from core.training_interface import TrainingInterface
    ti = TrainingInterface(harness)
    # Re-arm active state from Flask session
    if session.get("training_active"):
        ti.start(
            session_id=session.get("agent_session_id"),
            goal=session.get("training_goal"),
        )
        # Restore turn counter (trace itself is not persisted across requests;
        # only the counter for UI display purposes)
        ti._turn_counter = int(session.get("training_turns", 0))
    g._training_interface = ti
    return ti


def _owner() -> Optional[str]:
    return getattr(current_user, "username", None)


def _error(msg: str, code: int = 400):
    return jsonify({"error": msg}), code


# ---------------------------------------------------------------------------
# POST /api/agent/chat
# ---------------------------------------------------------------------------

@agent_bp.route("/chat", methods=["POST"])
@login_required
def agent_chat():
    """Main trainable-agent chat endpoint.

    Request JSON:
      messages      list[{role, content}]  required
      model         str                    optional, overrides session default
      skill         str                    optional, force-inject this skill
      auto_skill    bool                   optional (default true), auto-route to skill
      session_id    str                    optional, resume/start a named session
      training_mode bool                   optional, capture this turn in trace

    Response JSON:
      reply         str
      session_id    str
      skill_injected str|null
      tokens_used   int
      training      {active, turns_captured}
    """
    body: Dict = request.get_json(force=True, silent=True) or {}
    messages: List[Dict] = body.get("messages") or []
    if not messages:
        return _error("messages is required")

    model: Optional[str] = body.get("model") or session.get("model")
    force_skill: Optional[str] = body.get("skill")
    auto_skill: bool = body.get("auto_skill", True)
    req_session_id: Optional[str] = body.get("session_id")
    training_flag: Optional[bool] = body.get("training_mode")

    harness = _get_harness()
    if harness is None:
        return _error("Agent harness unavailable", 503)

    # Ensure a session is active
    sid = req_session_id or session.get("agent_session_id") or str(uuid.uuid4())
    if sid != harness.session_id:
        harness.begin_session(sid)
    session["agent_session_id"] = sid

    # Optional: toggle training mode via request flag
    if training_flag is not None:
        harness.set_training_mode(bool(training_flag))
        if training_flag:
            session["training_active"] = True
        else:
            session.pop("training_active", None)

    # Build system prompt with compact skill index
    user_task = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    system_prompt = harness.build_system_prompt(
        _base_prompt(),
        task=user_task,
        inject_skill=force_skill,
    )

    # Skill injection
    skill_injected: Optional[str] = None
    if force_skill:
        messages = harness.inject_skill(messages, force_skill)
        skill_injected = force_skill
    elif auto_skill and user_task:
        messages, skill_injected = harness.route_and_inject(messages, user_task)

    # Compaction guard (80% check)
    messages = harness.maybe_compact(messages, model=model)

    # Prepend system message
    full_messages = [{"role": "system", "content": system_prompt}] + [
        m for m in messages if m.get("role") != "system"
    ]

    # Delegate to existing chat helper
    try:
        reply, tokens_used = _run_chat(full_messages, model=model)
    except Exception as e:
        logger.error(f"agent_chat LLM call failed: {e}")
        return _error(f"LLM call failed: {e}", 502)

    harness.record_turn(tokens_used, skill_name=skill_injected, source="agent_chat")

    # Capture into training trace if active
    ti = _get_training_interface()
    if ti and ti.is_active:
        ti.capture_turn(user_task, reply, tool_calls=[])
        session["training_turns"] = ti.turn_count

    return jsonify({
        "reply": reply,
        "session_id": sid,
        "skill_injected": skill_injected,
        "tokens_used": tokens_used,
        "training": {
            "active": bool(ti and ti.is_active),
            "turns_captured": ti.turn_count if ti else 0,
        },
    })


# ---------------------------------------------------------------------------
# Training endpoints
# ---------------------------------------------------------------------------

@agent_bp.route("/train/start", methods=["POST"])
@login_required
def train_start():
    """Activate Teach Mode / trace capture.

    Request JSON:
      goal       str   optional — describe what you're teaching
      session_id str   optional — attach to an existing agent session
    """
    body: Dict = request.get_json(force=True, silent=True) or {}
    goal: Optional[str] = body.get("goal")
    sid: Optional[str] = body.get("session_id") or session.get("agent_session_id") or str(uuid.uuid4())

    harness = _get_harness()
    if harness is None:
        return _error("Agent harness unavailable", 503)
    if harness.session_id != sid:
        harness.begin_session(sid)
    session["agent_session_id"] = sid

    ti = _get_training_interface()
    ti.start(session_id=sid, goal=goal)
    session["training_active"] = True
    session["training_goal"] = goal
    session["training_turns"] = 0

    return jsonify({"status": "training_started", "session_id": sid, "goal": goal})


@agent_bp.route("/train/capture", methods=["POST"])
@login_required
def train_capture():
    """Manually push one turn into the trace buffer.

    Useful when the caller drives the LLM outside /api/agent/chat but
    still wants to build a trace for crystallization.

    Request JSON:
      user        str   required
      assistant   str   required
      tool_calls  list  optional
      annotation  str   optional
    """
    body: Dict = request.get_json(force=True, silent=True) or {}
    user_msg: str = body.get("user") or ""
    assistant_msg: str = body.get("assistant") or ""
    if not user_msg or not assistant_msg:
        return _error("user and assistant are required")

    ti = _get_training_interface()
    if ti is None:
        return _error("Training interface unavailable", 503)
    if not ti.is_active:
        return _error("Training mode is not active; call /train/start first", 409)

    entry = ti.capture_turn(
        user_msg, assistant_msg,
        tool_calls=body.get("tool_calls") or [],
        annotation=body.get("annotation"),
    )
    session["training_turns"] = ti.turn_count
    return jsonify({"status": "captured", "turn": entry.turn if entry else None,
                    "turns_captured": ti.turn_count})


@agent_bp.route("/train/stop", methods=["POST"])
@login_required
def train_stop():
    """Stop trace capture. Returns a summary (does not crystallize)."""
    ti = _get_training_interface()
    if ti is None:
        return _error("Training interface unavailable", 503)

    was_active = ti.is_active
    ti.stop()
    session.pop("training_active", None)
    session.pop("training_goal", None)

    return jsonify({
        "status": "stopped",
        "was_active": was_active,
        "turns_captured": ti.turn_count,
        "session_id": ti._session_id,
    })


@agent_bp.route("/train/crystallize", methods=["POST"])
@login_required
def train_crystallize():
    """Export the current trace as a skill_creator payload.

    Optionally submits the payload to POST /api/skills/generate
    (if `auto_generate=true` is passed and that endpoint exists).

    Request JSON:
      goal            str   optional — override the session goal
      auto_generate   bool  optional (default false) — immediately call skill generator
    """
    body: Dict = request.get_json(force=True, silent=True) or {}
    goal: Optional[str] = body.get("goal")
    auto_generate: bool = bool(body.get("auto_generate", False))

    ti = _get_training_interface()
    if ti is None:
        return _error("Training interface unavailable", 503)
    if ti.turn_count == 0:
        return _error("No turns captured; nothing to crystallize", 422)

    payload = ti.crystallize(goal=goal)

    result = {"status": "crystallized", "payload": payload}

    if auto_generate:
        skill_result = _auto_generate_skill(payload, owner=_owner())
        result["skill_generation"] = skill_result

    return jsonify(result)


# ---------------------------------------------------------------------------
# Status + index
# ---------------------------------------------------------------------------

@agent_bp.route("/status", methods=["GET"])
@login_required
def agent_status():
    """Return harness + training interface status for the current session."""
    harness = _get_harness()
    ti = _get_training_interface()
    return jsonify({
        "harness": harness.status() if harness else None,
        "training": ti.status() if ti else None,
    })


@agent_bp.route("/skills", methods=["GET"])
@login_required
def agent_skills_index():
    """Return the compact skill index for the authenticated user.

    This is what the agent sees in its system prompt — name + description only.
    Full skill content is never returned here.
    """
    harness = _get_harness()
    if harness is None:
        return _error("Agent harness unavailable", 503)
    idx = harness._registry.compact_index(owner=_owner())
    return jsonify({
        "skills": idx,
        "count": len(idx),
        "estimated_tokens": harness._registry.estimated_tokens(owner=_owner()),
    })


# ---------------------------------------------------------------------------
# Internal helpers (not routes)
# ---------------------------------------------------------------------------

def _base_prompt() -> str:
    """Return the agent's base system prompt.

    Pulls from app config (AGENT_SYSTEM_PROMPT) if set, otherwise returns
    a minimal sensible default so the route works standalone.
    """
    from flask import current_app
    custom = current_app.config.get("AGENT_SYSTEM_PROMPT")
    if custom:
        return custom
    return (
        "You are ShadowRealm, a capable AI assistant. "
        "Follow instructions precisely. "
        "When a skill is provided, follow it step-by-step. "
        "Be concise and accurate."
    )


def _run_chat(messages: List[Dict], model: Optional[str] = None):
    """Delegate to the existing chat_helpers.run_chat.

    Returns (reply_str, tokens_used_int).
    Falls back to a stub if chat_helpers is not available (test mode).
    """
    try:
        from routes.chat_helpers import run_chat
        result = run_chat(messages, model=model)
        # run_chat may return (str, int) or a dict depending on the version
        if isinstance(result, tuple):
            return result[0], result[1] if len(result) > 1 else 0
        if isinstance(result, dict):
            return result.get("reply", ""), result.get("tokens_used", 0)
        return str(result), 0
    except ImportError:
        # Stub for environments where chat_helpers isn't wired yet
        logger.warning("chat_helpers not available; returning stub reply")
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        return f"[stub] Received: {last_user[:80]}", 0


def _auto_generate_skill(payload: Dict, owner: Optional[str] = None) -> Dict:
    """Call the skill generator with the crystallized trace payload.

    Tries the internal skills_routes generate endpoint first;
    falls back to a direct SkillsManager.add_skill call from the
    trace metadata if the route is not registered.
    """
    try:
        from routes.skills_routes import generate_skill_from_trace
        return generate_skill_from_trace(payload, owner=owner)
    except (ImportError, AttributeError):
        pass
    # Minimal fallback: store the raw trace as a draft skill
    try:
        sm = _get_skills_manager()
        if sm:
            sk = sm.add_skill(
                name=f"trace-{payload.get('session_id', 'unknown')[:8]}",
                description=payload.get("goal") or "Auto-crystallized from trace",
                when_to_use=payload.get("goal") or "",
                procedure=[f"Turn {t['turn']}: {t['assistant'][:120]}" for t in payload.get("turns", [])[:10]],
                source="trace-crystallize",
                owner=owner,
                status="draft",
            )
            return {"status": "draft_saved", "skill_name": sk.get("name")}
    except Exception as e:
        logger.error(f"_auto_generate_skill fallback failed: {e}")
    return {"status": "failed", "error": "No generator available"}
