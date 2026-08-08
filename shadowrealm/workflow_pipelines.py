"""
Phase 4 — Named, resumable workflow pipelines.

Pipelines:
  - analyze-project   — local-only project scan + report
  - fix-and-verify    — fix → test → iterate (local N times, then cloud flag)
  - review-before-ship — tests + change summary + uncertainty flags (handoff)

Each run persists step status under DATA_DIR/workflow_runs/ so a paused
run can resume without redoing finished steps.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from shadowrealm.model_router import (
    PATH_LOCAL_ONLY,
    ModelRouter,
    build_default_router,
)
from shadowrealm.routing_log import log_decision
from shadowrealm.self_test_gate import run_self_tests

logger = logging.getLogger(__name__)

PIPELINE_ANALYZE = "analyze-project"
PIPELINE_FIX = "fix-and-verify"
PIPELINE_REVIEW = "review-before-ship"

STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_WAITING = "waiting_for_input"
STATUS_SKIPPED = "skipped"


@dataclass
class StepState:
    name: str
    status: str = STATUS_PENDING
    output: Any = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineRun:
    run_id: str
    pipeline: str
    status: str
    params: Dict[str, Any]
    steps: List[StepState]
    created_at: float
    updated_at: float
    result: Any = None
    routing_decision_id: Optional[str] = None
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "pipeline": self.pipeline,
            "status": self.status,
            "params": self.params,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": self.result,
            "routing_decision_id": self.routing_decision_id,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineRun":
        steps = [StepState(**s) for s in data.get("steps") or []]
        return cls(
            run_id=data["run_id"],
            pipeline=data["pipeline"],
            status=data.get("status", STATUS_PENDING),
            params=data.get("params") or {},
            steps=steps,
            created_at=float(data.get("created_at") or time.time()),
            updated_at=float(data.get("updated_at") or time.time()),
            result=data.get("result"),
            routing_decision_id=data.get("routing_decision_id"),
            message=data.get("message") or "",
        )


def _runs_dir() -> Path:
    try:
        from src.constants import DATA_DIR
        base = Path(DATA_DIR)
    except Exception:
        base = Path(os.getenv("ODYSSEUS_DATA_DIR", "data"))
    d = base / "workflow_runs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _run_path(run_id: str) -> Path:
    return _runs_dir() / f"{run_id}.json"


def save_run(run: PipelineRun) -> None:
    run.updated_at = time.time()
    path = _run_path(run.run_id)
    path.write_text(json.dumps(run.to_dict(), indent=2, default=str), encoding="utf-8")


def load_run(run_id: str) -> Optional[PipelineRun]:
    path = _run_path(run_id)
    if not path.exists():
        return None
    try:
        return PipelineRun.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception as e:
        logger.error("Failed to load workflow run %s: %s", run_id, e)
        return None


def list_runs(*, pipeline: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    items = []
    for path in sorted(_runs_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if pipeline and data.get("pipeline") != pipeline:
            continue
        items.append(data)
        if len(items) >= limit:
            break
    return items


def list_pipeline_defs() -> List[Dict[str, Any]]:
    return [
        {
            "name": PIPELINE_ANALYZE,
            "description": "Scan a project directory, summarize structure, flag issues (local-only).",
            "params": ["project_dir"],
            "default_local_only": True,
        },
        {
            "name": PIPELINE_FIX,
            "description": "Attempt a fix locally, run tests, iterate up to N times, then flag cloud.",
            "params": ["project_dir", "bug_report", "max_attempts"],
            "default_local_only": True,
        },
        {
            "name": PIPELINE_REVIEW,
            "description": "Final handoff review: run tests, summarize changes, flag uncertainty.",
            "params": ["project_dir", "diff_summary"],
            "default_local_only": True,
        },
    ]


class WorkflowPipelineEngine:
    """Execute / resume named pipelines with step checkpoints."""

    def __init__(self, router: Optional[ModelRouter] = None):
        self.router = router or build_default_router()

    def start(self, pipeline: str, params: Optional[Dict[str, Any]] = None) -> PipelineRun:
        pipeline = (pipeline or "").strip()
        if pipeline not in {PIPELINE_ANALYZE, PIPELINE_FIX, PIPELINE_REVIEW}:
            raise ValueError(f"Unknown pipeline: {pipeline}")
        params = dict(params or {})
        steps = _steps_for(pipeline)
        run = PipelineRun(
            run_id=uuid.uuid4().hex[:12],
            pipeline=pipeline,
            status=STATUS_RUNNING,
            params=params,
            steps=[StepState(name=s) for s in steps],
            created_at=time.time(),
            updated_at=time.time(),
        )
        # Routing decision up front
        task = _task_text(pipeline, params)
        decision = self.router.route(
            task,
            metadata={"pipeline": pipeline, "run_id": run.run_id, "local_only_default": True},
        )
        # These pipelines are local-only by default
        if pipeline in {PIPELINE_ANALYZE, PIPELINE_FIX, PIPELINE_REVIEW}:
            decision.path = PATH_LOCAL_ONLY
            decision.cloud_allowed = False
            decision.reason = (
                f"Pipeline `{pipeline}` is local-only by default. " + decision.reason
            )
        log_decision(decision, extra={"pipeline": pipeline, "run_id": run.run_id})
        run.routing_decision_id = decision.decision_id
        save_run(run)
        return self.resume(run.run_id)

    def resume(self, run_id: str, *, user_input: Optional[Dict[str, Any]] = None) -> PipelineRun:
        run = load_run(run_id)
        if not run:
            raise FileNotFoundError(f"workflow run not found: {run_id}")
        if user_input:
            run.params.update(user_input)
        if run.status in {STATUS_COMPLETED, STATUS_FAILED}:
            return run

        run.status = STATUS_RUNNING
        handlers = {
            PIPELINE_ANALYZE: self._run_analyze,
            PIPELINE_FIX: self._run_fix,
            PIPELINE_REVIEW: self._run_review,
        }
        handler = handlers[run.pipeline]
        try:
            handler(run)
        except _WaitForInput as w:
            run.status = STATUS_WAITING
            run.message = str(w)
            save_run(run)
            return run
        except Exception as e:
            run.status = STATUS_FAILED
            run.message = str(e)
            save_run(run)
            logger.exception("pipeline %s failed: %s", run.pipeline, e)
            return run

        if all(s.status in {STATUS_COMPLETED, STATUS_SKIPPED} for s in run.steps):
            run.status = STATUS_COMPLETED
            run.message = run.message or "completed"
        save_run(run)
        return run

    # ── Pipeline implementations ────────────────────────────────────

    def _run_analyze(self, run: PipelineRun) -> None:
        project = run.params.get("project_dir") or run.params.get("path")
        if not project:
            raise _WaitForInput("Need project_dir to analyze.")

        def scan(_):
            root = Path(project).expanduser().resolve()
            if not root.is_dir():
                raise FileNotFoundError(f"not a directory: {root}")
            return _scan_project(root)

        def flag_issues(scan_out):
            return _flag_issues(scan_out)

        def report(payload):
            scan_out, issues = payload["scan"], payload["issues"]
            lines = [
                f"# analyze-project report — {scan_out['root']}",
                "",
                f"Files: {scan_out['file_count']}  |  Dirs: {scan_out['dir_count']}",
                "",
                "## Top-level structure",
                *[f"- {e}" for e in scan_out["top_level"][:40]],
                "",
                "## Languages / extensions",
                *[f"- {k}: {v}" for k, v in sorted(scan_out["extensions"].items(), key=lambda kv: -kv[1])[:20]],
                "",
                "## Issues / TODOs",
            ]
            if not issues:
                lines.append("- (none flagged)")
            else:
                for issue in issues[:50]:
                    lines.append(f"- {issue}")
            text = "\n".join(lines)
            run.result = {"report": text, "scan": scan_out, "issues": issues}
            return text

        scan_out = self._step(run, "scan_structure", scan)
        issues = self._step(run, "flag_issues", lambda _: flag_issues(scan_out))
        self._step(run, "write_report", lambda _: report({"scan": scan_out, "issues": issues}))

    def _run_fix(self, run: PipelineRun) -> None:
        project = run.params.get("project_dir") or run.params.get("path")
        bug = run.params.get("bug_report") or run.params.get("failing_test")
        if not project:
            raise _WaitForInput("Need project_dir.")
        if not bug:
            raise _WaitForInput("Need bug_report or failing_test description.")
        max_attempts = int(run.params.get("max_attempts") or 3)

        def analyze(_):
            return {
                "bug_report": bug,
                "project_dir": str(Path(project).expanduser().resolve()),
                "plan": (
                    "1) Reproduce from bug report / failing test\n"
                    "2) Attempt minimal local fix\n"
                    "3) Run tests\n"
                    f"4) Iterate up to {max_attempts} local attempts, then flag cloud"
                ),
            }

        analysis = self._step(run, "analyze_failure", analyze)

        # attempt_fix is a placeholder the caller/agent fills; we record intent
        def attempt(_):
            attempts = list(run.params.get("attempts") or [])
            attempt_n = len(attempts) + 1
            note = {
                "attempt": attempt_n,
                "max_attempts": max_attempts,
                "note": (
                    "Local fix attempt recorded. Agent/tools should apply the patch "
                    "before verify_tests. Set params.fix_applied=true when done."
                ),
            }
            attempts.append(note)
            run.params["attempts"] = attempts
            if not run.params.get("fix_applied") and attempt_n <= max_attempts:
                # Allow resume after human/agent applies fix
                raise _WaitForInput(
                    f"Apply local fix for attempt {attempt_n}/{max_attempts}, "
                    "set fix_applied=true, then resume."
                )
            return {"attempts": attempts, "analysis": analysis}

        self._step(run, "attempt_fix", attempt)

        def verify(_):
            result = run_self_tests(project)
            run.params["last_test"] = result.to_dict()
            return result.to_dict()

        test_result = self._step(run, "verify_tests", verify)

        def decide(tr):
            if tr.get("ok"):
                run.result = {"fixed": True, "test": tr, "escalated": False}
                return run.result
            attempts = run.params.get("attempts") or []
            if len(attempts) < max_attempts:
                # Reset fix_applied so next resume does another attempt
                run.params["fix_applied"] = False
                # Mark attempt_fix pending again
                for s in run.steps:
                    if s.name == "attempt_fix":
                        s.status = STATUS_PENDING
                        s.output = None
                raise _WaitForInput(
                    f"Tests still failing after attempt {len(attempts)}/{max_attempts}. "
                    "Apply another local fix and resume."
                )
            run.result = {
                "fixed": False,
                "test": tr,
                "escalated": True,
                "escalation": (
                    "Local attempts exhausted. Flagging for cloud escalation "
                    "(OpenRouter) with local attempt context."
                ),
                "attempts": attempts,
            }
            return run.result

        self._step(run, "escalate_or_done", lambda _: decide(test_result))

    def _run_review(self, run: PipelineRun) -> None:
        project = run.params.get("project_dir") or run.params.get("path") or "."
        diff_summary = run.params.get("diff_summary") or run.params.get("changes") or ""

        def run_tests(_):
            return run_self_tests(project).to_dict()

        def summarize(_):
            summary = diff_summary.strip() or _git_diff_stat(project)
            return {"changes": summary}

        def flag_uncertain(payload):
            tests, changes = payload["tests"], payload["changes"]
            uncertain = []
            if not tests.get("ok"):
                uncertain.append("Tests did not pass or could not run.")
            text = (changes.get("changes") or "").lower()
            for needle in ("todo", "fixme", "xxx", "hack", "temporary"):
                if needle in text:
                    uncertain.append(f"Change summary mentions '{needle}'.")
            report = {
                "tests": tests,
                "changes": changes,
                "uncertain": uncertain,
                "handoff": (
                    "Ready for human review — not an auto-merge. "
                    + ("Uncertainties listed above." if uncertain else "No uncertainties auto-flagged.")
                ),
            }
            run.result = report
            return report

        tests = self._step(run, "run_tests", run_tests)
        changes = self._step(run, "summarize_changes", summarize)
        self._step(run, "flag_uncertain", lambda _: flag_uncertain({"tests": tests, "changes": changes}))

    # ── Step runner with resume ─────────────────────────────────────

    def _step(self, run: PipelineRun, name: str, fn: Callable[[Any], Any]) -> Any:
        step = next((s for s in run.steps if s.name == name), None)
        if step is None:
            step = StepState(name=name)
            run.steps.append(step)
        if step.status == STATUS_COMPLETED:
            return step.output
        step.status = STATUS_RUNNING
        step.started_at = time.time()
        save_run(run)
        try:
            out = fn(None)
            step.output = out
            step.status = STATUS_COMPLETED
            step.finished_at = time.time()
            step.error = None
            save_run(run)
            return out
        except _WaitForInput:
            step.status = STATUS_WAITING
            step.finished_at = time.time()
            save_run(run)
            raise
        except Exception as e:
            step.status = STATUS_FAILED
            step.error = str(e)
            step.finished_at = time.time()
            save_run(run)
            raise


class _WaitForInput(Exception):
    """Signal that the pipeline needs user/agent input before continuing."""


def _steps_for(pipeline: str) -> List[str]:
    return {
        PIPELINE_ANALYZE: ["scan_structure", "flag_issues", "write_report"],
        PIPELINE_FIX: ["analyze_failure", "attempt_fix", "verify_tests", "escalate_or_done"],
        PIPELINE_REVIEW: ["run_tests", "summarize_changes", "flag_uncertain"],
    }[pipeline]


def _task_text(pipeline: str, params: Dict[str, Any]) -> str:
    if pipeline == PIPELINE_ANALYZE:
        return f"analyze-project: scan {params.get('project_dir') or params.get('path')}"
    if pipeline == PIPELINE_FIX:
        return f"fix-and-verify: {params.get('bug_report') or params.get('failing_test')}"
    return f"review-before-ship: {params.get('diff_summary') or 'review changes'}"


def _scan_project(root: Path) -> Dict[str, Any]:
    exts: Dict[str, int] = {}
    file_count = 0
    dir_count = 0
    top_level = sorted(p.name + ("/" if p.is_dir() else "") for p in root.iterdir() if not p.name.startswith("."))
    skip = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", ".tox"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        dir_count += len(dirnames)
        for fn in filenames:
            if fn.startswith("."):
                continue
            file_count += 1
            ext = Path(fn).suffix.lower() or "(none)"
            exts[ext] = exts.get(ext, 0) + 1
            if file_count > 20000:
                break
        if file_count > 20000:
            break
    return {
        "root": str(root),
        "top_level": top_level,
        "file_count": file_count,
        "dir_count": dir_count,
        "extensions": exts,
    }


def _flag_issues(scan_out: Dict[str, Any]) -> List[str]:
    root = Path(scan_out["root"])
    issues: List[str] = []
    todo_re = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")
    skip = {".git", "node_modules", "venv", ".venv", "__pycache__"}
    scanned = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        for fn in filenames:
            if not fn.endswith((".py", ".js", ".ts", ".tsx", ".md", ".sh")):
                continue
            path = Path(dirpath) / fn
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            scanned += 1
            for i, line in enumerate(text.splitlines(), 1):
                if todo_re.search(line):
                    rel = path.relative_to(root)
                    issues.append(f"{rel}:{i}: {line.strip()[:120]}")
                    if len(issues) >= 50:
                        return issues
            if scanned > 400:
                return issues
    # Pattern inconsistency: mixed tabs/spaces in Python
    py_tabs = 0
    py_spaces = 0
    for path in list(root.rglob("*.py"))[:80]:
        if any(p in path.parts for p in skip):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if "\t" in text:
            py_tabs += 1
        if re.search(r"^ {2,}", text, re.M):
            py_spaces += 1
    if py_tabs and py_spaces:
        issues.append(
            f"Inconsistent indentation: {py_tabs} Python files use tabs, "
            f"{py_spaces} use spaces."
        )
    return issues


def _git_diff_stat(project: str) -> str:
    try:
        import subprocess
        proc = subprocess.run(
            ["git", "diff", "--stat", "HEAD"],
            cwd=str(Path(project).expanduser()),
            capture_output=True,
            text=True,
            timeout=30,
        )
        out = (proc.stdout or "").strip()
        if out:
            return out
        proc2 = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(Path(project).expanduser()),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return (proc2.stdout or "").strip() or "(no git changes detected)"
    except Exception as e:
        return f"(git summary unavailable: {e})"
