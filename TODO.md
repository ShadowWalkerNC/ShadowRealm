# ShadowRealm — Structured Gap Tracker

Priority-ordered by dependency. Fix items in sequence — later items depend on earlier ones.

Legend: 🔴 Critical blocker · 🟡 Missing capability · 🟠 Hardening · ✅ Done

---

## 🔴 CRITICAL — Blockers (Do These First)

### SR-001 · Wire MCP into Python inference loop
**File(s):** `app.py`, `core/mcp_client.py` (new), `mcp-registry.json`  
**Status:** ⬜ Not started  
**Problem:**  
`mcp_servers/` has 7 working servers but there is no Python MCP client that intercepts `tool_call` responses from the LLM, routes to the correct server, injects the result back, and continues the loop. The orchestrator is JavaScript and not connected to Flask.

**Tasks:**
- [ ] Implement `core/mcp_client.py` — Python MCP client (stdio + SSE transport)
- [ ] Add tool call interception in `app.py` streaming loop
- [ ] Map tool names → MCP server via `mcp-registry.json`
- [ ] Inject tool results back as `tool` role messages
- [ ] Handle multi-turn tool loops (tool → result → next tool → …)
- [ ] Timeout + error handling per tool call
- [ ] Tests for each registered MCP server

**Unlocks:** SR-002, SR-003, SR-005, SR-006, SR-007

---

### SR-002 · Add planner + supervisor to orchestrator
**File(s):** `orchestrator/planner.py` (new), `orchestrator/supervisor.py` (new), `orchestrator/context_bus.py` (new)  
**Status:** ⬜ Not started  
**Problem:**  
`tool_dispatcher.js` handles single tool dispatch only. There is no component that breaks a multi-step goal into tasks, assigns tasks to agents or tools, tracks state across steps, retries on failure, and merges results.

**Tasks:**
- [ ] `orchestrator/planner.py` — goal → task graph (DAG)
- [ ] `orchestrator/supervisor.py` — execute DAG, monitor, retry, merge
- [ ] `orchestrator/context_bus.py` — shared state store between agents mid-run
- [ ] Integrate planner output with tool dispatcher
- [ ] Support sequential and parallel task chains
- [ ] Max step limit + infinite loop guard

**Depends on:** SR-001  
**Unlocks:** SR-005, SR-006

---

### SR-003 · Bridge memory_server ↔ session_manager
**File(s):** `mcp_servers/memory_server.py`, `core/session_manager.py`  
**Status:** ⬜ Not started  
**Problem:**  
`session_manager.py` manages the context window (what fits in one prompt) but has no vector search and no long-term recall. `memory_server.py` exists but is not called by session management. The two systems are completely disconnected.

