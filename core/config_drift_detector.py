"""
C104 — Config Drift Detector
Validates local configuration files against reference templates to detect divergence.
"""
from __future__ import annotations
from typing import Dict, Any, List

class ConfigDriftDetector:
    @staticmethod
    def detect_drift(current: Dict[str, Any], reference: Dict[str, Any]) -> List[str]:
        drifted_keys = []
        for k, v in reference.items():
            if k not in current:
                drifted_keys.append(f"Missing key: {k}")
            elif current[k] != v:
                drifted_keys.append(f"Value mismatch for key '{k}': expected {v}, got {current[k]}")
        return drifted_keys
