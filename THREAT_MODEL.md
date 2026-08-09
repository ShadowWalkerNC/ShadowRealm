# Threat Model

Odysseus is a **self-hosted AI workspace with privileged local access**. This document states the trust boundary so contributors can reason about security decisions without reading through the full auth and middleware stack.

## Trust Boundary

Odysseus is designed for **trusted users on a private network**, not public exposure. The README describes it as "treat it like an admin console" — that framing is accurate. A logged-in admin can execute shell commands, read and write files, send email, and control model serving. This is intentional. The threat model does not try to prevent admins from doing these things. It does try to prevent:

- Unauthenticated access
- Non-admins reaching admin-only capabilities
- The AI agent acting on instructions injected through untrusted content (web results, emails, fetched pages, memories)
- Internal services (ChromaDB, Ollama, SearXNG, etc.) being reachable from outside the host

## Roles and Capabilities

| Capability | Admin | Non-admin (default) |
|---|---|---|
| Chat with agent | ✓ | ✓ |
| Browser tool | ✓ | ✓ |
| Documents | ✓ | ✓ |
| Research mode | ✓ | ✓ |
| Image generation | ✓ | ✓ |
| Memory management | ✓ | ✓ |
| Shell / Python execution | ✓ | ✗ |
| File read / write | ✓ | ✗ |
| Email send / read | ✓ | ✗ |
| MCP tools | ✓ | ✗ |
| Calendar management | ✓ | ✗ |
| Token / webhook management | ✓ | ✗ |
| Model serving | ✓ | ✗ |
| Vault | ✓ | ✗ |
| Settings | ✓ | ✗ |

Non-admin defaults are in `core/auth.py:DEFAULT_PRIVILEGES`. Tool enforcement is in `src/tool_security.py:NON_ADMIN_BLOCKED_TOOLS`. Any tool whose name starts with `mcp__` is also blocked for non-admins. Admins always get full access regardless of stored privilege values.

## Authentication

- **Sessions:** bcrypt passwords, 7-day session tokens stored atomically in `data/sessions.json` via `core/atomic_io.py`.
- **2FA:** TOTP with 8 single-use backup codes. Verified after password check, before session issuance.
- **Reserved usernames:** `internal-tool`, `api`, `demo`, `system` cannot be registered or renamed into. Defined in `core/auth.py:RESERVED_USERNAMES`.
  - `internal-tool` is security-critical: `core/middleware.py:require_admin` treats any request where `request.state.current_user == "internal-tool"` as the in-process tool loopback and grants admin unconditionally. A real account with that name would silently pass every `require_admin` check.
- **Orphan sessions:** `validate_token` re-checks that the user record still exists on every call. A deleted user's cookie is dropped on next request rather than continuing to authenticate.

## Internal Tool Loopback

Agent tool calls reach admin-gated HTTP routes over an in-process HTTP loopback. The mechanism:

1. At app startup, `core/middleware.py` resolves `INTERNAL_TOOL_TOKEN` from
   `SHADOWREALM_INTERNAL_TOKEN` / `ODYSSEUS_INTERNAL_TOKEN` (min 32 chars) or
   generates a random `secrets.token_hex(32)`. Short env values are ignored.
   The token is never sent to clients.
2. Loopback requests carry `X-ShadowRealm-Internal-Token` (or legacy
   `X-Odysseus-Internal-Token`) **and** must be a trusted loopback client
   (no proxy/tunnel forwarding headers). AuthMiddleware also stamps
   `request.state.current_user` to `"internal-tool"` when valid.
3. `require_admin` recognises the same loopback+token signal (or the
   already-stamped `internal-tool` user) and grants access without checking
   the session user.

The agent may be running in a non-admin user's session, but tool dispatch first calls `src/tool_security.py:owner_is_admin_or_single_user` to verify the session owner is an admin before issuing any loopback call. Non-admin users cannot invoke admin tools even via the agent.

## Prompt-Injection Hardening

External content that reaches the LLM is treated as untrusted via `src/prompt_security.py`:

- `untrusted_context_message(label, content)` wraps the content in a `user`-role message with a header block instructing the model not to follow instructions inside it. Content goes in as data, not as a system instruction.
- `UNTRUSTED_CONTEXT_POLICY` is a system-prompt preamble that states the same policy at the top of every session where untrusted data may appear.

**Untrusted surfaces that must go through this wrapper:** web search results, fetched URLs, emails (read), saved memories, skill text, notes, and any tool output sourced from outside the server. Injecting untrusted content directly into the system role is a security bug.

## Security Headers

`core/middleware.py:SecurityHeadersMiddleware` sets headers on every response:

- `X-Frame-Options: DENY` + `frame-ancestors 'none'` on all routes except tool-render iframes (which are sandboxed at the HTML level).
- `X-Content-Type-Options: nosniff` and `Referrer-Policy: no-referrer` everywhere.
- **CSP:** nonce-based `script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net`. `style-src 'unsafe-inline'` is intentionally kept — `static/index.html` ships inline `<style>` blocks and JS modules set `style=""` attributes at runtime. Inline styles do not execute script so the risk is visual-only. Removing this requires templating the HTML files and auditing all JS-set style attributes.

## Known Gaps

These are open, acknowledged, and contributor help is welcome:

1. **No shell/filesystem sandbox.** The agent `bash` and `read_file`/`write_file` tools run as the app process user with no network egress filtering or filesystem confinement. A successful prompt-injection reaching a shell-enabled admin session can make outbound requests to internal services. Shell timeouts are now capped (agent ≤10m, UI ≤10m; unlimited `timeout=0` rejected), but this is not a sandbox. See #1058 for the sandbox proposal. **Do not mount `/var/run/docker.sock` by default** — use `docker-compose.docker-sock.yml` only when Cookbook needs host Docker. OpenHands / Prometheus / Grafana are compose profiles and bind loopback only.

2. **SSRF via `/api/v1/chat` `base_url` parameter — mitigated.** Chat-scoped tokens pass `base_url` through `validate_public_http_url` (scheme + DNS + private/link-local block). Residual: DNS-rebinding TOCTOU between resolve and connect. Admin-created model endpoints and integrations intentionally allow LAN/loopback (local-first) but **always block link-local / cloud metadata** via `check_outbound_url`.

3. **`src/search/` partial consolidation.** `src.search.core` and `src.search.providers` correctly alias `services.search` via `sys.modules` replacement. `analytics`, `cache`, `content`, `query`, and `ranking` are still independent copies that can drift. The SSRF regression tests in `tests/test_webhook_ssrf_resilience.py` test `src.webhook_manager` directly (separate from search), so the safety net there is intact. See #1058.

4. **Token scopes — path allowlist added; session privileges still coarse.** Bearer `ody_` tokens are **default-denied** unless the path matches `src/api_token_access.py` (e.g. `/api/v1/chat` and companion require `chat`; `/api/codex/*` relies on route-level scopes). There is still no way to grant a *browser session* a subset of the owning user's privileges.

## Recent hardening notes

- `require_admin` internal-tool bypass requires **trusted loopback** (no proxy headers), matching AuthMiddleware. Env overrides `SHADOWREALM_INTERNAL_TOKEN` / `ODYSSEUS_INTERNAL_TOKEN` shorter than 32 chars are ignored.
- `auth.json` / `sessions.json` are written mode `0o600`.
- `vault_get` redacts passwords/TOTP/notes from model-visible tool output.
- Admin bootstrap accepts `SHADOWREALM_ADMIN_*` or legacy `ODYSSEUS_ADMIN_*`.
