"""
C105 — Release Gate
Runs pre-release validation checks to block unstable releases.
"""
from __future__ import annotations
from typing import List

class ReleaseGate:
    @staticmethod
    def run_preflight_checks(tests_passed: bool, lint_passed: bool) -> List[str]:
        failures = []
        if not tests_passed:
            failures.append("Test suite failed")
        if not lint_passed:
            failures.append("Lint suite failed")
        return failures
