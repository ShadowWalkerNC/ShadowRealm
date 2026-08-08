"""
ShadowRealm ModelRouter (C118-aligned)
======================================
Local-first task routing with logged reasoning.

Fork note: lives under ``shadowrealm/`` so Odysseus upstream syncs do not
collide with a future upstream ``core/model_router.py``.

Decision order (fixed):
  1. Sensitivity check — proprietary/sensitive → force local, never cloud
  2. Scope check — small/contained → local first; large/architectural →
     flag cloud but still produce a local first-pass plan
  3. Local attempt — anything not cloud-only tries Qwen/local first
  4. Self-assessed confidence — complete → done; gaps → escalate only
     the unresolved portion (OpenRouter/cloud when configured)
  5. Logging — every decision is persisted for review

This module is deterministic for steps 1–2 (keyword/heuristic). Steps 3–4
are orchestrated by callers (chat/agent loop) using the RoutingDecision
returned here; ``assess_confidence`` provides a cheap local second-pass
heuristic, and ``package_escalation`` builds the cloud payload.
"""
from __future__ import annotations

import logging
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# ── Classification enums ────────────────────────────────────────────

SENSITIVITY_FORCE_LOCAL = "force_local"
SENSITIVITY_OK = "ok"

SCOPE_SMALL = "small"          # (a) single-file / small multi-file
SCOPE_CONTAINED = "contained"  # (b) bug fix, small refactor, review, explain
SCOPE_LARGE = "large"          # (c) architectural / cross-codebase / long-context

PATH_LOCAL_ONLY = "local_only"
PATH_LOCAL_FIRST = "local_first"
PATH_LOCAL_PLAN_THEN_CLOUD = "local_plan_then_cloud"
PATH_ESCALATE_UNRESOLVED = "escalate_unresolved"
PATH_CLOUD = "cloud"


_SENSITIVE_PATTERNS = [
    re.compile(p, re.I)
    for p in (
        r"\b(proprietary|confidential|trade[- ]secret)\b",
        r"\b(api[_ ]?key|secret[_ ]?key|private[_ ]?key|password|passwd|credential)\b",
        r"\b(\.env|vault|secrets?\.ya?ml|id_rsa|kubeconfig)\b",
        r"\b(pii|ssn|social security|credit card|hipaa|gdpr)\b",
        r"\b(internal only|do not (share|upload|send) (to )?cloud)\b",
        r"\b(company[- ]private|customer data|production (db|database|secrets))\b",
    )
]

_LARGE_SCOPE_PATTERNS = [
    re.compile(p, re.I)
    for p in (
        r"\b(architect(ure|ural)|cross[- ]codebase|entire (codebase|repo|project))\b",
        r"\b(redesign|migrate (the )?whole|multi[- ]service|system design)\b",
        r"\b(long[- ]context|hundreds of files|monorepo[- ]wide)\b",
        r"\b(end[- ]to[- ]end (feature|system)|greenfield|from scratch)\b",
        r"\b(refactor (the )?entire|rewrite (the )?(app|system|platform))\b",
    )
]

_CONTAINED_PATTERNS = [
    re.compile(p, re.I)
    for p in (
        r"\b(bug|fix|patch|hotfix|regression)\b",
        r"\b(refactor|cleanup|rename|explain|review|lint)\b",
        r"\b(unit test|add test|typo|docstring|comment)\b",
        r"\b(single file|one file|this file|this function|this class)\b",
    )
]

_LOW_CONFIDENCE_PATTERNS = [
    re.compile(p, re.I)
    for p in (
        r"\b(i'?m not sure|not certain|unable to|could not|couldn't)\b",
        r"\b(unresolved|incomplete|partial(ly)?|needs? (more|further))\b",
        r"\b(TODO|FIXME|XXX)\b",
        r"\b(escalate|beyond my|too complex|insufficient context)\b",
        r"\b(please (provide|clarify)|i need more)\b",
        r"\b(contradict|conflict|ambiguous)\b",
    )
]


