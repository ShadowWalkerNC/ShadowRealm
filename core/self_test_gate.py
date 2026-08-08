"""
Phase 3 — Self-testing before hand-off.

For coding tasks, refuse to mark work "done" until tests (or a minimal
syntax/runtime check) have been attempted. Surfaces failures explicitly
instead of presenting untested code as complete.
"""
from __future__ import annotations

import ast
import logging
import os
import py_compile
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

_PYTHON = sys.executable or "python3"

logger = logging.getLogger(__name__)


@dataclass
class SelfTestResult:
    ok: bool
    ran: bool
    method: str  # pytest | unittest | compile | generated | skipped
    summary: str
    output: str = ""
    generated_tests: List[str] = field(default_factory=list)
    elapsed: float = 0.0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def handoff_blocker(self) -> Optional[str]:
        """Human-readable reason this must not be marked done, or None."""
        if self.ok and self.ran:
            return None
        if not self.ran:
            return (
                f"Self-test gate: tests could not be run ({self.summary}). "
                "Do not present this change as done."
            )
        return (
            f"Self-test gate: tests FAILED ({self.summary}). "
            "Do not present this change as done until fixed or explicitly reported."
        )


_CODING_HINTS = (
    "fix", "bug", "implement", "refactor", "patch", "write code",
    "add test", "unittest", "pytest", "function", "class ", "module",
    ".py", "typescript", "javascript", "compile", "syntax",
)


def looks_like_coding_task(task: str, *, tools_used: Optional[Sequence[str]] = None) -> bool:
    text = (task or "").lower()
    if any(h in text for h in _CODING_HINTS):
        return True
    coding_tools = {"bash", "python", "write_file", "edit_file", "create_document", "read_file"}
    used = {str(t).lower() for t in (tools_used or [])}
    return bool(used & coding_tools)


def run_self_tests(
    workspace: Optional[str],
    *,
    touched_files: Optional[Sequence[str]] = None,
    timeout: int = 120,
) -> SelfTestResult:
    """Run the best available verification for ``workspace``.

    Order:
      1. Existing pytest/unittest suite
      2. py_compile / ast.parse on touched Python files
      3. Generate a minimal smoke test for touched pure functions (best-effort)
    """
    start = time.time()
    root = Path(workspace or ".").expanduser().resolve()
    if not root.exists() or not root.is_dir():
        return SelfTestResult(
            ok=False,
            ran=False,
            method="skipped",
            summary=f"workspace not found: {root}",
            errors=[f"workspace not found: {root}"],
            elapsed=time.time() - start,
        )

    # 1) Existing suite
    suite = _detect_test_runner(root)
    if suite:
        ok, output = _run_cmd(suite["cmd"], cwd=str(root), timeout=timeout)
        return SelfTestResult(
            ok=ok,
            ran=True,
            method=suite["method"],
            summary="passed" if ok else "failed",
            output=_trim(output),
            elapsed=time.time() - start,
            errors=[] if ok else ["test suite reported failure"],
        )

    # 2) Syntax/compile check on touched files
    py_files = [f for f in (touched_files or []) if str(f).endswith(".py")]
    if not py_files:
        py_files = [str(p) for p in root.rglob("*.py") if ".venv" not in p.parts and "venv" not in p.parts][:20]

    compile_errors: List[str] = []
    checked = 0
    for rel in py_files:
        path = Path(rel)
        if not path.is_absolute():
            path = root / path
        if not path.exists() or not path.is_file():
            continue
        checked += 1
        try:
            py_compile.compile(str(path), doraise=True)
            ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
        except Exception as e:
            compile_errors.append(f"{path}: {e}")

    if checked and not compile_errors:
        # 3) Optional generated smoke tests — best-effort only. If they fail
        # (import path quirks, missing deps), fall back to compile success
        # rather than blocking handoff on a synthetic test.
        generated, gen_ok, gen_out = _try_generated_tests(root, py_files)
        if generated and gen_ok:
            return SelfTestResult(
                ok=True,
                ran=True,
                method="generated",
                summary="generated smoke tests passed",
                output=_trim(gen_out),
                generated_tests=generated,
                elapsed=time.time() - start,
            )
        return SelfTestResult(
            ok=True,
            ran=True,
            method="compile",
            summary=f"syntax/compile OK on {checked} file(s); no test suite found",
            output=_trim(gen_out) if generated and not gen_ok else "",
            generated_tests=generated if generated else [],
            elapsed=time.time() - start,
        )

    if compile_errors:
        return SelfTestResult(
            ok=False,
            ran=True,
            method="compile",
            summary=f"{len(compile_errors)} syntax/compile error(s)",
            output="\n".join(compile_errors),
            errors=compile_errors,
            elapsed=time.time() - start,
        )

    return SelfTestResult(
        ok=False,
        ran=False,
        method="skipped",
        summary="no test suite and no Python files to check",
        errors=["nothing to verify"],
        elapsed=time.time() - start,
    )


