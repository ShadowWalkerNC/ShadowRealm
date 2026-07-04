"""
C121 — Prompt Normalizer
Strips and normalizes user prompt payloads before intent routing.
"""
from __future__ import annotations

class PromptNormalizer:
    @staticmethod
    def normalize(text: str) -> str:
        # Standardize whitespace and strip outer punctuation
        return text.strip().lower()
