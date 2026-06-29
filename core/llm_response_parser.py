"""
C90 — LLM Response Parser
Extracts structured data and tool calls from raw LLM output.
Handles JSON, fenced JSON, XML tags, regex, and schema-based extraction.
Includes JSON repair for common model formatting errors.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolCall:
    name: str
    arguments: dict
    call_id: Optional[str] = None


@dataclass
class ParseResult:
    success: bool
    data: Any = None
    errors: list[str] = field(default_factory=list)
    raw: str = ""

    @classmethod
    def ok(cls, data: Any, raw: str = "") -> "ParseResult":
        return cls(success=True, data=data, raw=raw)

    @classmethod
    def fail(cls, error: str, raw: str = "") -> "ParseResult":
        return cls(success=False, errors=[error], raw=raw)


class LLMResponseParser:
    """
    Parses LLM text responses into structured data.
    """

    def extract_json(self, text: str) -> ParseResult:
        result = self._extract_fenced_json(text)
        if result.success:
            return result
        return self._extract_bare_json(text)

    def _extract_fenced_json(self, text: str) -> ParseResult:
        pattern = r"```(?:json)?\s*([\s\S]*?)```"
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return ParseResult.fail("No fenced JSON block found", raw=text)
        return self._parse_json_with_repair(match.group(1).strip())

    def _extract_bare_json(self, text: str) -> ParseResult:
        for start_char, end_char in ("{", "}"), ("[", "]"):
            start = text.find(start_char)
            if start == -1:
                continue
            end = self._find_matching_bracket(text, start, start_char, end_char)
            if end != -1:
                result = self._parse_json_with_repair(text[start:end + 1])
                if result.success:
                    return result
        return ParseResult.fail("No valid JSON found in text", raw=text)

    def _find_matching_bracket(self, text: str, start: int, open_b: str, close_b: str) -> int:
        depth = 0
        in_string = False
        escape_next = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape_next:
                escape_next = False
                continue
            if ch == "\\" and in_string:
                escape_next = True
                continue
            if ch == '"' and not escape_next:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == open_b:
                depth += 1
            elif ch == close_b:
                depth -= 1
                if depth == 0:
                    return i
        return -1

    def _parse_json_with_repair(self, text: str) -> ParseResult:
        try:
            return ParseResult.ok(json.loads(text), raw=text)
        except json.JSONDecodeError:
            pass
        repaired = self._repair_json(text)
        try:
            return ParseResult.ok(json.loads(repaired), raw=text)
        except json.JSONDecodeError as e:
            return ParseResult.fail(f"JSON parse error after repair: {e}", raw=text)

    def _repair_json(self, text: str) -> str:
        text = re.sub(r",\s*([}\]])", r"\1", text)
        text = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', text)
        text = re.sub(r'#[^\n]*', '', text)
        text = text.replace("None", "null").replace("True", "true").replace("False", "false")
        return text

    def extract_xml_tag(self, text: str, tag: str) -> ParseResult:
        pattern = rf"<{re.escape(tag)}[^>]*>([\s\S]*?)</{re.escape(tag)}>"
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return ParseResult.fail(f"Tag <{tag}> not found", raw=text)
        return ParseResult.ok(match.group(1).strip(), raw=text)

    def extract_all_xml_tags(self, text: str, tag: str) -> list[str]:
        pattern = rf"<{re.escape(tag)}[^>]*>([\s\S]*?)</{re.escape(tag)}>"
        return re.findall(pattern, text, re.IGNORECASE)

    def extract_pattern(self, text: str, pattern: str, group: int = 1) -> ParseResult:
        match = re.search(pattern, text, re.DOTALL)
        if not match:
            return ParseResult.fail(f"Pattern not found: {pattern}", raw=text)
        try:
            return ParseResult.ok(match.group(group), raw=text)
        except IndexError:
            return ParseResult.ok(match.group(0), raw=text)

    def extract_with_schema(
        self,
        text: str,
        schema: dict,
        strict: bool = False,
    ) -> ParseResult:
        result = self.extract_json(text)
        if not result.success:
            return result
        data = result.data
        if not isinstance(data, dict):
            return ParseResult.fail("Expected JSON object, got array or primitive", raw=text)
        errors = []
        for key in schema.get("required", []):
            if key not in data:
                errors.append(f"Missing required field: '{key}'")
        if errors and strict:
            return ParseResult(success=False, errors=errors, raw=text)
        return ParseResult(success=len(errors) == 0, data=data, errors=errors, raw=text)

    def extract_tool_calls(
        self,
        response: Any,
        provider: str = "openai",
    ) -> list[ToolCall]:
        if hasattr(response, "tool_calls") and hasattr(response, "content"):
            return self._parse_llmresponse_tool_calls(response)
        if provider in ("openai", "ollama"):
            return self._parse_openai_tool_calls(response)
        elif provider == "anthropic":
            return self._parse_anthropic_tool_calls(response)
        content = getattr(response, "content", str(response))
        return self._parse_text_tool_calls(content)

    def _parse_llmresponse_tool_calls(self, response) -> list[ToolCall]:
        result = []
        for tc in response.tool_calls:
            args = tc.get("arguments", {})
            if isinstance(args, str):
                r = self._parse_json_with_repair(args)
                args = r.data if r.success else {}
            result.append(ToolCall(name=tc["name"], arguments=args, call_id=tc.get("id")))
        return result

    def _parse_openai_tool_calls(self, response) -> list[ToolCall]:
        result = []
        for choice in getattr(response, "choices", []):
            message = getattr(choice, "message", None)
            if message is None:
                continue
            for tc in getattr(message, "tool_calls", None) or []:
                fn = tc.function
                args = {}
                if fn.arguments:
                    r = self._parse_json_with_repair(fn.arguments)
                    args = r.data if r.success else {}
                result.append(ToolCall(name=fn.name, arguments=args, call_id=tc.id))
        return result

    def _parse_anthropic_tool_calls(self, response) -> list[ToolCall]:
        result = []
        for block in getattr(response, "content", []):
            if getattr(block, "type", None) == "tool_use":
                args = block.input if isinstance(block.input, dict) else {}
                result.append(ToolCall(name=block.name, arguments=args, call_id=block.id))
        return result

    def _parse_text_tool_calls(self, text: str, tool_call_tag: str = "tool_call") -> list[ToolCall]:
        result = []
        for raw in self.extract_all_xml_tags(text, tool_call_tag):
            parse = self._parse_json_with_repair(raw.strip())
            if parse.success and isinstance(parse.data, dict):
                name = parse.data.get("name", "")
                args = parse.data.get("arguments", parse.data.get("args", {}))
                if name:
                    result.append(ToolCall(name=name, arguments=args))
        return result

    def extract_thinking(self, text: str) -> Optional[str]:
        result = self.extract_xml_tag(text, "thinking")
        return result.data if result.success else None

    def extract_answer(self, text: str) -> Optional[str]:
        result = self.extract_xml_tag(text, "answer")
        return result.data if result.success else None
