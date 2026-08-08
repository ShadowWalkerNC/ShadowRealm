"""Tests for C118 ModelRouter + routing log + self-test gate + pipelines."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from shadowrealm.model_router import (
    PATH_LOCAL_FIRST,
    PATH_LOCAL_ONLY,
    PATH_LOCAL_PLAN_THEN_CLOUD,
    ModelRouter,
    build_default_router,
)
from shadowrealm.routing_log import get_decision, list_decisions, log_decision
from shadowrealm.self_test_gate import looks_like_coding_task, run_self_tests
from shadowrealm.workflow_pipelines import (
    PIPELINE_ANALYZE,
    PIPELINE_REVIEW,
    WorkflowPipelineEngine,
    list_pipeline_defs,
)


@pytest.fixture
def tmp_data(tmp_path, monkeypatch):
    monkeypatch.setenv("ODYSSEUS_DATA_DIR", str(tmp_path))
    # Force constants.DATA_DIR if already imported
    import src.constants as constants
    monkeypatch.setattr(constants, "DATA_DIR", str(tmp_path))
    return tmp_path


def test_sensitive_forces_local():
    r = ModelRouter(cloud_available=True, openrouter_configured=True)
    d = r.route("Please review this proprietary customer database dump and API key vault.yml")
    assert d.sensitivity == "force_local"
    assert d.path == PATH_LOCAL_ONLY
    assert d.cloud_allowed is False


def test_large_scope_plans_then_cloud():
    r = ModelRouter(cloud_available=True, openrouter_configured=True)
    d = r.route(
        "Redesign the entire architecture of this cross-codebase monorepo "
        "and migrate the whole multi-service platform."
    )
    assert d.scope == "large"
    assert d.path == PATH_LOCAL_PLAN_THEN_CLOUD
    assert d.cloud_allowed is True
    assert d.require_local_first_pass is True


def test_small_bug_is_local_first():
    r = ModelRouter(cloud_available=True)
    d = r.route("Fix the typo in this single file function and add a unit test.")
    assert d.scope in {"small", "contained"}
    assert d.path == PATH_LOCAL_FIRST


def test_confidence_and_escalation_package():
    r = ModelRouter(cloud_available=True)
    d = r.route("Implement a small helper")
    assessment = r.assess_confidence(
        "Implement a small helper",
        "I'm not sure how to finish this. Unresolved: edge case for empty input",
    )
    assert assessment.confident is False
    pkg = r.package_escalation(
        d,
        task="Implement a small helper",
        local_result="partial work",
        assessment=assessment,
    )
    prompt = pkg.to_prompt()
    assert "Unresolved" in prompt or "unresolved" in prompt.lower()
    assert "Implement a small helper" in prompt


def test_routing_log_persists(tmp_data):
    r = build_default_router()
    d = r.route("explain this function", session_id="sess-1")
    log_decision(d)
    items = list_decisions(limit=10, session_id="sess-1")
    assert items
    assert items[0]["decision_id"] == d.decision_id
    assert get_decision(d.decision_id)["path"] == d.path


def test_self_test_compile(tmp_data):
    py = tmp_data / "mod.py"
    py.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    result = run_self_tests(str(tmp_data), touched_files=[str(py)])
    assert result.ran is True
    assert result.ok is True
    assert result.method in {"compile", "generated", "pytest", "unittest"}


def test_self_test_syntax_error(tmp_data):
    py = tmp_data / "bad.py"
    py.write_text("def broken(\n", encoding="utf-8")
    result = run_self_tests(str(tmp_data), touched_files=[str(py)])
    assert result.ran is True
    assert result.ok is False
    assert result.handoff_blocker()


def test_looks_like_coding_task():
    assert looks_like_coding_task("fix the bug in foo.py")
    assert looks_like_coding_task("please help", tools_used=["write_file"])
    assert not looks_like_coding_task("what's the weather?")


def test_analyze_project_pipeline(tmp_data):
    (tmp_data / "src").mkdir()
    (tmp_data / "src" / "a.py").write_text("# TODO: clean this up\nx=1\n", encoding="utf-8")
    engine = WorkflowPipelineEngine()
    run = engine.start(PIPELINE_ANALYZE, {"project_dir": str(tmp_data)})
    assert run.status == "completed"
    assert run.result and "report" in run.result
    assert "TODO" in run.result["report"] or any("TODO" in i for i in run.result.get("issues", []))


def test_review_before_ship_pipeline(tmp_data):
    (tmp_data / "ok.py").write_text("print('hi')\n", encoding="utf-8")
    engine = WorkflowPipelineEngine()
    run = engine.start(
        PIPELINE_REVIEW,
        {"project_dir": str(tmp_data), "diff_summary": "Added ok.py helper"},
    )
    assert run.status == "completed"
    assert run.result
    assert "handoff" in run.result


def test_pipeline_defs_include_three_named():
    names = {p["name"] for p in list_pipeline_defs()}
    assert names == {"analyze-project", "fix-and-verify", "review-before-ship"}


def test_openrouter_escalate_skips_without_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    from shadowrealm.openrouter import escalate_unresolved, openrouter_configured

    assert openrouter_configured() is False
    result = escalate_unresolved(escalation_prompt="finish the unresolved part")
    assert result["ok"] is False
    assert result["skipped"] is True


def test_hooks_apply_routing_force_local(tmp_data):
    from types import SimpleNamespace
    from shadowrealm.hooks import apply_model_routing, chat_routing_summary

    sess = SimpleNamespace(endpoint_url="", model="", headers={})
    rec = apply_model_routing(
        "Review proprietary customer PII and vault.yml secrets",
        sess,
        session_id="s1",
        owner="admin",
    )
    assert rec is not None
    assert rec["path"] == "local_only"
    summary = chat_routing_summary(rec)
    assert summary["sensitivity"] == "force_local"
