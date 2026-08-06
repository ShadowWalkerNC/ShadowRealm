"""Regression: vault_get must not return live secrets to the model."""

import asyncio
import json
from unittest.mock import AsyncMock, patch


def test_vault_get_redacts_password_and_totp(monkeypatch):
    from src.tools import vault as vault_mod

    item = {
        "id": "item-1",
        "name": "Example",
        "login": {
            "username": "alice",
            "password": "s3cret-password",
            "totp": "JBSWY3DPEHPK3PXP",
            "uris": [{"uri": "https://example.com"}],
        },
        "notes": "recovery codes here",
    }

    monkeypatch.setattr(vault_mod, "_load_vault_config", lambda: {"session": "sess"})
    monkeypatch.setattr(
        vault_mod,
        "_run_bw",
        AsyncMock(return_value=(json.dumps(item), "", 0)),
    )

    result = asyncio.run(
        vault_mod.do_vault_get(
            json.dumps({"item_id": "item-1", "reason": "fill login form"}),
            owner="admin",
        )
    )
    out = result["output"]
    assert "s3cret-password" not in out
    assert "JBSWY3DPEHPK3PXP" not in out
    assert "recovery codes here" not in out
    assert "REDACTED" in out
    assert "alice" in out
