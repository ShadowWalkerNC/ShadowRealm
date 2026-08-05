"""TrainingInterface — trace capture and workflow recording for Teach Mode."""

import logging
from typing import Dict, Any, List, Optional
from core.agent_harness import AgentHarness

logger = logging.getLogger(__name__)

class TrainingInterface:
    """Manages Teach Mode interaction recording and crystallization into skills."""

    def __init__(self, harness: AgentHarness):
        self.harness = harness
        self.active_teach_sessions: Dict[str, Dict[str, Any]] = {}

    def start_teach_session(self, session_id: str, goal_description: str) -> Dict[str, Any]:
        """Start recording a human-guided workflow session."""
        teach_session = {
            "session_id": session_id,
            "goal": goal_description,
            "recorded_steps": [],
            "status": "recording",
        }
        self.active_teach_sessions[session_id] = teach_session
        logger.info(f"Started Teach Mode session '{session_id}' with goal: {goal_description}")
        return teach_session

    def record_step(self, session_id: str, step_action: str, input_data: Any, output_data: Any) -> Optional[Dict[str, Any]]:
        """Record an interactive step with annotation."""
        teach = self.active_teach_sessions.get(session_id)
        if not teach or teach["status"] != "recording":
            return None

        step = {
            "step_index": len(teach["recorded_steps"]) + 1,
            "action": step_action,
            "input": input_data,
            "output": output_data,
        }
        teach["recorded_steps"].append(step)
        return step

    def stop_teach_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Finalize teach session trace for skill crystallization."""
        teach = self.active_teach_sessions.get(session_id)
        if not teach:
            return None

        teach["status"] = "completed"
        return teach
