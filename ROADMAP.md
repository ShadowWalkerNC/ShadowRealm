# ShadowRealm v2 — Master Roadmap

> Last updated: 2026-06-29  
> Branch: `shadowrealm-v2`  
> Progress: **78 / 120 components shipped**

---

## Progress Overview

| Track | Components | Status |
|---|---|---|
| Foundation (C1–C18) | 18 | ✅ Complete |
| Data & Storage (C19–C36) | 18 | ✅ Complete |
| Security & Auth (C37–C54) | 18 | ✅ Complete |
| Observability (C55–C63) | 9 | ✅ Complete |
| Task & Job Queue (C64–C66) | 3 | ✅ Complete |
| Networking & HTTP (C67–C69) | 3 | ✅ Complete |
| Event Sourcing & Audit (C70–C72) | 3 | ✅ Complete |
| Search & Indexing (C73–C75) | 3 | ✅ Complete |
| User & Session (C76–C78) | 3 | ✅ Complete |
| Notification & Messaging (C79–C81) | 3 | 🔄 Sprint 23 |
| Permission & Policy (C82–C84) | 3 | Queued |
| Plugin & Extension (C85–C87) | 3 | Queued |
| AI/LLM Integration (C88–C90) | 3 | Queued |
| Workflow Engine (C91–C93) | 3 | Queued |
| Data Pipeline (C94–C96) | 3 | Queued |
| Multimodal & Media (C97–C99) | 3 | Queued |
| Testing Infrastructure (C100–C102) | 3 | Queued |
| Deployment & DevOps (C103–C105) | 3 | Queued |
| Integration Adapters (C106–C108) | 3 | Queued |
| **[NEW] Agent Identity Layer (C109–C111)** | 3 | Queued — Hermes-inspired |
| **[NEW] Memory Vault (C112–C114)** | 3 | Queued — Hermes-inspired |
| **[NEW] Operational Controls (C115–C117)** | 3 | Queued — Hermes-inspired |
| **[NEW] Model & Channel Routing (C118–C120)** | 3 | Queued — Hermes-inspired |

---

## Original Sprints (C1–C108)

### ✅ Sprint 1–6 — Foundation & Core (C1–C18)
Config, logging, error handling, event bus, plugin manager, service registry, CLI, env validator, task runner.

### ✅ Sprint 7–12 — Data & Storage (C19–C36)
Database manager, migrations, model registry, cache layers, file store, blob store, document store, graph store, time-series store, data validator, serialiser, query builder.

### ✅ Sprint 13–18 — Security & Auth (C37–C54)
JWT auth, OAuth2, RBAC, rate limiter, request validator, secret manager, encryption, key rotation, audit, threat model.

### ✅ Sprint 16–17 — Observability (C55–C63)
Structured logging, distributed tracing, metrics collector, alert manager, dashboard, health checker, metrics registry, diagnostics reporter.

### ✅ Sprint 18 — Task & Job Queue (C64–C66)
TaskQueue (priority + retry + DLQ), JobScheduler (interval/cron/once), WorkerPool (thread drain + backoff).

### ✅ Sprint 19 — Networking & HTTP (C67–C69)
HTTPClient (retry + auth), WebhookDispatcher (HMAC-signed), RateLimitedSession (token bucket).

### ✅ Sprint 20 — Event Sourcing & Audit (C70–C72)
EventStore (append-only + snapshots), AuditLogger (hash-chained), ChangeTracker (field diff + rollback).

### ✅ Sprint 21 — Search & Indexing (C73–C75)
FullTextIndex (FTS5/BM25), VectorSearchIndex (cosine + numpy), SearchRouter (hybrid RRF fusion).

### ✅ Sprint 22 — User & Session (C76–C78)
UserStore (PBKDF2), SessionManager (CSPRNG tokens + sliding TTL), UserPreferenceStore (namespaced + callbacks).

### 🔄 Sprint 23 — Notification & Messaging (C79–C81)
NotificationDispatcher, InAppMessageQueue, EmailComposer.

### Sprints 24–33 — Remaining Original Track (C82–C108)
Permission/Policy → Plugin/Extension → AI/LLM Integration → Workflow Engine →
Data Pipeline → Multimodal/Media → Testing Infrastructure → Deployment/DevOps → Integration Adapters.

---

## 🔮 Hermes-Inspired Extension (C109–C120)

> Derived from Hermes agentic framework analysis. See `docs/HERMES_MAPPING.md`.

### Sprint H1 — Agent Identity Layer (C109–C111)
- **C109** `core/soul_loader.py` — Parse + validate `soul.md` persona blueprints
- **C110** `core/agent_identity.py` — Runtime identity object injected into every LLM prompt
- **C111** `core/pantheon_router.py` — Route tasks to named persona+model combos by cost/complexity tier

### Sprint H2 — Memory Vault (C112–C114)
- **C112** `core/memory_vault.py` — Unified `memory.md` + SQLite store with context-injection API
- **C113** `core/context_compressor.py` — LLM-based summarisation + `/compress` command trigger
- **C114** `core/memory_sync_agent.py` — Scheduled push of memory state to GitHub

### Sprint H3 — Operational Controls (C115–C117)
- **C115** `core/command_parser.py` — `/q /background /reset /compress /model /stop` inline parser
- **C116** `core/goal_budget.py` — N-turn constraint loop with budget-exhaustion auto-compress
- **C117** `core/sub_agent_orchestrator.py` — Parallel sub-agents with isolated context windows + result merge

### Sprint H4 — Model & Channel Routing (C118–C120)
- **C118** `core/model_router.py` — Dynamic LLM swap with cost-aware routing + Ollama offline fallback
- **C119** `core/channel_router.py` — Multi-channel adapter: Telegram, Discord, Slack, WhatsApp, Matrix, Web
- **C120** `core/os_action_executor.py` — Sandboxed OS execution with permission gates + audit trail

---

## Design Principles

1. **Zero external deps for core** — every `core/` module runs on stdlib alone
2. **Least privilege** — all agents operate under explicit permission grants
3. **Local-first** — full functionality without cloud; cloud features are additive
4. **Compounding memory** — context stacks across sessions; nothing is lost silently
5. **Model agnostic** — swap any LLM backend without touching business logic
6. **Observable** — every action is logged, audited, and traceable
