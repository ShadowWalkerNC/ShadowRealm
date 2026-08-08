"""OpenRouter escalation adapter — dormant until OPENROUTER_API_KEY is set.

When you add an OpenRouter key later, ``escalate_unresolved`` sends only the
unresolved package (not the whole original task) to a cloud model and logs
token/cost estimates onto the routing decision.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = os.getenv(
    "SHADOWREALM_OPENROUTER_MODEL", "anthropic/claude-sonnet-4"
)
# Rough blended estimate; refine per-model once you settle on a default.
_USD_PER_1K = float(os.getenv("SHADOWREALM_OPENROUTER_USD_PER_1K", "0.003"))


def openrouter_configured() -> bool:
    return bool((os.getenv("OPENROUTER_API_KEY") or "").strip())


def escalate_unresolved(
    *,
    escalation_prompt: str,
    model: Optional[str] = None,
    decision_id: Optional[str] = None,
    timeout: float = 120.0,
) -> Dict[str, Any]:
    """Call OpenRouter with an unresolved-only package.

    If no key is configured, returns ``{"ok": False, "skipped": True}``
    without making a network call — safe for local-only operation.
    """
    api_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if not api_key:
        return {
            "ok": False,
            "skipped": True,
            "reason": "OPENROUTER_API_KEY not set — local-only mode",
            "decision_id": decision_id,
        }

    model = model or DEFAULT_OPENROUTER_MODEL
    base = (os.getenv("OPENROUTER_BASE_URL") or DEFAULT_OPENROUTER_BASE).rstrip("/")
    url = f"{base}/chat/completions"

    try:
        import httpx
        from shadowrealm.routing_log import update_decision

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ShadowWalkerNC/ShadowRealm",
            "X-OpenRouter-Title": "ShadowRealm",
        }
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are the cloud escalation model for ShadowRealm. "
                        "Complete ONLY the unresolved portions. Do not redo finished work."
                    ),
                },
                {"role": "user", "content": escalation_prompt},
            ],
            "temperature": 0.2,
        }
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        choice = (data.get("choices") or [{}])[0]
        content = ((choice.get("message") or {}).get("content")) or ""
        usage = data.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total = prompt_tokens + completion_tokens

        if decision_id:
            update_decision(
                decision_id,
                {
                    "path": "escalate_unresolved",
                    "estimated_tokens": total,
                    "estimated_cost_usd": round((total / 1000.0) * _USD_PER_1K, 6),
                    "cloud_model": model,
                    "extra": {"openrouter_usage": usage},
                },
            )

        return {
            "ok": True,
            "skipped": False,
            "model": model,
            "content": content,
            "usage": usage,
            "decision_id": decision_id,
            "estimated_tokens": total,
            "estimated_cost_usd": round((total / 1000.0) * _USD_PER_1K, 6),
        }
    except Exception as e:
        logger.warning("OpenRouter escalation failed: %s", e)
        return {
            "ok": False,
            "skipped": False,
            "error": str(e),
            "decision_id": decision_id,
        }
