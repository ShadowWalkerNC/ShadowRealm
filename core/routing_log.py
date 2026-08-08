"""Persistent, reviewable log of ModelRouter decisions.

Stored as JSONL under ``DATA_DIR/routing_decisions.jsonl`` so operators can
inspect every local-vs-cloud choice without a DB migration.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.model_router import RoutingDecision

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()


def _log_path() -> Path:
    try:
        from src.constants import DATA_DIR
        base = Path(DATA_DIR)
    except Exception:
        base = Path(os.getenv("ODYSSEUS_DATA_DIR", "data"))
    base.mkdir(parents=True, exist_ok=True)
    return base / "routing_decisions.jsonl"


def log_decision(
    decision: RoutingDecision,
    *,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Append one routing decision. Returns the written record."""
    record = decision.to_dict()
    record["logged_at"] = time.time()
    if extra:
        record["extra"] = extra
    path = _log_path()
    line = json.dumps(record, ensure_ascii=False, default=str)
    with _LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    logger.info(
        "routing log written id=%s path=%s file=%s",
        decision.decision_id,
        decision.path,
        path,
    )
    return record


def update_decision(
    decision_id: str,
    updates: Dict[str, Any],
) -> bool:
    """Rewrite the matching log line with merged updates (small files only)."""
    path = _log_path()
    if not path.exists() or not decision_id:
        return False
    with _LOCK:
        lines = path.read_text(encoding="utf-8").splitlines()
        out: List[str] = []
        found = False
        for line in lines:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                out.append(line)
                continue
            if obj.get("decision_id") == decision_id:
                obj.update(updates)
                obj["updated_at"] = time.time()
                out.append(json.dumps(obj, ensure_ascii=False, default=str))
                found = True
            else:
                out.append(line)
        if found:
            path.write_text("\n".join(out) + ("\n" if out else ""), encoding="utf-8")
        return found


def list_decisions(
    *,
    limit: int = 100,
    session_id: Optional[str] = None,
    path_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return newest-first decision records."""
    path = _log_path()
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with _LOCK:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    for line in raw_lines:
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        meta = obj.get("metadata") or {}
        if session_id and meta.get("session_id") != session_id:
            continue
        if path_filter and obj.get("path") != path_filter:
            continue
        records.append(obj)
    records.reverse()
    return records[: max(1, min(int(limit), 1000))]


def get_decision(decision_id: str) -> Optional[Dict[str, Any]]:
    if not decision_id:
        return None
    for rec in list_decisions(limit=1000):
        if rec.get("decision_id") == decision_id:
            return rec
    return None
