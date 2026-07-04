"""
C126 — Domain Model Registry
Maps specialized model profiles (law, science, coding) to domain optimized models.
"""
from __future__ import annotations
from typing import Dict

class DomainModelRegistry:
    def __init__(self):
        self._mappings: Dict[str, str] = {
            "coding": "deepseek-coder",
            "science": "galactica",
            "general": "llama-3"
        }

    def get_model_for_domain(self, domain: str) -> str:
        return self._mappings.get(domain, self._mappings["general"])
