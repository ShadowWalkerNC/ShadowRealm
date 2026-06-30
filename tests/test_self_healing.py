import pytest
from routes.healing_routes import log_skill_trace, proposals_queue
from core.database import get_db_session, SkillTrace

def test_log_skill_trace_success():
    proposals_queue.clear()
    
    # Log a successful run trace
    log_skill_trace(
        name="test_skill",
        agent="ShadowCoder",
        prompt="hello coder",
        response="ready to write",
        tokens=150,
        duration=1.2,
        error_type=None,
        owner="admin"
    )
    
    with get_db_session() as db:
        trace = db.query(SkillTrace).filter(SkillTrace.name == "test_skill").first()
        assert trace is not None
        assert trace.agent == "ShadowCoder"
        assert trace.error_type is None
        
    assert len(proposals_queue) == 0

def test_log_skill_trace_failure_triggers_autoheal():
    proposals_queue.clear()
    
    # Log a failed run trace
    log_skill_trace(
        name="failing_skill",
        agent="ShadowOps",
        prompt="run check",
        response="command not found",
        tokens=180,
        duration=2.5,
        error_type="ShellExecutionError",
        owner="admin"
    )
    
    with get_db_session() as db:
        trace = db.query(SkillTrace).filter(SkillTrace.name == "failing_skill").first()
        assert trace is not None
        assert trace.error_type == "ShellExecutionError"
        
    assert len(proposals_queue) == 1
    proposal = list(proposals_queue.values())[0]
    assert proposal["skill_name"] == "failing_skill"
    assert proposal["error_type"] == "ShellExecutionError"
    assert proposal["status"] == "pending"
