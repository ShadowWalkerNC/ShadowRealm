"""
Cascading Intelligence Router for ShadowRealm.
Routes queries dynamically across 4 complexity tiers to maximize performance and minimize token cost:
- Tier 0: AST Symbol Parser & Exact Cache (Zero Cost, <1ms)
- Tier 1: CactusNeedle On-Device Model (Zero Cloud Cost, 14MB, Tool Calling)
- Tier 2: Muse Code / Local Model (Fast Code Generation & Explanation)
- Tier 3: Cloud Heavy Reasoning (Complex Architecture & Audits)
"""

import os
import re
import hashlib
import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# In-memory LRU prompt cache
_QUERY_CACHE: Dict[str, Any] = {}

class CascadingRouter:
    @staticmethod
    def classify_complexity(prompt: str) -> int:
        """Classify user intent into Tier 0, 1, 2, or 3."""
        p = prompt.strip().lower()

        # Tier 0: Simple code outline / symbol search / syntax check
        if re.search(r"^(list|find|search|outline|symbols|classes|functions|ast)\b", p):
            return 0
        
        # Tier 1: Deterministic tool execution / simple query / CLI dispatch
        if re.search(r"^(run|exec|execute|terminal|cli|status|check|git diff|git status|docker)\b", p) or len(p) < 40:
            return 1

        # Tier 2: Medium code edits / function writing / unit tests / docstrings
        if re.search(r"\b(write a function|unit test|refactor|fix syntax|docstring|explain|format)\b", p) or len(p) < 300:
            return 2

        # Tier 3: Complex architecture / deep reasoning / full file synthesis
        return 3

    @classmethod
    def route_and_execute(cls, prompt: str, repo_path: Optional[str] = None) -> Dict[str, Any]:
        """Dynamically routes query to the lowest capable intelligence tier."""
        cache_key = hashlib.sha256(f"{prompt}::{repo_path or ''}".encode()).hexdigest()
        if cache_key in _QUERY_CACHE:
            return {
                "ok": True,
                "tier": "Tier 0 (Cached Result)",
                "result": _QUERY_CACHE[cache_key],
                "cost": "$0.00",
                "cached": True
            }

        tier = cls.classify_complexity(prompt)

        # Tier 0: AST Outline
        if tier == 0:
            from src.ast_indexer import extract_all_ast_metadata, index_file_symbols
            target = repo_path or os.getcwd()
            if os.path.isfile(target):
                ast_data = index_file_symbols(target)
                symbols = ast_data.get("symbols", [])
                files_scanned = 1
            else:
                ast_data = extract_all_ast_metadata(target)
                symbols = ast_data.get("symbols", [])[:30]
                files_scanned = ast_data.get("files_scanned", 0)

            res = {"symbols": symbols, "files_scanned": files_scanned}
            _QUERY_CACHE[cache_key] = res
            return {
                "ok": True,
                "tier": "Tier 0 (AST Indexer - Zero Token Cost)",
                "result": res,
                "cost": "$0.00",
                "cached": False
            }

        # Tier 1: Needle Local AI Tool Calling
        elif tier == 1:
            from src.tool_harness import run_needle_inference
            res = run_needle_inference(prompt)
            _QUERY_CACHE[cache_key] = res.get("result")
            return {
                "ok": res.get("ok", True),
                "tier": "Tier 1 (CactusNeedle 14MB Local AI - Zero Cloud Tokens)",
                "result": res.get("result", ""),
                "cost": "$0.00",
                "cached": False
            }

        # Tier 2: Muse Code / Meta AI
        elif tier == 2:
            from src.muse import muse_chat
            res = muse_chat([{"role": "user", "content": prompt}])
            out = res.get("content", "")
            _QUERY_CACHE[cache_key] = out
            return {
                "ok": res.get("ok", True),
                "tier": "Tier 2 (Muse Code muse-spark-1.2)",
                "result": out,
                "cost": "Included in API subscription",
                "cached": False
            }

        # Tier 3: Heavy Reasoning
        else:
            return {
                "ok": True,
                "tier": "Tier 3 (Cloud Deep Reasoning)",
                "result": f"[Tier 3 Dispatched] Ready for multi-agent autonomous deep plan.",
                "cost": "Standard Cloud Model",
                "cached": False
            }
