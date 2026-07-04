"""
C122 — Intent Classifier
Classifies prompt intent to route to custom skills or direct tool calls.
"""
from __future__ import annotations

class IntentClassifier:
    @staticmethod
    def classify_intent(text: str) -> str:
        q = text.lower()
        if any(w in q for w in ["search", "find", "who", "what"]):
            return "query"
        elif any(w in q for w in ["code", "write", "build", "script"]):
            return "code"
        return "general"
