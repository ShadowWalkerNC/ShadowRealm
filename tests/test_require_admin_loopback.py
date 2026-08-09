"""Tests for require_admin internal-token loopback gating."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException


def _req(*, host="127.0.0.1", headers=None, current_user=None, auth_manager=None):
    request = MagicMock()
    request.client = SimpleNamespace(host=host)
    request.headers = headers or {}
    request.state = SimpleNamespace(current_user=current_user)
    request.app = SimpleNamespace(state=SimpleNamespace(auth_manager=auth_manager))
    return request


def test_require_admin_internal_token_requires_loopback(monkeypatch):
    import core.middleware as mw

    monkeypatch.setattr(mw, "INTERNAL_TOOL_TOKEN", "a" * 64)
    monkeypatch.setenv("AUTH_ENABLED", "true")

    auth = MagicMock()
    auth.is_configured = True
    auth.is_admin.return_value = False

    # Non-loopback + correct token → still 403
    with pytest.raises(HTTPException) as ei:
        mw.require_admin(
            _req(
                host="10.0.0.5",
                headers={mw.INTERNAL_TOOL_HEADER: "a" * 64},
                current_user="bob",
                auth_manager=auth,
            )
        )
    assert ei.value.status_code == 403

    # Loopback + correct token → allowed
    mw.require_admin(
        _req(
            host="127.0.0.1",
            headers={mw.INTERNAL_TOOL_HEADER: "a" * 64},
            current_user="bob",
            auth_manager=auth,
        )
    )


def test_require_admin_rejects_token_behind_proxy_headers(monkeypatch):
    import core.middleware as mw

    monkeypatch.setattr(mw, "INTERNAL_TOOL_TOKEN", "b" * 64)
    monkeypatch.setenv("AUTH_ENABLED", "true")
    auth = MagicMock()
    auth.is_configured = True
    auth.is_admin.return_value = False

    with pytest.raises(HTTPException):
        mw.require_admin(
            _req(
                host="127.0.0.1",
                headers={
                    mw.INTERNAL_TOOL_HEADER: "b" * 64,
                    "x-forwarded-for": "1.2.3.4",
                },
                current_user="bob",
                auth_manager=auth,
            )
        )


def test_tokens_match_length_safe():
    from core.middleware import tokens_match

    assert tokens_match("abc", "abc") is True
    assert tokens_match("ab", "abc") is False
    assert tokens_match(None, "abc") is False


def test_short_env_internal_token_ignored(monkeypatch):
    monkeypatch.setenv("SHADOWREALM_INTERNAL_TOKEN", "tooshort")
    monkeypatch.delenv("ODYSSEUS_INTERNAL_TOKEN", raising=False)
    # Re-resolve via the helper (import-time constant already bound).
    from core.middleware import _resolve_internal_tool_token, MIN_INTERNAL_TOKEN_LEN

    tok = _resolve_internal_tool_token()
    assert len(tok) >= MIN_INTERNAL_TOKEN_LEN
    assert tok != "tooshort"
