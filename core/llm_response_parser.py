"""C90 — LLM Response Parser

Structured output extraction and validation from raw LLM responses.
Handles:
  * JSON extraction from fenced code blocks or bare JSON embedded in prose
  * Strict / lenient JSON repair (trailing commas, single quotes, etc.)
  * Schema validation against a user-supplied dict schema (lite, stdlib-only)
  * Typed field coercion (str → int, str → bool, str → list, etc.)
  * Key normalisation (snake_case, camelCase → canonical form)
  * Extraction of reasoning traces, chain-of-thought tags, and tool-call blocks
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional, TypeVar, Type

from core.structured_logger import get_logger

log = get_logger(__name__)

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
_JSON_FENCE = re.compile(
    r"```(?:json)?\s*\n?(?P<body>[\s\S]*?)\n?```",
    re.IGNORECASE,
)
_BARE_JSON_OBJ = re.compile(r"(?s)\{.*\}", re.DOTALL)
_BARE_JSON_ARR = re.compile(r"(?s)\[.*\]", re.DOTALL)
_THINK_TAG = re.compile(r"<think>(?P<trace>[\s\S]*?)</think>", re.IGNORECASE)
_REASON_TAG = re.compile(r"<reasoning>(?P<trace>[\s\S]*?)</reasoning>", re.IGNORECASE)
_TOOL_CALL_TAG = re.compile(
    r"<tool_call>(?P<body>[\s\S]*?)</tool_call>", re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ParseResult:
    raw_text: str
    extracted: Optional[Any] = None          # parsed Python object
    reasoning_trace: Optional[str] = None    # <think>…</think> content
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    repaired: bool = False                   # True if JSON required repair

    @property
    def ok(self) -> bool:
        return not self.errors and self.extracted is not None


@dataclass
class FieldSpec:
    """Declare an expected field for schema-lite validation."""
    type: type
    required: bool = True
    default: Any = None
    choices: Optional[list[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


# ---------------------------------------------------------------------------
# JSON repair helpers
# ---------------------------------------------------------------------------

def _repair_json(text: str) -> str:
    """Apply lightweight heuristic fixes to near-valid JSON."""
    # Remove JS-style // line comments
    text = re.sub(r"//[^\n]*", "", text)
    # Remove /* */ block comments
    text = re.sub(r"/\*[\s\S]*?\*/", "", text)
    # Trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)
    # Single-quoted strings → double-quoted (naive, avoids apostrophes in words)
    text = re.sub(r"(?<![\w])'([^']*?)'(?![\w])", r'"\1"', text)
    # Python True/False/None → JSON
    text = re.sub(r"\bTrue\b", "true", text)
    text = re.sub(r"\bFalse\b", "false", text)
    text = re.sub(r"\bNone\b", "null", text)
    return text


# ---------------------------------------------------------------------------
# Main extractor
# ---------------------------------------------------------------------------

def _extract_json_text(text: str) -> Optional[str]:
    """Return the first plausible JSON string from *text*, or None."""
    # 1. Fenced code block
    m = _JSON_FENCE.search(text)
    if m:
        return m.group("body").strip()
    # 2. Bare JSON object
    m = _BARE_JSON_OBJ.search(text)
    if m:
        return m.group(0)
    # 3. Bare JSON array
    m = _BARE_JSON_ARR.search(text)
    if m:
        return m.group(0)
    return None


def _parse_json_with_repair(
    raw: str, strict: bool = False
) -> tuple[Any, bool, list[str]]:
    """Attempt to parse JSON; optionally repair and retry.
    Returns (object, repaired, errors).
    """
    try:
        return json.loads(raw), False, []
    except json.JSONDecodeError as exc:
        if strict:
            return None, False, [f"JSON parse error: {exc}"]
        repaired = _repair_json(raw)
        try:
            return json.loads(repaired), True, []
        except json.JSONDecodeError as exc2:
            return None, False, [f"JSON parse error (after repair): {exc2}"]


# ---------------------------------------------------------------------------
# Schema-lite validation
# ---------------------------------------------------------------------------

def _coerce(value: Any, target: type) -> tuple[Any, Optional[str]]:
    """Attempt to coerce *value* to *target* type. Returns (coerced, error)."""
    if isinstance(value, target):
        return value, None
    try:
        if target is bool:
            if isinstance(value, str):
                if value.lower() in ("true", "1", "yes"):
                    return True, None
                if value.lower() in ("false", "0", "no"):
                    return False, None
            return bool(value), None
        if target is int:
            return int(value), None
        if target is float:
            return float(value), None
        if target is str:
            return str(value), None
        if target is list and isinstance(value, str):
            return json.loads(value), None
        if target is dict and isinstance(value, str):
            return json.loads(value), None
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        return value, f"Cannot coerce {value!r} to {target.__name__}: {exc}"
    return value, f"No coercion rule from {type(value).__name__} to {target.__name__}"


def validate_schema(
    obj: dict[str, Any],
    schema: dict[str, FieldSpec],
    coerce: bool = True,
) -> tuple[dict[str, Any], list[str]]:
    """Validate and optionally coerce *obj* against a ``FieldSpec`` schema.
    Returns (validated_obj, errors).
    """
    errors: list[str] = []
    result = dict(obj)

    for field_name, spec in schema.items():
        if field_name not in result:
            if spec.required:
                errors.append(f"Missing required field: '{field_name}'")
            else:
                result[field_name] = spec.default
            continue

        val = result[field_name]

        if coerce:
            val, err = _coerce(val, spec.type)
            if err:
                errors.append(f"Field '{field_name}': {err}")
            else:
                result[field_name] = val

        if spec.choices is not None and val not in spec.choices:
            errors.append(
                f"Field '{field_name}' value {val!r} not in {spec.choices}"
            )
        if spec.min_value is not None:
            try:
                if float(val) < spec.min_value:
                    errors.append(
                        f"Field '{field_name}' {val} < min {spec.min_value}"
                    )
            except (TypeError, ValueError):
                pass
        if spec.max_value is not None:
            try:
                if float(val) > spec.max_value:
                    errors.append(
                        f"Field '{field_name}' {val} > max {spec.max_value}"
                    )
            except (TypeError, ValueError):
                pass

    return result, errors


# ---------------------------------------------------------------------------
# Key normalisation
# ---------------------------------------------------------------------------

_CAMEL_RE = re.compile(r"(?<=[a-z0-9])([A-Z])")


def _to_snake(name: str) -> str:
    return _CAMEL_RE.sub(r"_\1", name).lower()


def normalise_keys(obj: Any, style: str = "snake") -> Any:
    """Recursively convert dict keys to snake_case (or leave as-is)."""
    if isinstance(obj, dict):
        return {
            (_to_snake(k) if style == "snake" else k): normalise_keys(v, style)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [normalise_keys(i, style) for i in obj]
    return obj


# ---------------------------------------------------------------------------
# Trace + tool-call extraction
# ---------------------------------------------------------------------------

def _extract_reasoning(text: str) -> tuple[Optional[str], str]:
    """Return (trace_text, cleaned_text) stripping <think>/<reasoning> tags."""
    for pattern in (_THINK_TAG, _REASON_TAG):
        m = pattern.search(text)
        if m:
            trace = m.group("trace").strip()
            cleaned = pattern.sub("", text).strip()
            return trace, cleaned
    return None, text


def _extract_tool_calls(text: str) -> tuple[list[dict[str, Any]], str]:
    """Return (tool_calls, cleaned_text) from <tool_call>…</tool_call> tags."""
    calls: list[dict[str, Any]] = []
    cleaned = text
    for m in _TOOL_CALL_TAG.finditer(text):
        body = m.group("body").strip()
        try:
            obj = json.loads(body)
            calls.append(obj)
        except json.JSONDecodeError:
            repaired = _repair_json(body)
            try:
                calls.append(json.loads(repaired))
            except json.JSONDecodeError:
                log.warning("llm_response_parser.bad_tool_call", body=body[:80])
    cleaned = _TOOL_CALL_TAG.sub("", cleaned).strip()
    return calls, cleaned


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class LLMResponseParser:
    """Parse, validate, and normalise raw LLM response text.

    Usage::

        parser = LLMResponseParser()

        # Extract a JSON object from a response
        result = parser.parse_json(response.content)
        if result.ok:
            data = result.extracted

        # Extract and validate against a schema
        schema = {
            "action": FieldSpec(str, required=True, choices=["search", "done"]),
            "query":  FieldSpec(str, required=False, default=""),
        }
        result = parser.parse_structured(response.content, schema=schema)
    """

    def __init__(self, strict: bool = False, normalise: str = "snake") -> None:
        """Args:
            strict: If True, do not attempt JSON repair.
            normalise: Key normalisation style ("snake" | "none").
        """
        self._strict = strict
        self._normalise = normalise

    # ------------------------------------------------------------------
    # JSON extraction
    # ------------------------------------------------------------------

    def parse_json(
        self,
        text: str,
        repair: bool = True,
    ) -> ParseResult:
        """Extract the first JSON object/array from *text*."""
        trace, text = _extract_reasoning(text)
        tool_calls, text = _extract_tool_calls(text)

        json_text = _extract_json_text(text)
        if json_text is None:
            return ParseResult(
                raw_text=text,
                reasoning_trace=trace,
                tool_calls=tool_calls,
                errors=["No JSON found in response."],
            )

        obj, repaired, errors = _parse_json_with_repair(
            json_text, strict=self._strict or not repair
        )
        if errors:
            return ParseResult(
                raw_text=text,
                reasoning_trace=trace,
                tool_calls=tool_calls,
                errors=errors,
            )

        if self._normalise != "none" and isinstance(obj, (dict, list)):
            obj = normalise_keys(obj, style=self._normalise)

        return ParseResult(
            raw_text=text,
            extracted=obj,
            reasoning_trace=trace,
            tool_calls=tool_calls,
            repaired=repaired,
        )

    # ------------------------------------------------------------------
    # Structured extraction + validation
    # ------------------------------------------------------------------

    def parse_structured(
        self,
        text: str,
        schema: dict[str, FieldSpec],
        coerce: bool = True,
        repair: bool = True,
    ) -> ParseResult:
        """Extract JSON and validate against *schema*."""
        result = self.parse_json(text, repair=repair)
        if not result.ok:
            return result
        if not isinstance(result.extracted, dict):
            result.errors.append(
                f"Expected a JSON object, got {type(result.extracted).__name__}."
            )
            return result
        validated, errors = validate_schema(result.extracted, schema, coerce=coerce)
        result.extracted = validated
        result.errors.extend(errors)
        return result

    # ------------------------------------------------------------------
    # Plain text helpers
    # ------------------------------------------------------------------

    def extract_reasoning(self, text: str) -> tuple[Optional[str], str]:
        """Return (reasoning_trace, cleaned_text)."""
        return _extract_reasoning(text)

    def extract_tool_calls(
        self, text: str
    ) -> tuple[list[dict[str, Any]], str]:
        """Return (tool_calls, cleaned_text) from XML-style tool_call tags."""
        return _extract_tool_calls(text)

    def extract_code_blocks(
        self, text: str, language: str = ""
    ) -> list[str]:
        """Return all fenced code block bodies for a given language tag."""
        pattern = re.compile(
            r"```" + re.escape(language) + r"\s*\n?([\s\S]*?)\n?```",
            re.IGNORECASE,
        )
        return [m.group(1).strip() for m in pattern.finditer(text)]

    def to_typed(
        self, text: str, target: Type[T], repair: bool = True
    ) -> tuple[Optional[T], list[str]]:
        """Parse JSON and attempt to instantiate *target* dataclass/namedtuple.
        Returns (instance, errors).
        """
        result = self.parse_json(text, repair=repair)
        if not result.ok:
            return None, result.errors
        try:
            return target(**result.extracted), []  # type: ignore[call-arg]
        except (TypeError, KeyError) as exc:
            return None, [f"Cannot instantiate {target.__name__}: {exc}"]
