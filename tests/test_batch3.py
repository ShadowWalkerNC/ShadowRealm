import pytest
from core.deployment_manager import DeploymentManager
from core.config_drift_detector import ConfigDriftDetector
from core.release_gate import ReleaseGate
from integrations.github_adapter import GitHubAdapter
from integrations.calendar_adapter import CalendarAdapter
from integrations.browser_adapter import BrowserAdapter

def test_devops_logic():
    dm = DeploymentManager()
    assert dm.deploy("1.1.0")["active_version"] == "1.1.0"
    assert dm.rollback()["active_version"] == "1.0.0"
    
    drift = ConfigDriftDetector.detect_drift({"a": 1}, {"a": 1, "b": 2})
    assert len(drift) == 1
    
    failures = ReleaseGate.run_preflight_checks(tests_passed=False, lint_passed=True)
    assert "Test suite failed" in failures

def test_integrations_adapters():
    gh = GitHubAdapter()
    assert len(gh.fetch_repos("test-user")) == 2
    assert gh.create_pr("test-repo", "Fix bugs", "dev", "main")["id"] == 101
    
    cal = CalendarAdapter("http://cal.local")
    event = cal.add_event("Meeting", "2026-07-04T12:00:00", "2026-07-04T13:00:00")
    assert len(cal.list_events()) == 1
    
    browser = BrowserAdapter()
    res = browser.fetch_page_content("https://example.com")
    assert res["status"] == 200
