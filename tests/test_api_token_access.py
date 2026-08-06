"""Unit tests for central API-token path → scope allowlist."""

from src.api_token_access import check_api_token_path_access, required_scopes_for_path


def test_chat_path_requires_chat_scope():
    assert required_scopes_for_path("/api/v1/chat") == frozenset({"chat"})
    assert check_api_token_path_access("/api/v1/chat", ["chat"]) is None
    err = check_api_token_path_access("/api/v1/chat", ["todos:read"])
    assert err and "chat" in err


def test_unlisted_path_default_deny():
    assert required_scopes_for_path("/api/shell/exec") is None
    err = check_api_token_path_access("/api/shell/exec", ["chat"])
    assert err and "not allowed" in err


def test_codex_prefix_allows_any_authenticated_token():
    # Finer scopes enforced in routes/codex_routes.py
    assert required_scopes_for_path("/api/codex/todos") == frozenset()
    assert check_api_token_path_access("/api/codex/todos", ["todos:read"]) is None
    assert check_api_token_path_access("/api/codex/todos", []) is None


def test_sessions_require_chat():
    assert "chat" in required_scopes_for_path("/api/sessions/abc")
    assert check_api_token_path_access("/api/sessions", ["chat"]) is None
    assert check_api_token_path_access("/api/sessions", ["memory:read"]) is not None


def test_companion_requires_chat():
    assert check_api_token_path_access("/api/companion/models", ["chat"]) is None
    assert check_api_token_path_access("/api/companion/ping", ["email:read"]) is not None