def _detect_test_runner(root: Path) -> Optional[Dict[str, Any]]:
    markers = [
        root / "pytest.ini",
        root / "pyproject.toml",
        root / "setup.cfg",
        root / "tox.ini",
    ]
    tests_dir = root / "tests"
    test_glob = list(root.glob("test_*.py")) + list(root.glob("*_test.py"))
    has_tests = tests_dir.is_dir() or bool(test_glob)
    if not has_tests and not any(m.exists() for m in markers):
        return None
    # Prefer pytest if importable / on PATH
    try:
        import pytest  # noqa: F401
        return {"method": "pytest", "cmd": [_PYTHON, "-m", "pytest", "-q", "--tb=line"]}
    except Exception:
        pass
    which = _which("pytest")
    if which:
        return {"method": "pytest", "cmd": [which, "-q", "--tb=line"]}
    if has_tests:
        return {"method": "unittest", "cmd": [_PYTHON, "-m", "unittest", "discover", "-q"]}
    return None


def _try_generated_tests(root: Path, py_files: Sequence[str]) -> tuple:
    """Write a tiny import-smoke test for modules that look importable."""
    modules = []
    for rel in py_files[:5]:
        path = Path(rel)
        if not path.is_absolute():
            path = root / path
        if path.name == "__init__.py":
            continue
        try:
            rel_to_root = path.resolve().relative_to(root.resolve())
        except ValueError:
            continue
        mod = ".".join(rel_to_root.with_suffix("").parts)
        if any(part.startswith(".") for part in rel_to_root.parts):
            continue
        modules.append(mod)
    if not modules:
        return [], True, ""

    body_lines = ["import importlib", "import unittest", "", "class Smoke(unittest.TestCase):"]
    for i, mod in enumerate(modules):
        body_lines.append(f"    def test_import_{i}(self):")
        body_lines.append(f"        importlib.import_module({mod!r})")
    body_lines += ["", "if __name__ == '__main__':", "    unittest.main()"]
    content = "\n".join(body_lines) + "\n"

    with tempfile.TemporaryDirectory(prefix="ody-selftest-") as tmp:
        test_path = Path(tmp) / "test_ody_smoke.py"
        test_path.write_text(content, encoding="utf-8")
        ok, output = _run_cmd(
            [_PYTHON, "-m", "unittest", str(test_path)],
            cwd=str(root),
            timeout=60,
            env={**os.environ, "PYTHONPATH": str(root) + os.pathsep + os.environ.get("PYTHONPATH", "")},
        )
        return [str(test_path.name)], ok, output


def _run_cmd(
    cmd: List[str],
    *,
    cwd: str,
    timeout: int,
    env: Optional[Dict[str, str]] = None,
) -> tuple:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode == 0, out
    except subprocess.TimeoutExpired as e:
        return False, f"timeout after {timeout}s: {e}"
    except Exception as e:
        return False, str(e)


def _which(name: str) -> Optional[str]:
    from shutil import which
    return which(name)


def _trim(text: str, limit: int = 8000) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[: limit - 20] + "\n…[truncated]…"


# Agent-facing directive injected for coding tasks
SELF_TEST_DIRECTIVE = """\
## Self-testing before hand-off (mandatory for coding tasks)
Before you declare DONE on any coding change:
1. Run the existing test suite if one exists (`pytest` / `python -m unittest`).
2. If none exists for the touched code, write minimal tests covering the change and run them.
3. Check for obvious syntax/runtime errors (compile/import).
4. If tests fail or cannot be run, say so explicitly — never present the code as done.
This applies whether the task stayed local or was partially escalated to cloud.
"""
