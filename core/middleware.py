# core/middleware.py
# Shared middleware, decorators, and request helpers

import os
import secrets

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


# Per-process token that lets the in-app tool layer hit admin-gated
# routes via HTTP loopback (the agent's tool calls don't carry the
# admin user's session cookie). Set once at import; tools read the
# same value from this module. Never exposed to clients.
#
# Reads SHADOWREALM_INTERNAL_TOKEN first for new deployments.
# Falls back to the legacy ODYSSEUS_INTERNAL_TOKEN name so existing
# .env files keep working without changes. Env overrides must be at
# least MIN_INTERNAL_TOKEN_LEN hex/bytes long — short values are
# rejected and a fresh random token is used instead.
MIN_INTERNAL_TOKEN_LEN = 32


def _resolve_internal_tool_token() -> str:
    for key in ("SHADOWREALM_INTERNAL_TOKEN", "ODYSSEUS_INTERNAL_TOKEN"):
        raw = (os.environ.get(key) or "").strip()
        if not raw:
            continue
        if len(raw) < MIN_INTERNAL_TOKEN_LEN:
            # Weak/shared env tokens become a global admin key if accepted.
            # Fail closed to a random per-process token and warn via stderr
            # (logging may not be configured at import time).
            import sys
            print(
                f"[security] Ignoring {key}: value shorter than "
                f"{MIN_INTERNAL_TOKEN_LEN} chars; using ephemeral token.",
                file=sys.stderr,
            )
            continue
        return raw
    return secrets.token_hex(32)


INTERNAL_TOOL_TOKEN = _resolve_internal_tool_token()
INTERNAL_TOOL_HEADER = "X-ShadowRealm-Internal-Token"
# Backward-compat alias — old routes that still reference the Odysseus header
# name will still match. Remove after Sprint 4 UI cleanup.
INTERNAL_TOOL_HEADER_LEGACY = "X-Odysseus-Internal-Token"
# Pseudo-username on in-process tool-loopback requests; require_admin trusts it and it is reserved.
INTERNAL_TOOL_USER = "internal-tool"

# Headers that prove a request was forwarded by a proxy/tunnel (cloudflared,
# nginx, Caddy, Tailscale Funnel, …). cloudflared connects to the app FROM
# 127.0.0.1, so without this check every tunneled request would look like
# loopback and could bypass auth / the internal-tool path.
PROXY_FWD_HEADERS = (
    "cf-connecting-ip", "cf-ray", "cf-visitor",
    "x-forwarded-for", "x-forwarded-host", "x-real-ip", "forwarded",
)


def is_trusted_loopback(request: Request) -> bool:
    """True ONLY for a DIRECT loopback connection with no proxy/tunnel headers.

    A bare ``client.host in ('127.0.0.1','::1')`` check is unsafe behind a
    Cloudflare tunnel / reverse proxy: those connect from loopback, so a
    remote visitor would otherwise inherit local trust. In-process agent
    loopback calls carry none of these headers, so they still qualify.
    """
    host = request.client.host if getattr(request, "client", None) else None
    if host not in ("127.0.0.1", "::1"):
        return False
    headers = getattr(request, "headers", None) or {}
    for header in PROXY_FWD_HEADERS:
        try:
            if headers.get(header):
                return False
        except Exception:
            continue
    return True


def tokens_match(provided: str | None, expected: str) -> bool:
    """Constant-time compare that never raises on length mismatch."""
    if not provided or not expected:
        return False
    if len(provided) != len(expected):
        return False
    return secrets.compare_digest(provided, expected)


def is_cors_preflight(method: str, headers) -> bool:
    """True for a genuine CORS preflight: an OPTIONS request carrying the
    Access-Control-Request-Method header. Such requests are credential-less by
    design and must reach CORSMiddleware to be answered -- gating them on auth
    401s the preflight and breaks every cross-origin browser/WebView client.
    Pure so it can be unit-tested without standing up the app."""
    return method == "OPTIONS" and "access-control-request-method" in headers


def require_admin(request: Request):
    """Raise 403 if the current user isn't an admin.
    Allows access when auth is explicitly disabled, or when the request carries
    the in-process internal-tool token used by loopback agent tools.
    """
    # In-process bypass for tool-layer loopback calls. Two paths:
    # (a) header-direct (caller set X-ShadowRealm-Internal-Token or legacy alias)
    #     AND the client is a trusted loopback (no proxy headers), or
    # (b) the auth middleware already validated the token + loopback and stamped
    #     request.state.current_user = "internal-tool".
    headers = getattr(request, "headers", None) or {}
    try:
        hdr = headers.get(INTERNAL_TOOL_HEADER) or headers.get(INTERNAL_TOOL_HEADER_LEGACY)
    except Exception:
        hdr = None
    if tokens_match(hdr, INTERNAL_TOOL_TOKEN) and is_trusted_loopback(request):
        return
    state = getattr(request, "state", None)
    if getattr(state, "current_user", None) == INTERNAL_TOOL_USER:
        return

    try:
        auth_mgr = getattr(request.app.state, "auth_manager", None)
    except Exception:
        auth_mgr = None

    if os.getenv("AUTH_ENABLED", "true").lower() == "false":
        return
    if not auth_mgr or not auth_mgr.is_configured:
        raise HTTPException(403, "Admin only")
    user = getattr(state, "current_user", None)
    if not user or not auth_mgr.is_admin(user):
        raise HTTPException(403, "Admin only")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add standard security headers to all responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate a per-request nonce for inline scripts
        nonce = secrets.token_hex(16)
        request.state.csp_nonce = nonce

        response = await call_next(request)
        path = request.url.path

        # Tool render endpoints
        is_tool_render = path.startswith("/api/tools/") and path.endswith("/render")
        # Document library PDF preview endpoint
        is_document_pdf_preview = path.startswith("/api/document/") and path.endswith("/render-pdf")
        # Visual report pages are self-contained HTML — need inline scripts + external images
        is_report = path.startswith("/api/research/report/")

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(self), geolocation=()"

        is_https = (
            request.url.scheme == "https"
            or request.headers.get("X-Forwarded-Proto") == "https"
        )
        if is_https:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        if is_report:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "font-src 'self'; "
                "img-src 'self' data: blob: https:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'"
            )
        elif is_tool_render:
            # Skip framing headers for tools.
            pass
        elif is_document_pdf_preview:
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; "
                "frame-ancestors 'self'"
            )
        else:
            response.headers["X-Frame-Options"] = "DENY"
            # NOTE: `style-src 'unsafe-inline'` is intentionally retained.
            # `static/index.html` and `static/login.html` ship inline <style>
            # blocks, and several JS modules build runtime `style=""` attrs.
            # Migrating to nonce-only requires templating the HTML files +
            # auditing every JS-set style attribute. Since inline styles
            # don't execute script, the residual risk is visual-only.
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "img-src 'self' data: blob:; "
                "media-src 'self' blob:; "
                "connect-src 'self'; "
                "frame-src 'self'; "
                "frame-ancestors 'none'"
            )
        return response
