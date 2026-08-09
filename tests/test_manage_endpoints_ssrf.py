"""manage_endpoints add must reject link-local / metadata SSRF targets."""

import asyncio
import importlib.util
import json
import sys
from pathlib import Path


def _load_admin_tools():
    """Load admin_tools.py without importing the heavy agent_tools package."""
    path = Path("/workspace/src/agent_tools/admin_tools.py")
    spec = importlib.util.spec_from_file_location("admin_tools_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_manage_endpoints_rejects_link_local(monkeypatch):
    mod = _load_admin_tools()
    import core.database as dbmod

    class _FakeSession:
        def add(self, *a, **k):
            raise AssertionError("should not add rejected endpoint")

        def commit(self):
            pass

        def close(self):
            pass

    monkeypatch.setattr(dbmod, "SessionLocal", lambda: _FakeSession())

    result = asyncio.run(
        mod.do_manage_endpoints(
            json.dumps(
                {
                    "action": "add",
                    "name": "meta",
                    "base_url": "http://169.254.169.254/latest/meta-data/",
                }
            )
        )
    )
    assert result["exit_code"] == 1
    assert "Rejected" in result["error"] or "link-local" in result["error"].lower()