@dataclass
class RoutingDecision:
    """Immutable record of one routing evaluation."""

    decision_id: str
    task_summary: str
    sensitivity: str
    scope: str
    path: str
    reason: str
    local_model: str = "qwen3:8b"
    cloud_allowed: bool = False
    require_local_first_pass: bool = True
    escalate_unresolved_only: bool = True
    confidence: Optional[float] = None
    confidence_notes: str = ""
    estimated_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    local_endpoint_id: Optional[str] = None
    cloud_endpoint_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ConfidenceAssessment:
    confident: bool
    score: float  # 0.0–1.0
    unresolved: List[str]
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EscalationPackage:
    """Payload for cloud escalation — only unresolved work, plus local context."""

    original_task: str
    local_result: str
    unresolved: List[str]
    local_first_pass_plan: str
    reason: str
    routing_decision_id: str

    def to_prompt(self) -> str:
        unresolved_block = "\n".join(f"- {u}" for u in self.unresolved) or "- (unspecified gaps)"
        return (
            "You are receiving an escalated task. A local model already attempted it.\n"
            "Complete ONLY the unresolved portions. Do not redo finished work.\n\n"
            f"## Original task\n{self.original_task}\n\n"
            f"## Local first-pass / plan\n{self.local_first_pass_plan or '(none)'}\n\n"
            f"## Local result so far\n{self.local_result or '(empty)'}\n\n"
            f"## Unresolved (fix these)\n{unresolved_block}\n\n"
            f"## Why escalated\n{self.reason}\n"
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ModelRouter:
    """Cost-aware local-first router with Ollama fallback preference."""

    def __init__(
        self,
        *,
        local_model: str = "qwen3:8b",
        cloud_available: bool = False,
        openrouter_configured: bool = False,
    ):
        self.local_model = local_model
        self.cloud_available = bool(cloud_available or openrouter_configured)
        self.openrouter_configured = openrouter_configured

    # ── Public API ──────────────────────────────────────────────────

    def route(
        self,
        task: str,
        *,
        session_id: Optional[str] = None,
        owner: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        task = (task or "").strip()
        summary = _summarize_task(task)
        sensitivity = self.check_sensitivity(task)
        scope = self.check_scope(task)

        if sensitivity == SENSITIVITY_FORCE_LOCAL:
            path = PATH_LOCAL_ONLY
            reason = (
                "Sensitivity check: task touches proprietary/sensitive material — "
                "forcing local model; cloud blocked regardless of complexity."
            )
            cloud_allowed = False
            require_plan = False
        elif scope == SCOPE_LARGE:
            path = PATH_LOCAL_PLAN_THEN_CLOUD
            reason = (
                "Scope check: large/architectural task — flag for cloud, but "
                "local model must produce a first-pass analysis/plan first."
            )
            cloud_allowed = self.cloud_available
            require_plan = True
        else:
            path = PATH_LOCAL_FIRST
            reason = (
                f"Scope check: {scope} task — attempt fully on local "
                f"({self.local_model}) first; escalate only unresolved gaps."
            )
            cloud_allowed = self.cloud_available
            require_plan = False

        decision = RoutingDecision(
            decision_id=uuid.uuid4().hex[:12],
            task_summary=summary,
            sensitivity=sensitivity,
            scope=scope,
            path=path,
            reason=reason,
            local_model=self.local_model,
            cloud_allowed=cloud_allowed,
            require_local_first_pass=True,
            escalate_unresolved_only=True,
            metadata={
                **(metadata or {}),
                "session_id": session_id,
                "owner": owner,
                "cloud_available": self.cloud_available,
                "openrouter_configured": self.openrouter_configured,
                "require_local_plan": require_plan,
            },
        )
        logger.info(
            "routing decision id=%s path=%s scope=%s sensitivity=%s summary=%r",
            decision.decision_id,
            decision.path,
            decision.scope,
            decision.sensitivity,
            decision.task_summary,
        )
        return decision

    def check_sensitivity(self, task: str) -> str:
        text = task or ""
        for pat in _SENSITIVE_PATTERNS:
            if pat.search(text):
                return SENSITIVITY_FORCE_LOCAL
        return SENSITIVITY_OK

    def check_scope(self, task: str) -> str:
        text = task or ""
        for pat in _LARGE_SCOPE_PATTERNS:
            if pat.search(text):
                return SCOPE_LARGE
        for pat in _CONTAINED_PATTERNS:
            if pat.search(text):
                return SCOPE_CONTAINED
        # Heuristic: short prompts → small; long multi-file language → large-ish
        if len(text) < 280 and text.count("\n") < 8:
            return SCOPE_SMALL
        if re.search(r"\b(files?|modules?|packages?|services?)\b", text, re.I) and len(text) > 600:
            return SCOPE_LARGE
        return SCOPE_CONTAINED

    def assess_confidence(
        self,
        task: str,
        local_result: str,
        *,
        explicit_score: Optional[float] = None,
    ) -> ConfidenceAssessment:
        """Heuristic self-assessment of a local-model result.

        Callers may pass an LLM-produced ``explicit_score`` (0–1). Otherwise
        we score from length, give-up phrases, and unresolved markers.
        """
        result = (local_result or "").strip()
        unresolved: List[str] = []
        notes_parts: List[str] = []

        if not result:
            return ConfidenceAssessment(
                confident=False,
                score=0.0,
                unresolved=["empty local result"],
                notes="Local model produced no output.",
            )

        hit_patterns = []
        for pat in _LOW_CONFIDENCE_PATTERNS:
            if pat.search(result):
                hit_patterns.append(pat.pattern)
                unresolved.append(f"matched low-confidence pattern: {pat.pattern}")

        score = 0.85
        if explicit_score is not None:
            try:
                score = max(0.0, min(1.0, float(explicit_score)))
                notes_parts.append(f"explicit_score={score:.2f}")
            except (TypeError, ValueError):
                pass
        else:
            if hit_patterns:
                score -= 0.15 * min(3, len(hit_patterns))
                notes_parts.append(f"low-confidence phrases: {len(hit_patterns)}")
            if len(result) < 40:
                score -= 0.25
                unresolved.append("result unusually short")
            # Structured self-eval block the local model may emit
            m = re.search(
                r"confidence\s*[:=]\s*([0-9]*\.?[0-9]+)",
                result,
                re.I,
            )
            if m:
                try:
                    score = max(0.0, min(1.0, float(m.group(1))))
                    if score > 1.0:
                        score = score / 100.0
                    notes_parts.append(f"parsed confidence={score:.2f}")
                except ValueError:
                    pass
            um = re.search(
                r"unresolved\s*:\s*(.+?)(?:\n\n|\Z)",
                result,
                re.I | re.S,
            )
            if um:
                for line in um.group(1).splitlines():
                    line = line.strip().lstrip("-*• ").strip()
                    if line:
                        unresolved.append(line)

        score = max(0.0, min(1.0, score))
        confident = score >= 0.7 and not hit_patterns
        if not notes_parts:
            notes_parts.append("heuristic assessment")
        return ConfidenceAssessment(
            confident=confident,
            score=score,
            unresolved=unresolved,
            notes="; ".join(notes_parts),
        )

    def package_escalation(
        self,
        decision: RoutingDecision,
        *,
        task: str,
        local_result: str,
        assessment: ConfidenceAssessment,
        local_first_pass_plan: str = "",
    ) -> EscalationPackage:
        return EscalationPackage(
            original_task=task,
            local_result=local_result,
            unresolved=list(assessment.unresolved) or ["low confidence / incomplete"],
            local_first_pass_plan=local_first_pass_plan or _extract_plan(local_result),
            reason=assessment.notes or decision.reason,
            routing_decision_id=decision.decision_id,
        )

    def estimate_cloud_impact(
        self,
        decision: RoutingDecision,
        *,
        prompt_tokens: int,
        completion_tokens: int = 0,
        usd_per_1k: float = 0.002,
    ) -> RoutingDecision:
        """Attach rough token/cost estimates (used once cloud is connected)."""
        total = max(0, int(prompt_tokens)) + max(0, int(completion_tokens))
        decision.estimated_tokens = total
        decision.estimated_cost_usd = round((total / 1000.0) * usd_per_1k, 6)
        return decision

    # ── Endpoint helpers ────────────────────────────────────────────

    def pick_local_endpoint(
        self,
        endpoints: Sequence[Any],
        *,
        preferred_model: Optional[str] = None,
    ) -> Tuple[Optional[Any], Optional[str]]:
        """Prefer Ollama/local hosts; return (endpoint_row, model_id)."""
        preferred = (preferred_model or self.local_model).lower()
        local_eps = []
        for ep in endpoints or []:
            base = getattr(ep, "base_url", "") or ""
            if _is_local_base(base):
                local_eps.append(ep)
        if not local_eps:
            return None, None
        # Prefer one that lists the preferred model
        for ep in local_eps:
            models = _cached_models(ep)
            for m in models:
                if preferred in str(m).lower() or str(m).lower() in preferred:
                    return ep, m
        ep = local_eps[0]
        models = _cached_models(ep)
        return ep, (models[0] if models else preferred_model or self.local_model)

    def pick_cloud_endpoint(
        self,
        endpoints: Sequence[Any],
    ) -> Tuple[Optional[Any], Optional[str]]:
        for ep in endpoints or []:
            base = (getattr(ep, "base_url", "") or "").lower()
            if "openrouter.ai" in base or _is_cloud_base(base):
                models = _cached_models(ep)
                return ep, (models[0] if models else None)
        return None, None


def _summarize_task(task: str, limit: int = 160) -> str:
    one_line = " ".join((task or "").split())
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 1] + "…"


def _extract_plan(text: str) -> str:
    if not text:
        return ""
    m = re.search(r"(?is)(?:plan|analysis)\s*:\s*(.+?)(?:\n\n|\Z)", text)
    if m:
        return m.group(1).strip()[:4000]
    # First ~800 chars as a weak stand-in
    return text.strip()[:800]


def _cached_models(ep: Any) -> List[str]:
    import json
    raw = getattr(ep, "cached_models", None) or getattr(ep, "models", None)
    if not raw:
        return []
    try:
        models = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return []
    return [str(m) for m in models] if isinstance(models, list) else []


def _is_local_base(base: str) -> bool:
    try:
        host = (urlparse(base).hostname or "").lower()
    except Exception:
        return False
    if host in {"localhost", "127.0.0.1", "::1", "host.docker.internal", "0.0.0.0"}:
        return True
    if host.startswith("192.168.") or host.startswith("10.") or host.endswith(".local"):
        return True
    if "ollama" in (base or "").lower():
        return True
    return False


def _is_cloud_base(base: str) -> bool:
    cloud_hosts = (
        "openrouter.ai", "api.openai.com", "api.anthropic.com",
        "generativelanguage.googleapis.com", "api.groq.com",
        "api.together.xyz", "api.fireworks.ai", "api.deepseek.com",
        "api.mistral.ai", "api.x.ai",
    )
    try:
        host = (urlparse(base).hostname or "").lower()
    except Exception:
        return False
    return any(h == host or host.endswith("." + h) for h in cloud_hosts)


def cloud_is_configured() -> bool:
    """True if OpenRouter or another cloud key is present in the environment."""
    import os
    keys = (
        "OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
        "GROQ_API_KEY", "GEMINI_API_KEY", "DEEPSEEK_API_KEY", "XAI_API_KEY",
    )
    return any((os.getenv(k) or "").strip() for k in keys)


def build_default_router() -> ModelRouter:
    configured = cloud_is_configured()
    openrouter = bool((__import__("os").getenv("OPENROUTER_API_KEY") or "").strip())
    return ModelRouter(
        local_model="qwen3:8b",
        cloud_available=configured,
        openrouter_configured=openrouter,
    )
