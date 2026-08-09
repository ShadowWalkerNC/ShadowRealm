"""Shell timeout / command-length hardening."""

import pytest
from fastapi import HTTPException

from routes.shell_routes import (
    MAX_SHELL_COMMAND_BYTES,
    MAX_SHELL_TIMEOUT,
    _normalize_shell_timeout,
    _validate_shell_command,
)


def test_normalize_shell_timeout_caps_and_rejects_unlimited():
    assert _normalize_shell_timeout(None, 30) == 30
    assert _normalize_shell_timeout(0, 30) == MAX_SHELL_TIMEOUT
    assert _normalize_shell_timeout(-1, 30) == MAX_SHELL_TIMEOUT
    assert _normalize_shell_timeout(99999, 30) == MAX_SHELL_TIMEOUT
    assert _normalize_shell_timeout(120, 30) == 120


def test_validate_shell_command_rejects_empty_and_oversized():
    with pytest.raises(HTTPException) as empty:
        _validate_shell_command("   ")
    assert empty.value.status_code == 400

    huge = "x" * (MAX_SHELL_COMMAND_BYTES + 1)
    with pytest.raises(HTTPException) as big:
        _validate_shell_command(huge)
    assert big.value.status_code == 400

    assert _validate_shell_command(" echo hi ") == "echo hi"
