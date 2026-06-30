"""C88 — LLM Client

Unified API adapter for OpenAI, Anthropic, Google Gemini, and Ollama (local).
Supports both streaming and non-streaming responses, automatic retries,
timeout handling, and per-provider token counting.

All calls are stdlib-only at the transport shim layer; actual HTTP is
delegated to core/http_client.py (C67) so this module stays zero-dep.

Architecture invariants honoured:
  - Every call is logged to AuditLogger (C71) BEFORE dispatch.
  - Forward stubs for PromptNormalizer (C121) and ReasoningEngine (C123)
    are wired in; swap out stubs for real imports when Blocks 24 land.
  - reasoning_trace field carried on every LLMResponse.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Generator, Iterator, Optional

from core.http_client import HttpClient
from core.structured_logger import get_logger
from core.circuit_breaker import CircuitBreaker
from core.retry_policy import RetryPolicy
from core.rate_limiter_core import RateLimiter

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Provider(str, Enum):
    OPENAI    = "openai"
    ANTHROPIC = "anthropic"
    GEMINI    = "gemini"
    OLLAMA    = "ollama"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


@dataclass
class LLMToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    id: str
    provider: Provider
    model: str
    content: str
    tool_calls: list[LLMToolCall] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"
    latency_ms: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)
    # Invariant #9: every response carries a reasoning_trace (populated by C123)
    reasoning_trace: Optional[str] = None


@dataclass
class LLMRequest:
    messages: list[LLMMessage]
    model: str
    provider: Provider
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False
    tools: list[dict[str, Any]] = field(default_factory=list)
    tool_choice: str = "auto"
    timeout: float = 60.0
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # Forward-stub flags — set True by the respective modules when they land
    _normalised: bool = False
    _react_prepared: bool = False


# ---------------------------------------------------------------------------
# Forward stubs — Block 24 (C121 / C123)
# ---------------------------------------------------------------------------

def _apply_prompt_normalizer(req: LLMRequest) -> LLMRequest:
    """
    Stub for PromptNormalizer (C121).
    Replace body with real call once Block 24 lands:
        from core.prompt_normalizer import PromptNormalizer
        return PromptNormalizer.instance().normalise(req)
    """
    req._normalised = True
    return req


def _apply_reasoning_engine(req: LLMRequest) -> tuple[LLMRequest, Optional[str]]:
    """
    Stub for ReasoningEngine ReAct loop (C123).
    Replace body with real call once Block 24 lands:
        from core.reasoning_engine import ReasoningEngine
        return ReasoningEngine.instance().prepare(req)
    Returns (prepared_request, reasoning_trace_or_None).
    """
    req._react_prepared = True
    trace = "[ReAct stub — C123 not yet installed]"
    return req, trace


# ---------------------------------------------------------------------------
# Audit helper — C71
# ---------------------------------------------------------------------------

def _audit(action: str, payload: dict[str, Any]) -> None:
    """Write to AuditLogger (C71). Gracefully degrades if module not loaded."""
    try:
        from core.audit_logger import AuditLogger  # type: ignore
        AuditLogger.instance().record(action=action, payload=payload)
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# Provider adapters
# ---------------------------------------------------------------------------

class _ProviderAdapter:
    """Base adapter — subclasses normalise provider-specific wire formats."""

    BASE_URL: str = ""

    def __init__(self, api_key: str, http: HttpClient) -> None:
        self._api_key = api_key
        self._http = http

    def build_payload(self, req: LLMRequest) -> tuple[str, dict, dict]:
        """Return (url, headers, body)."""
        raise NotImplementedError

    def parse_response(self, provider: Provider, model: str,
                       raw: dict, latency_ms: float) -> LLMResponse:
        raise NotImplementedError

    def iter_stream(self, provider: Provider, model: str,
                    url: str, headers: dict, body: dict) -> Iterator[str]:
        raise NotImplementedError


class _OpenAIAdapter(_ProviderAdapter):
    BASE_URL = "https://api.openai.com/v1/chat/completions"

    def build_payload(self, req: LLMRequest) -> tuple[str, dict, dict]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        messages = [
            {"role": m.role, "content": m.content,
             **(({"tool_call_id": m.tool_call_id} if m.tool_call_id else {}))}
            for m in req.messages
        ]
        body: dict[str, Any] = {
            "model": req.model,
            "messages": messages,
            "temperature": req.temperature,
            "max_tokens": req.max_tokens,
            "stream": req.stream,
        }
        if req.tools:
            body["tools"] = req.tools
            body["tool_choice"] = req.tool_choice
        return self.BASE_URL, headers, body

    def parse_response(self, provider: Provider, model: str,
                       raw: dict, latency_ms: float) -> LLMResponse:
        choice = raw["choices"][0]
        msg = choice["message"]
        tool_calls = [
            LLMToolCall(
                id=tc["id"],
                name=tc["function"]["name"],
                arguments=json.loads(tc["function"]["arguments"]),
            )
            for tc in msg.get("tool_calls", [])
        ]
        usage = raw.get("usage", {})
        return LLMResponse(
            id=raw.get("id", str(uuid.uuid4())),
            provider=provider,
            model=model,
            content=msg.get("content") or "",
            tool_calls=tool_calls,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
            latency_ms=latency_ms,
            raw=raw,
        )

    def iter_stream(self, provider: Provider, model: str,
                    url: str, headers: dict, body: dict) -> Iterator[str]:
        for chunk in self._http.stream_post(url, headers=headers, json=body):
            data = chunk.lstrip("data: ").strip()
            if data in ("", "[DONE]"):
                continue
            try:
                obj = json.loads(data)
                delta = obj["choices"][0]["delta"].get("content") or ""
                if delta:
                    yield delta
            except (KeyError, json.JSONDecodeError):
                continue


class _AnthropicAdapter(_ProviderAdapter):
    BASE_URL = "https://api.anthropic.com/v1/messages"

    def build_payload(self, req: LLMRequest) -> tuple[str, dict, dict]:
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        system = next(
            (m.content for m in req.messages if m.role == "system"), None
        )
        messages = [
            {"role": m.role, "content": m.content}
            for m in req.messages if m.role != "system"
        ]
        body: dict[str, Any] = {
            "model": req.model,
            "messages": messages,
            "max_tokens": req.max_tokens,
            "temperature": req.temperature,
            "stream": req.stream,
        }
        if system:
            body["system"] = system
        if req.tools:
            body["tools"] = req.tools
        return self.BASE_URL, headers, body

    def parse_response(self, provider: Provider, model: str,
                       raw: dict, latency_ms: float) -> LLMResponse:
        content_blocks = raw.get("content", [])
        text = "".join(
            b.get("text", "") for b in content_blocks if b.get("type") == "text"
        )
        tool_calls = [
            LLMToolCall(
                id=b.get("id", str(uuid.uuid4())),
                name=b["name"],
                arguments=b.get("input", {}),
            )
            for b in content_blocks if b.get("type") == "tool_use"
        ]
        usage = raw.get("usage", {})
        return LLMResponse(
            id=raw.get("id", str(uuid.uuid4())),
            provider=provider,
            model=model,
            content=text,
            tool_calls=tool_calls,
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            finish_reason=raw.get("stop_reason", "stop"),
            latency_ms=latency_ms,
            raw=raw,
        )

    def iter_stream(self, provider: Provider, model: str,
                    url: str, headers: dict, body: dict) -> Iterator[str]:
        for chunk in self._http.stream_post(url, headers=headers, json=body):
            if not chunk.startswith("data:"):
                continue
            data = chunk[5:].strip()
            try:
                obj = json.loads(data)
                if obj.get("type") == "content_block_delta":
                    delta = obj.get("delta", {}).get("text") or ""
                    if delta:
                        yield delta
            except json.JSONDecodeError:
                continue


class _GeminiAdapter(_ProviderAdapter):
    BASE_URL = (
        "https://generativelanguage.googleapis.com/v1beta/models"
        "/{model}:generateContent?key={key}"
    )

    def build_payload(self, req: LLMRequest) -> tuple[str, dict, dict]:
        url = self.BASE_URL.format(model=req.model, key=self._api_key)
        headers = {"Content-Type": "application/json"}
        parts = [
            {"text": m.content}
            for m in req.messages if m.role in ("user", "assistant")
        ]
        body: dict[str, Any] = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": req.temperature,
                "maxOutputTokens": req.max_tokens,
            },
        }
        return url, headers, body

    def parse_response(self, provider: Provider, model: str,
                       raw: dict, latency_ms: float) -> LLMResponse:
        candidate = raw["candidates"][0]
        text = "".join(
            p.get("text", "")
            for p in candidate["content"].get("parts", [])
        )
        usage = raw.get("usageMetadata", {})
        return LLMResponse(
            id=str(uuid.uuid4()),
            provider=provider,
            model=model,
            content=text,
            prompt_tokens=usage.get("promptTokenCount", 0),
            completion_tokens=usage.get("candidatesTokenCount", 0),
            total_tokens=usage.get("totalTokenCount", 0),
            finish_reason=candidate.get("finishReason", "STOP").lower(),
            latency_ms=latency_ms,
            raw=raw,
        )

    def iter_stream(self, provider, model, url, headers, body):
        for line in self._http.stream_post(url, headers=headers, json=body):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                text = "".join(
                    p.get("text", "")
                    for p in obj["candidates"][0]["content"].get("parts", [])
                )
                if text:
                    yield text
            except (KeyError, json.JSONDecodeError):
                continue


class _OllamaAdapter(_ProviderAdapter):
    """Ollama local inference (default base http://localhost:11434)."""

    BASE_URL = "http://localhost:11434/api/chat"

    def build_payload(self, req: LLMRequest) -> tuple[str, dict, dict]:
        headers = {"Content-Type": "application/json"}
        messages = [
            {"role": m.role, "content": m.content} for m in req.messages
        ]
        body: dict[str, Any] = {
            "model": req.model,
            "messages": messages,
            "stream": req.stream,
            "options": {
                "temperature": req.temperature,
                "num_predict": req.max_tokens,
            },
        }
        return self.BASE_URL, headers, body

    def parse_response(self, provider: Provider, model: str,
                       raw: dict, latency_ms: float) -> LLMResponse:
        msg = raw.get("message", {})
        return LLMResponse(
            id=str(uuid.uuid4()),
            provider=provider,
            model=model,
            content=msg.get("content", ""),
            prompt_tokens=raw.get("prompt_eval_count", 0),
            completion_tokens=raw.get("eval_count", 0),
            total_tokens=raw.get("prompt_eval_count", 0) + raw.get("eval_count", 0),
            finish_reason="stop" if raw.get("done") else "length",
            latency_ms=latency_ms,
            raw=raw,
        )

    def iter_stream(self, provider, model, url, headers, body):
        for line in self._http.stream_post(url, headers=headers, json=body):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                delta = obj.get("message", {}).get("content") or ""
                if delta:
                    yield delta
            except json.JSONDecodeError:
                continue


_ADAPTER_MAP: dict[Provider, type[_ProviderAdapter]] = {
    Provider.OPENAI:    _OpenAIAdapter,
    Provider.ANTHROPIC: _AnthropicAdapter,
    Provider.GEMINI:    _GeminiAdapter,
    Provider.OLLAMA:    _OllamaAdapter,
}


# ---------------------------------------------------------------------------
# LLMClient — public API
# ---------------------------------------------------------------------------

class LLMClient:
    """Unified LLM client — create once, call any provider.

    Usage::

        client = LLMClient()
        client.register(Provider.OPENAI, api_key="sk-...")
        response = client.complete(LLMRequest(
            provider=Provider.OPENAI,
            model="gpt-4o",
            messages=[LLMMessage(role="user", content="Hello!")],
        ))
        print(response.content)
        print(response.reasoning_trace)   # set by C123 when live
    """

    def __init__(
        self,
        http: Optional[HttpClient] = None,
        retry: Optional[RetryPolicy] = None,
    ) -> None:
        self._http    = http or HttpClient()
        self._retry   = retry or RetryPolicy(max_attempts=3, base_delay=1.0)
        self._adapters: dict[Provider, _ProviderAdapter] = {}
        self._breakers: dict[Provider, CircuitBreaker]   = {}
        self._limiters: dict[Provider, RateLimiter]      = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        provider: Provider,
        api_key: str = "",
        base_url: Optional[str] = None,
        rpm: int = 60,
    ) -> None:
        """Register a provider with its API key and optional rate limit."""
        cls     = _ADAPTER_MAP[provider]
        adapter = cls(api_key=api_key, http=self._http)
        if base_url and hasattr(adapter, "BASE_URL"):
            adapter.BASE_URL = base_url  # type: ignore[attr-defined]
        self._adapters[provider] = adapter
        self._breakers[provider] = CircuitBreaker(name=f"llm:{provider.value}")
        self._limiters[provider] = RateLimiter(rate=rpm, per=60.0)
        log.info("llm_client.registered", provider=provider.value)

    @classmethod
    def from_env(cls) -> "LLMClient":
        """Build a client pre-loaded from environment variables:

            SR_OPENAI_API_KEY, SR_OPENAI_BASE_URL
            SR_ANTHROPIC_API_KEY
            SR_GEMINI_API_KEY
            SR_OLLAMA_BASE_URL  (defaults to http://localhost:11434)
        """
        import os
        client = cls()
        if key := os.getenv("SR_OPENAI_API_KEY"):
            client.register(Provider.OPENAI, api_key=key,
                            base_url=os.getenv("SR_OPENAI_BASE_URL"))
        if key := os.getenv("SR_ANTHROPIC_API_KEY"):
            client.register(Provider.ANTHROPIC, api_key=key)
        if key := os.getenv("SR_GEMINI_API_KEY"):
            client.register(Provider.GEMINI, api_key=key)
        client.register(
            Provider.OLLAMA,
            base_url=os.getenv("SR_OLLAMA_BASE_URL", "http://localhost:11434"),
        )
        return client

    # ------------------------------------------------------------------
    # Internal pipeline: normalise → ReAct → audit → dispatch
    # ------------------------------------------------------------------

    def _prepare(self, req: LLMRequest) -> tuple[LLMRequest, Optional[str]]:
        """Run C121 normalisation stub + C123 ReAct stub."""
        req = _apply_prompt_normalizer(req)
        req, trace = _apply_reasoning_engine(req)
        return req, trace

    # ------------------------------------------------------------------
    # Core call
    # ------------------------------------------------------------------

    def complete(self, req: LLMRequest) -> LLMResponse:
        """Execute a blocking (non-streaming) LLM call."""
        req, trace = self._prepare(req)
        adapter    = self._get_adapter(req.provider)
        url, headers, body = adapter.build_payload(req)
        self._limiters[req.provider].acquire()

        # Invariant #2: audit BEFORE execution
        _audit("llm_call_start", {
            "request_id": req.request_id,
            "provider":   req.provider.value,
            "model":      req.model,
            "messages":   len(req.messages),
            "stream":     False,
        })

        t0 = time.monotonic()
        raw = self._breakers[req.provider].call(
            lambda: self._retry.execute(
                lambda: self._http.post_json(url, headers=headers, json=body,
                                             timeout=req.timeout)
            )
        )
        latency_ms = (time.monotonic() - t0) * 1000

        response = adapter.parse_response(req.provider, req.model, raw, latency_ms)
        response.reasoning_trace = trace  # Invariant #9

        _audit("llm_call_end", {
            "request_id":      req.request_id,
            "finish_reason":   response.finish_reason,
            "total_tokens":    response.total_tokens,
            "latency_ms":      round(latency_ms, 1),
        })
        log.info(
            "llm_client.complete",
            provider=req.provider.value,
            model=req.model,
            total_tokens=response.total_tokens,
            latency_ms=round(latency_ms, 1),
            request_id=req.request_id,
        )
        return response

    def stream(
        self, req: LLMRequest
    ) -> Generator[str, None, None]:
        """Yield content delta strings as the model produces them."""
        req.stream  = True
        req, trace  = self._prepare(req)
        adapter     = self._get_adapter(req.provider)
        url, headers, body = adapter.build_payload(req)
        self._limiters[req.provider].acquire()

        _audit("llm_stream_start", {
            "request_id": req.request_id,
            "provider":   req.provider.value,
            "model":      req.model,
        })

        yield from self._breakers[req.provider].call(
            lambda: adapter.iter_stream(req.provider, req.model, url, headers, body)
        )

        _audit("llm_stream_end", {"request_id": req.request_id})

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_adapter(self, provider: Provider) -> _ProviderAdapter:
        if provider not in self._adapters:
            raise RuntimeError(
                f"Provider '{provider.value}' not registered. "
                "Call client.register() or use LLMClient.from_env()."
            )
        return self._adapters[provider]

    def available_providers(self) -> list[Provider]:
        return list(self._adapters.keys())

    def health(self) -> dict[str, str]:
        return {
            p.value: ("open" if self._breakers[p].is_closed else "tripped")
            for p in self._adapters
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_client: Optional[LLMClient] = None


def get_client() -> LLMClient:
    """Return the module-level default client, initialised from env on first call."""
    global _default_client
    if _default_client is None:
        _default_client = LLMClient.from_env()
    return _default_client
