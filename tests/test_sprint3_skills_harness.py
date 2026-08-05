"""Unit & Integration tests for Sprint 3 (SkillRegistry, AgentHarness, TrainingInterface, ReflectionEngine, RemoteController)."""

import pytest
from core.skill_registry import SkillRegistry
from core.agent_harness import AgentHarness
from core.training_interface import TrainingInterface
from core.reflection_engine import ReflectionEngine
from core.remote_controller import RemoteController

def test_skill_registry_progressive_disclosure(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    skill_file = skills_dir / "test_skill.md"
    skill_file.write_text("# test_skill\n## Description\nTest skill description.\n## Instructions\nFull instructions here.", encoding="utf-8")

    registry = SkillRegistry(str(skills_dir))
    context = registry.get_progressive_context()
    assert len(context) == 1
    assert context[0]["name"] == "test_skill"
    assert context[0]["description"] == "Test skill description."

    full = registry.get_full_skill("test_skill")
    assert full is not None
    assert "Full instructions here." in full["content"]

def test_agent_harness_session():
    registry = SkillRegistry()
    harness = AgentHarness(registry)
    session = harness.create_session("sess_123", "shadowcoder")
    assert session["session_id"] == "sess_123"

    trace = harness.log_execution_trace("sess_123", "shell_exec", {"cmd": "dir"}, success=True)
    assert trace["action"] == "shell_exec"
    assert len(session["trace_log"]) == 1

def test_training_interface():
    registry = SkillRegistry()
    harness = AgentHarness(registry)
    training = TrainingInterface(harness)

    sess = training.start_teach_session("teach_1", "Build automated backup script")
    assert sess["status"] == "recording"

    step = training.record_step("teach_1", "shell_exec", "python backup.py", "success")
    assert step["step_index"] == 1

    completed = training.stop_teach_session("teach_1")
    assert completed["status"] == "completed"

def test_reflection_engine():
    registry = SkillRegistry()
    harness = AgentHarness(registry)
    engine = ReflectionEngine(harness)

    traces = [
        {"action": "web_search", "success": True},
        {"action": "shell_exec", "success": False},
        {"action": "shell_exec", "success": False},
    ]

    report = engine.run_daily_reflection(traces)
    assert report["total_traces"] == 3
    assert report["total_failures"] == 2
    assert len(report["proposals"]) == 1
    assert report["proposals"][0]["action"] == "shell_exec"

def test_remote_controller():
    controller = RemoteController()
    status = controller.get_system_status()
    assert "status" in status
    assert status["status"] == "online"

    exec_res = controller.execute_pc_command("echo hello")
    assert exec_res["exit_code"] == 0
    assert "hello" in exec_res["stdout"].lower()
