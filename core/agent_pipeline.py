"""
C95 — Agent Pipeline & Orchestrator (Sprint 7B)
Chains multiple agents/callables in sequence with Task Routing (C55),
LangGraph research (C56), AutoGen coding (C57), and CrewAI scheduled monitoring (C58).
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Dict, List

from src.constants import DATA_DIR
from src.memory import MemoryManager

logger = logging.getLogger(__name__)

# Active pipeline tasks in-memory tracker (C59)
active_pipeline_tasks: Dict[str, Dict[str, Any]] = {}

@dataclass
class StepResult:
    step_name: str
    output: Any
    success: bool
    error: Optional[str] = None
    elapsed: float = 0.0


@dataclass
class PipelineResult:
    steps: list[StepResult] = field(default_factory=list)
    final_output: Any = None
    success: bool = True

    def last(self) -> Optional[StepResult]:
        return self.steps[-1] if self.steps else None

    def failed_steps(self) -> list[StepResult]:
        return [s for s in self.steps if not s.success]


StepCallable = Callable[[Any], Any]


@dataclass
class PipelineStep:
    name: str
    fn: StepCallable
    condition: Optional[Callable[[Any], bool]] = None
    on_error: str = "raise"  # 'raise' | 'skip' | 'stop'


class AgentPipeline:
    """Sequential pipeline of steps."""

    def __init__(self, name: str = "pipeline", task_id: Optional[str] = None):
        self.name = name
        self.task_id = task_id or str(uuid.uuid4())
        self._steps: list[PipelineStep] = []
        if self.task_id not in active_pipeline_tasks:
            active_pipeline_tasks[self.task_id] = {
                "id": self.task_id,
                "name": name,
                "status": "todo",
                "current_step": "",
                "steps": [],
                "created_at": time.time(),
                "updated_at": time.time()
            }

    def step(
        self,
        name: str,
        fn: StepCallable,
        condition: Optional[Callable[[Any], bool]] = None,
        on_error: str = "raise",
    ) -> "AgentPipeline":
        self._steps.append(PipelineStep(name=name, fn=fn, condition=condition, on_error=on_error))
        active_pipeline_tasks[self.task_id]["steps"].append({
            "name": name,
            "status": "pending"
        })
        return self

    def run(self, initial_input: Any = None) -> PipelineResult:
        result = PipelineResult()
        current = initial_input
        task_info = active_pipeline_tasks[self.task_id]
        task_info["status"] = "in_progress"
        task_info["updated_at"] = time.time()
        
        for idx, step in enumerate(self._steps):
            task_info["current_step"] = step.name
            task_info["steps"][idx]["status"] = "running"
            task_info["updated_at"] = time.time()
            
            if step.condition and not step.condition(current):
                logger.debug("[%s] Skipping step '%s' (condition=False)", self.name, step.name)
                task_info["steps"][idx]["status"] = "skipped"
                continue
                
            start = time.time()
            try:
                output = step.fn(current)
                if hasattr(output, "output"):
                    output = output.output
                elapsed = time.time() - start
                step_result = StepResult(step_name=step.name, output=output, success=True, elapsed=elapsed)
                result.steps.append(step_result)
                current = output
                task_info["steps"][idx]["status"] = "completed"
            except Exception as e:
                elapsed = time.time() - start
                step_result = StepResult(step_name=step.name, output=None, success=False, error=str(e), elapsed=elapsed)
                result.steps.append(step_result)
                result.success = False
                task_info["steps"][idx]["status"] = "failed"
                task_info["status"] = "failed"
                task_info["updated_at"] = time.time()
                logger.error("[%s] Step '%s' failed: %s", self.name, step.name, e)
                if step.on_error == "raise":
                    raise
                elif step.on_error == "stop":
                    break
                    
        if result.success:
            task_info["status"] = "done"
        task_info["updated_at"] = time.time()
        result.final_output = current
        return result

    async def arun(self, initial_input: Any = None) -> PipelineResult:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.run(initial_input))


# --- Task Router (C55) ---
class TaskRouter:
    """Classifies user queries and routes them to appropriate multi-agent pipelines (C55)."""

    @staticmethod
    def route(query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["find", "search", "read", "research", "summarize", "web", "lookup", "gather"]):
            return "research"
        elif any(w in q for w in ["code", "write", "test", "deploy", "build", "script", "program", "develop"]):
            return "coding"
        else:
            return "scheduled"


# --- LangGraph Research Pipeline (C56) ---
class LangGraphResearchPipeline:
    """Simulates LangGraph research steps (C56): query -> search -> read -> summarize -> memory_write -> report."""

    def __init__(self, query: str, owner: str = "admin", task_id: Optional[str] = None):
        self.query = query
        self.owner = owner
        self.pipeline = AgentPipeline("LangGraph Research Pipeline", task_id=task_id)
        
        # Build steps
        self.pipeline.step("search", self.step_search)
        self.pipeline.step("read", self.step_read)
        self.pipeline.step("summarize", self.step_summarize)
        self.pipeline.step("memory_write", self.step_memory_write)
        self.pipeline.step("report", self.step_report)

    def step_search(self, input_data: Any) -> Any:
        # Step 1: Query 5-tier memory for existing cool/warm contexts (C60)
        logger.info(f"LangGraph research pipeline [search]: query = {self.query}")
        return {"query": self.query, "search_results": f"Indexed results for query '{self.query}'"}

    def step_read(self, data: Any) -> Any:
        logger.info("LangGraph research pipeline [read]")
        data["read_content"] = f"Detailed context read from source page of {data['query']}"
        return data

    def step_summarize(self, data: Any) -> Any:
        logger.info("LangGraph research pipeline [summarize]")
        data["summary"] = f"Executive summary of research: {data['read_content'][:100]}..."
        return data

    def step_memory_write(self, data: Any) -> Any:
        logger.info("LangGraph research pipeline [memory_write] (C60)")
        mgr = MemoryManager(DATA_DIR)
        entry = mgr.add_entry(
            text=f"Research context for {data['query']}: {data['summary']}",
            source="langgraph_pipeline",
            category="project",
            owner=self.owner
        )
        # Write to cool tier
        entry["tier"] = "cool"
        all_mem = mgr.load_all()
        all_mem.append(entry)
        mgr.save(all_mem)
        data["memory_entry_id"] = entry["id"]
        return data

    def step_report(self, data: Any) -> Any:
        logger.info("LangGraph research pipeline [report]")
        return f"# Research Report: {data['query']}\n\n{data['summary']}\n\n*Saved to Memory Tier: Cool ({data['memory_entry_id'][:8]})*"

    async def execute(self) -> PipelineResult:
        return await self.pipeline.arun(self.query)


# --- AutoGen Coding Pipeline (C57) ---
class AutoGenCodingPipeline:
    """Simulates AutoGen coding steps (C57): planner -> coder -> tester -> reviewer -> deployer."""

    def __init__(self, request: str, owner: str = "admin", task_id: Optional[str] = None):
        self.request = request
        self.owner = owner
        self.pipeline = AgentPipeline("AutoGen Coding Pipeline", task_id=task_id)
        
        # Build steps
        self.pipeline.step("planner", self.step_planner)
        self.pipeline.step("coder", self.step_coder)
        self.pipeline.step("tester", self.step_tester)
        self.pipeline.step("reviewer", self.step_reviewer)
        self.pipeline.step("deployer", self.step_deployer)

    def step_planner(self, input_data: Any) -> Any:
        logger.info("AutoGen coding pipeline [planner]")
        return {"plan": f"Plan for task: {self.request}"}

    def step_coder(self, data: Any) -> Any:
        logger.info("AutoGen coding pipeline [coder]")
        data["code"] = "def solution():\n    return 'ShadowRealm V2.0 Solution'"
        return data

    def step_tester(self, data: Any) -> Any:
        logger.info("AutoGen coding pipeline [tester] (C61)")
        # Simulates running code in OpenHands sandbox environment
        data["test_results"] = "All 3 unit tests passed on sandbox environment (OpenHands run)"
        return data

    def step_reviewer(self, data: Any) -> Any:
        logger.info("AutoGen coding pipeline [reviewer]")
        data["review"] = "Approved: Clean code syntax, passes all tests."
        return data

    def step_deployer(self, data: Any) -> Any:
        logger.info("AutoGen coding pipeline [deployer]")
        # Write to warm memory (project context)
        mgr = MemoryManager(DATA_DIR)
        entry = mgr.add_entry(
            text=f"AutoGen Coding deploy plan: {data['plan']}",
            source="autogen_pipeline",
            category="project",
            owner=self.owner
        )
        entry["tier"] = "warm"
        all_mem = mgr.load_all()
        all_mem.append(entry)
        mgr.save(all_mem)
        return f"Successfully generated solution code:\n\n```python\n{data['code']}\n```\n\nStatus: {data['test_results']}"

    async def execute(self) -> PipelineResult:
        return await self.pipeline.arun(self.request)


# --- CrewAI Scheduled Pipeline (C58) ---
class CrewAIScheduledPipeline:
    """Simulates CrewAI scheduled steps (C58): watcher -> analyzer -> notifier."""

    def __init__(self, target: str, owner: str = "admin", task_id: Optional[str] = None):
        self.target = target
        self.owner = owner
        self.pipeline = AgentPipeline("CrewAI Scheduled Pipeline", task_id=task_id)
        
        # Build steps
        self.pipeline.step("watcher", self.step_watcher)
        self.pipeline.step("analyzer", self.step_analyzer)
        self.pipeline.step("notifier", self.step_notifier)

    def step_watcher(self, input_data: Any) -> Any:
        logger.info("CrewAI scheduled pipeline [watcher]")
        return {"target": self.target, "logs": f"Checking system logs for {self.target}..."}

    def step_analyzer(self, data: Any) -> Any:
        logger.info("CrewAI scheduled pipeline [analyzer]")
        data["status"] = "healthy"
        return data

    def step_notifier(self, data: Any) -> Any:
        logger.info("CrewAI scheduled pipeline [notifier]")
        # Log to episodic memory
        mgr = MemoryManager(DATA_DIR)
        entry = mgr.add_entry(
            text=f"CrewAI watchdog check: {data['target']} is {data['status']}.",
            source="crewai_pipeline",
            category="task",
            owner=self.owner
        )
        entry["tier"] = "episodic"
        all_mem = mgr.load_all()
        all_mem.append(entry)
        mgr.save(all_mem)
        return f"CrewAI scheduled watchdog checked {data['target']}: Status {data['status']}."

    async def execute(self) -> PipelineResult:
        return await self.pipeline.arun(self.target)
