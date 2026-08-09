"""Central API-token path → scope allowlist (default-deny).

Bearer ``ody_`` tokens authenticate globally in AuthMiddleware. Without a
central gate, any valid token could call owner-scoped routes that use
``effective_user()`` without checking ``api_token_scopes``.

Rules are longest-prefix match. A non-empty scope set means the token must
hold at least one of those scopes. An empty frozenset means "any authenticated
token may reach this prefix" — used for ``/api/codex/*`` where route handlers
enforce finer scopes themselves.
"""

from __future__ import annotations

from typing import FrozenSet, List, Optional, Tuple

# (path_prefix, any-of scopes). Empty frozenset = any valid token (route-level).
_API_TOKEN_ROUTE_RULES: List[Tuple[str, FrozenSet[str]]] = [
    ("/api/v1/chat", frozenset({"chat"})),
    ("/api/companion", frozenset({"chat"})),
    ("/api/codex", frozenset()),  # finer checks in routes/codex_routes.py
    ("/api/models", frozenset({"chat"})),
    # Companion / chat clients resume and manage the owner's sessions.
    ("/api/sessions", frozenset({"chat"})),
    ("/api/session", frozenset({"chat"})),
    ("/api/chat", frozenset({"chat"})),
    ("/api/agent", frozenset({"chat"})),
    ("/api/history", frozenset({"chat"})),
    ("/api/upload", frozenset({"chat"})),
    ("/api/uploads", frozenset({"chat"})),
]


def required_scopes_for_path(path: str) -> Optional[FrozenSet[str]]:
    """Return the any-of scope set for ``path``, or None if no rule matches.

    None means the path is not allowlisted for bearer tokens (default-deny).
    """
    path = path or ""
    best: Optional[Tuple[str, FrozenSet[str]]] = None
    for prefix, scopes in _API_TOKEN_ROUTE_RULES:
        if path == prefix or path.startswith(prefix + "/") or (
            prefix.endswith("/") and path.startswith(prefix)
        ):
            if best is None or len(prefix) > len(best[0]):
                best = (prefix, scopes)
        # Also allow exact prefix without trailing semantics for short prefixes
        elif path.startswith(prefix) and (
            len(path) == len(prefix) or path[len(prefix)] in "/?#"
        ):
            if best is None or len(prefix) > len(best[0]):
                best = (prefix, scopes)
    return None if best is None else best[1]


def check_api_token_path_access(path: str, scopes) -> Optional[str]:
    """Return an error message if the bearer token may not call ``path``.

    ``scopes`` is the list/iterable from ``request.state.api_token_scopes``.
    Returns None when access is allowed.
    """
    required = required_scopes_for_path(path)
    if required is None:
        return "API token is not allowed for this endpoint"
    if not required:
        # Empty set: prefix allowlisted; route handlers enforce finer scopes.
        return None
    held = {str(s).strip() for s in (scopes or []) if str(s).strip()}
    if held.intersection(required):
        return None
    needed = ", ".join(sorted(required))
    return f"API token missing required scope (need one of: {needed})"
