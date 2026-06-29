"""
C88 — LLM Client
Unified interface for OpenAI, Anthropic, Gemini, and Ollama.
Supports sync complete(), async acomplete(), and streaming.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Iterator, Optional


@dataclass
class LLMMessage:
    role: str  # 'system' | 'user' | 'assistant' | 'tool'
    content: str
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    finish_reason: str = "stop"
    tool_calls: list[dict] = field(default_factory=list)
    raw: Any = None


class LLMError(Exception):
    pass


class RateLimitError(LLMError):
    pass


class LLMClient:
    """
    Unified LLM client. Provider detected from model prefix or explicit provider arg.
    Supported providers: openai, anthropic, gemini, ollama.
    """

    PROVIDER_PREFIXES = {
        "gpt": "openai",
        "o1": "openai",
        "o3": "openai",
        "claude": "anthropic",
        "gemini": "gemini",
        "llama": "ollama",
        "mistral": "ollama",
        "phi": "ollama",
    }

    def __init__(
        self,
        model: str = "gpt-4o",
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        timeout: float = 60.0,
        max_retries: int = 3,
        retry_base_delay: float = 1.0,
    ):
        self.model = model
        self.provider = provider or self._detect_provider(model)
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self._client = None

    def _detect_provider(self, model: str) -> str:
        lower = model.lower()
        for prefix, provider in self.PROVIDER_PREFIXES.items():
            if lower.startswith(prefix):
                return provider
        return "openai"

    def _get_client(self):
        if self._client is not None:
            return self._client
        if self.provider == "openai":
            from openai import OpenAI
            kwargs = {}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = OpenAI(**kwargs)
        elif self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        elif self.provider == "gemini":
            import google.generativeai as genai
            if self.api_key:
                genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
        elif self.provider == "ollama":
            from openai import OpenAI
            self._client = OpenAI(
                base_url=self.base_url or "http://localhost:11434/v1",
                api_key="ollama",
            )
        else:
            raise LLMError(f"Unsupported provider: {self.provider}")
        return self._client

    def _messages_to_openai(self, messages: list[LLMMessage]) -> list[dict]:
        result = []
        for m in messages:
            entry: dict = {"role": m.role, "content": m.content}
            if m.tool_call_id:
                entry["tool_call_id"] = m.tool_call_id
            if m.name:
                entry["name"] = m.name
            result.append(entry)
        return result

    def _messages_to_anthropic(self, messages: list[LLMMessage]) -> tuple[str, list[dict]]:
        system = ""
        chat = []
        for m in messages:
            if m.role == "system":
                system = m.content
            else:
                chat.append({"role": m.role, "content": m.content})
        return system, chat

    def complete(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> LLMResponse:
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                return self._complete_once(messages, tools, **kwargs)
            except RateLimitError as e:
                last_exc = e
                delay = self.retry_base_delay * (2 ** attempt)
                time.sleep(delay)
            except LLMError:
                raise
        raise last_exc or LLMError("Max retries exceeded")

    def _complete_once(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> LLMResponse:
        client = self._get_client()

        if self.provider in ("openai", "ollama"):
            params: dict = {
                "model": self.model,
                "messages": self._messages_to_openai(messages),
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            }
            if tools:
                params["tools"] = tools
            resp = client.chat.completions.create(**params)
            choice = resp.choices[0]
            tool_calls = []
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    })
            return LLMResponse(
                content=choice.message.content or "",
                model=resp.model,
                usage=TokenUsage(
                    prompt_tokens=resp.usage.prompt_tokens,
                    completion_tokens=resp.usage.completion_tokens,
                    total_tokens=resp.usage.total_tokens,
                ),
                finish_reason=choice.finish_reason or "stop",
                tool_calls=tool_calls,
                raw=resp,
            )

        elif self.provider == "anthropic":
            system, chat = self._messages_to_anthropic(messages)
            params = {
                "model": self.model,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "messages": chat,
            }
            if system:
                params["system"] = system
            if tools:
                params["tools"] = tools
            resp = client.messages.create(**params)
            content_text = ""
            tool_calls = []
            for block in resp.content:
                if hasattr(block, "text"):
                    content_text += block.text
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "arguments": block.input,
                    })
            return LLMResponse(
                content=content_text,
                model=resp.model,
                usage=TokenUsage(
                    prompt_tokens=resp.usage.input_tokens,
                    completion_tokens=resp.usage.output_tokens,
                    total_tokens=resp.usage.input_tokens + resp.usage.output_tokens,
                ),
                finish_reason=resp.stop_reason or "stop",
                tool_calls=tool_calls,
                raw=resp,
            )

        elif self.provider == "gemini":
            prompt = "\n".join(f"{m.role}: {m.content}" for m in messages)
            resp = client.generate_content(prompt)
            return LLMResponse(
                content=resp.text,
                model=self.model,
                raw=resp,
            )

        raise LLMError(f"Provider not handled: {self.provider}")

    async def acomplete(
        self,
        messages: list[LLMMessage],
        tools: Optional[list[dict]] = None,
        **kwargs,
    ) -> LLMResponse:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.complete(messages, tools, **kwargs)
        )

    def stream(
        self,
        messages: list[LLMMessage],
        **kwargs,
    ) -> Iterator[str]:
        client = self._get_client()
        if self.provider in ("openai", "ollama"):
            params = {
                "model": self.model,
                "messages": self._messages_to_openai(messages),
                "temperature": kwargs.get("temperature", self.temperature),
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "stream": True,
            }
            for chunk in client.chat.completions.create(**params):
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        elif self.provider == "anthropic":
            system, chat = self._messages_to_anthropic(messages)
            params = {
                "model": self.model,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "messages": chat,
            }
            if system:
                params["system"] = system
            with client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield text
        else:
            resp = self.complete(messages, **kwargs)
            yield resp.content

    async def astream(self, messages: list[LLMMessage], **kwargs) -> AsyncIterator[str]:
        loop = asyncio.get_event_loop()
        chunks = await loop.run_in_executor(None, lambda: list(self.stream(messages, **kwargs)))
        for chunk in chunks:
            yield chunk