**Tasks:**
- [ ] Add vector store backend to `memory_server.py` (ChromaDB or Qdrant)
- [ ] `session_manager.py` — on each new message, query memory for relevant context
- [ ] `session_manager.py` — on each AI response, store key facts to memory
- [ ] Memory retrieval score threshold (don't inject low-relevance memories)
- [ ] Per-user memory namespacing
- [ ] Memory clear/export API endpoint

**Depends on:** SR-001  
**Unlocks:** SR-005

---

## 🟡 MISSING CAPABILITIES

### SR-004 · Search engine layer (multi-provider router)
**File(s):** `core/search/` (new directory)  
**Status:** ⬜ Not started  
**Problem:**  
No search providers exist in the codebase. Agents cannot reach the live web. RAG server can only index documents you manually provide.

**Tasks:**
- [ ] `core/search/search_router.py` — fan-out query to N providers in parallel
- [ ] `core/search/providers/brave.py`
- [ ] `core/search/providers/searxng.py`
- [ ] `core/search/providers/perplexity_api.py`
- [ ] `core/search/providers/google_cse.py`
- [ ] `core/search/providers/ddg.py`
- [ ] `core/search/result_ranker.py` — merge, dedupe, rank results
- [ ] `core/search/cache.py` — Redis/SQLite cache for repeat queries
- [ ] Config flags in `.env` per provider (API key + enable/disable)
- [ ] `/api/search` route in `app.py`

**Unlocks:** SR-005

---

### SR-005 · Agent base class + role-specific agents
**File(s):** `agents/` (new directory)  
**Status:** ⬜ Not started  
**Problem:**  
No agent abstraction exists. `integrations/claude/` and `integrations/codex/` are empty directories.

**Tasks:**
- [ ] `agents/base_agent.py` — abstract class: `run()`, `plan()`, `act()`, `reflect()`
- [ ] `agents/researcher.py` — search + scrape + summarize
- [ ] `agents/coder.py` — write / execute / test code
- [ ] `agents/analyst.py` — data reasoning agent
- [ ] `agents/writer.py` — long-form content agent
- [ ] `agents/custom/` — drop-in folder for user-defined agents
- [ ] Agent registry (name → class mapping)
- [ ] Per-agent system prompt + tool manifest
- [ ] Agent result schema (structured output)

**Depends on:** SR-001, SR-002, SR-003, SR-004

---

### SR-006 · Pipeline system (named, replayable chains)
**File(s):** `pipelines/` (new directory)  
**Status:** ⬜ Not started  
**Problem:**  
No way to define, save, or replay a named chain of agent operations. Every interaction is stateless and one-shot.

**Tasks:**
- [ ] `pipelines/pipeline_runner.py` — load + execute a pipeline definition
- [ ] Pipeline schema (YAML/JSON): steps, agents, inputs, outputs, conditions
- [ ] `pipelines/templates/deep_research.yaml`
- [ ] `pipelines/templates/code_review.yaml`
- [ ] `pipelines/templates/api_monitor.yaml`
- [ ] `pipelines/ui_builder.py` — generate pipeline configs from chat/UI
- [ ] Pipeline run history stored in `database.py`
- [ ] `/api/pipelines` CRUD routes

**Depends on:** SR-002, SR-005

---

### SR-007 · Custom API plugin system
**File(s):** `integrations/` (expand existing)  
**Status:** ⬜ Not started  
**Problem:**  
`integrations/` has only two empty subdirectories. Every new API requires custom code. No generic auth-aware HTTP client, no webhook handler.

**Tasks:**
- [ ] `integrations/api_registry.json` — name, base_url, auth_type, endpoints
- [ ] `integrations/api_client.py` — generic authenticated HTTP client
- [ ] `integrations/auth/bearer.py`
- [ ] `integrations/auth/oauth2.py`
- [ ] `integrations/auth/api_key.py`
- [ ] `integrations/webhooks/inbound_handler.py` — webhook → trigger pipeline
- [ ] `integrations/webhooks/outbound_sender.py` — send results to external services
- [ ] `/api/integrations` CRUD routes
- [ ] UI panel for managing registered APIs

**Depends on:** SR-001

---

## 🟠 HARDENING — Production Readiness

### SR-008 · Async Flask / concurrency fix
**File(s):** `app.py`  
**Status:** ⬜ Not started  
**Problem:**  
Sync Flask blocks under concurrent load — multiple agents running, streaming responses, and tool calls in flight will queue behind each other.

**Tasks:**
- [ ] Option A: add `gevent` workers to gunicorn config (lower effort)
- [ ] Option B: migrate to FastAPI or Quart (higher effort, better long-term)
- [ ] Benchmark before + after under concurrent agent load

---

### SR-009 · Postgres support in database layer
**File(s):** `core/database.py`  
**Status:** ⬜ Not started  
**Problem:**  
`database.py` (103KB) is SQLite-only. No connection pooling, no Postgres path, no vector column (pgvector) for semantic memory.

**Tasks:**
- [ ] Abstract DB backend behind an interface
- [ ] Add Postgres adapter (SQLAlchemy or asyncpg)
- [ ] Connection pool config
- [ ] `pgvector` extension support for memory queries
- [ ] Migration guide SQLite → Postgres

---

### SR-010 · Middleware hook system + observability
**File(s):** `core/middleware.py`  
**Status:** ⬜ Not started  
**Problem:**  
`middleware.py` is 5KB — thin for what it needs to do. No pre/post-request plugin hooks, no per-route policy injection, no tracing or metrics.

**Tasks:**
- [ ] Plugin-style hook system: `on_request`, `on_response`, `on_error`
- [ ] Per-route policy injection (rate limits, auth requirements, tool allowlist)
- [ ] Request tracing (trace ID propagated through agent runs)
- [ ] Prometheus-compatible metrics endpoint (`/metrics`)
- [ ] Structured JSON logging

---

### SR-011 · Circuit breaker + upstream fallback
**File(s):** `app.py`, `routes/`  
**Status:** ⬜ Not started  
**Problem:**  
If an AI provider goes down or rate-limits, there's no automatic fallback, no retry with backoff, no endpoint health scoring.

**Tasks:**
- [ ] Per-endpoint health state (healthy / degraded / down)
- [ ] Exponential backoff on 429/5xx responses
- [ ] Auto-fallback to next healthy endpoint in same model group
- [ ] Health state visible in admin UI
- [ ] Alert via ntfy/email when provider goes down

---

### SR-012 · Security hardening
**File(s):** `core/auth.py`, `mcp_servers/`, `core/middleware.py`  
**Status:** ⬜ Not started  
**Problem:**  
ROADMAP already flags: user-editable skills, notes, documents, fetched pages, and memories should be treated as untrusted data. Prompt injection via tool results is a real attack surface.

**Tasks:**
- [ ] Sanitize all tool results before injecting into prompt
- [ ] Admin-only tool allowlist (some tools should never run as user)
- [ ] API key scoping (per-key tool/route restrictions)
- [ ] Rate limit per user per tool
- [ ] Audit log for all tool executions
- [ ] OAuth2 provider login (Google, GitHub)

---

### SR-013 · Refactor + dead code cleanup
**File(s):** `app.py`, `static/style.css`, `orchestrator/`  
**Status:** ⬜ Not started  
**Problem:**  
ROADMAP flags CSS chaos, dead routes, stale feature flags, and copy-pasted tour scaffolding.

**Tasks:**
- [ ] Dead code pass: old routes, unused UI states, stale feature flags
- [ ] CSS cleanup (`static/style.css`)
- [ ] Shared `tour-core.js` helper to replace copy-pasted tour scaffolding
- [ ] Modal/popup positioning refactor
- [ ] Mobile `@media` override comments/linting

---

## Dependency Graph

```
SR-001 (MCP loop)
  └── SR-002 (Planner)
  └── SR-003 (Memory bridge)
  └── SR-007 (API plugins)

SR-001 + SR-002 + SR-003 + SR-004 (Search)
  └── SR-005 (Agents)
      └── SR-006 (Pipelines)

SR-008 (Async)       — parallel, improves everything
SR-009 (Postgres)    — parallel, needed before production scale
SR-010 (Middleware)  — parallel, needed before production scale
SR-011 (Circuit breaker) — parallel
SR-012 (Security)    — parallel, but do before any public exposure
SR-013 (Refactor)    — ongoing
```

---

*Last updated: 2026-06-28*
