"""
Muse Code (Meta AI) LLM Provider for ShadowRealm.
Provides streaming and non-streaming chat completions via the Meta AI API
using the muse-spark-1.2 model (and any future muse-* models).

API Reference:
  POST https://api.meta.ai/v1/responses
  Authorization: Bearer <MUSE_API_KEY>
  Content-Type: application/json

Response format follows the OpenAI Responses API shape.
"""

import json
import logging
import os
import urllib.error
import urllib.request
from typing import AsyncIterator, Dict, Any, List, Optional

logger = logging.getLogger(__name__)

MUSE_API_BASE = os.environ.get("MUSE_API_BASE", "https://api.meta.ai/v1")
MUSE_MODEL_DEFAULT = os.environ.get("MUSE_MODEL", "muse-spark-1.2")


def _get_api_key() -> str:
    """Retrieve the Muse Code API key from environment."""
    key = os.environ.get("MUSE_API_KEY", "")
    if not key:
        raise ValueError(
            "MUSE_API_KEY not set. Add it to your .env file as:\n"
            "  MUSE_API_KEY=LLM_1657887906341824_CbLAL_..."
        )
    return key


def _build_payload(
    messages: List[Dict[str, Any]],
    model: str = MUSE_MODEL_DEFAULT,
    stream: bool = False,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """Build the Muse API request payload from a list of chat messages."""
    # Convert standard chat messages → Muse input format
    muse_input = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, str):
            muse_input.append({
                "role": role,
                "content": [{"type": "input_text", "text": content}]
            })
        elif isinstance(content, list):
            muse_input.append({"role": role, "content": content})

    return {
        "model": model,
        "input": muse_input,
        "stream": stream,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }


def muse_chat(
    messages: List[Dict[str, Any]],
    model: str = MUSE_MODEL_DEFAULT,
    stream: bool = False,
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """Send a synchronous chat request to the Muse Code API.

    Args:
        messages:    List of {"role": "user"|"assistant"|"system", "content": str}
        model:       Muse model ID (default: muse-spark-1.2)
        stream:      Enable streaming (default: False)
        max_tokens:  Maximum tokens in response
        temperature: Sampling temperature

    Returns:
        dict with keys: ok, content (str), model, usage
    """
    url = f"{MUSE_API_BASE}/responses"
    payload = _build_payload(messages, model, stream, max_tokens, temperature)

    try:
        api_key = _get_api_key()
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "ShadowRealm-MuseCode/1.0")

        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)

        # Extract text from Muse response format
        content = ""
        output = data.get("output", [])
        if isinstance(output, list):
            for block in output:
                for part in block.get("content", []):
                    if part.get("type") == "output_text":
                        content += part.get("text", "")
        elif isinstance(output, str):
            content = output

        return {
            "ok": True,
            "model": data.get("model", model),
            "content": content,
            "usage": data.get("usage", {}),
            "raw": data,
        }

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        logger.error("Muse API HTTP error %s: %s", e.code, body)
        return {"ok": False, "error": f"HTTP {e.code}: {body}"}
    except Exception as e:
        logger.error("Muse API error: %s", e)
        return {"ok": False, "error": str(e)}


def muse_quick(prompt: str, model: str = MUSE_MODEL_DEFAULT) -> str:
    """Convenience wrapper — send a single user prompt, return text reply."""
    res = muse_chat([{"role": "user", "content": prompt}], model=model)
    if res["ok"]:
        return res["content"]
    return f"[Muse Error] {res.get('error', 'Unknown error')}"


def muse_model_info() -> Dict[str, Any]:
    """Return metadata about the configured Muse Code provider."""
    try:
        key = _get_api_key()
        key_preview = f"{key[:12]}...{key[-6:]}" if len(key) > 18 else "***"
    except ValueError:
        key_preview = "NOT SET"

    return {
        "provider": "Muse Code (Meta AI)",
        "model": MUSE_MODEL_DEFAULT,
        "api_base": MUSE_API_BASE,
        "api_key_preview": key_preview,
        "capabilities": ["chat", "code", "reasoning", "streaming"],
        "context_window": "128k tokens",
        "cost": "API key based",
    }
