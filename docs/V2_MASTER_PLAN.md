# ShadowRealm v2.0 — Master Build Plan

> **Branch:** `shadowrealm-v2` → merges to `dev` → merges to `main` on v2.0.0 tag
> **Target Score:** 9 / 10
> **Total Commits:** 92
> **Total Sprints:** 10
> **Estimated Duration:** 10–11 weeks solo
> **Last Updated:** 2026-06-29
> **Audit Date:** 2026-06-29 — full codebase read, plan rebuilt from source truth

---

## What's Already Shipped (Pre-Plan)

A full read of `dev` revealed these were already production-grade before v2 planning began:

| System | File | Status |
|---|---|---|
| Skills Engine (CRUD, versioning, slash-invoke, search) | `routes/skills_routes.py` (77KB) | ✅ Shipped |
| LLM-as-judge skill test runner | `routes/skills_routes.py` | ✅ Shipped |
| Self-edit + retry on failing skills | `routes/skills_routes.py` | ✅ Shipped |
| Teacher model escalation | `routes/skills_routes.py` | ✅ Shipped |
| Necessity + redundancy checker | `routes/skills_routes.py` | ✅ Shipped |
| Retrieval precision auditor | `routes/skills_routes.py` | ✅ Shipped |
| Nightly scheduled skill audit | `routes/skills_routes.py` | ✅ Shipped |
| Auto-publish policy + confidence scoring | `routes/skills_routes.py` | ✅ Shipped |
| Degraded-state health reporting | `src/service_health.py` | ✅ Shipped |
| GET /api/diagnostics/services endpoint | `routes/diagnostics_routes.py` | ✅ Shipped |
| Shell execution backend | `routes/shell_routes.py` (74KB) | ✅ Shipped |
| Codex/coding route | `routes/codex_routes.py` (43KB) | ✅ Shipped |
| Webhook ingestion | `routes/webhook_routes.py` | ✅ Shipped |
| Secrets vault | `routes/vault_routes.py` | ✅ Shipped |
| MCP protocol + servers (email, memory, RAG, image_gen) | `routes/mcp_routes.py` | ✅ Shipped |
| Security middleware + CSP + internal tool token | `core/middleware.py` | ✅ Shipped |
| Multi-model compare | `routes/compare_routes.py` | ✅ Shipped |
| Research pipeline sub-module | `routes/research/` | ✅ Shipped |

This collapses Sprint 7 from a 3-week build to a 4–5 day UI + agent-bot wiring sprint.
Sprint 7B self-healing is ~60% done. Total timeline drops from 17 weeks to 10–11 weeks.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     ShadowRealm UI                          │
│   (IDE layout: file tree / agent chat / preview+terminal)   │
└───────────────────────┬─────────────────────────────────────┘
                        │ MCP Protocol
┌───────────────────────▼─────────────────────────────────────┐
│                 Agent Orchestration Layer                    │
│                                                             │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────┐  │
│  │  LangGraph  │   │   AutoGen    │   │     CrewAI       │  │
│  │ (Research)  │   │  (Coding)    │   │  (Scheduled)     │  │
│  └──────┬──────┘   └──────┬───────┘   └────────┬─────────┘  │
│         └─────────────────┼────────────────────┘            │
│                      Task Router                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                   Execution Layer                            │
│                                                             │
│  Open Hands Runtime  │  MCP Servers   │  Shell / Bash       │
│  (Code sandbox)      │  (GitHub,      │  ✅ shell_routes.py  │
│                      │  Notion, Files)│                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│          Skills Engine ✅ ALREADY RUNNING                    │
│                                                             │
│  SkillsManager │ LLM-as-judge │ Self-edit+retry │ Nightly   │
│  Teacher model │ Necessity check │ Retrieval audit │ Audit  │
│  Slash-invoke  │ Built-in overrides │ URL import           │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│      Self-Healing + Reflection Engine (~60% shipped)         │
│                                                             │
│  ✅ Test runner → ✅ Judge → ✅ Self-edit → ✅ Teacher       │
│  🔲 Telemetry table → 🔲 Trace dashboard → 🔲 Proposal UI   │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  5-Tier Memory Layer                         │
│                                                             │
│  Hot (context) → Warm (ChromaDB ✅) → Cool (Notion/Obsidian)│
│  → Episodic (summaries) → Procedural (skills ✅)            │
└─────────────────────────────────────────────────────────────┘
```

---

## Design Rules (Never Break These)

1. **One framework per pipeline type** — LangGraph=Research, AutoGen=Coding, CrewAI=Scheduled. Never mixed.
2. **One commit per task** — atomic, reversible, readable git history.
3. **Never build on unstable ground** — each sprint must be stable before the next begins.
4. **CSS cleanup before any UI work** — Sprint 3 must complete before Sprint 4 starts.
5. **Skills engine is already running** — do not replace it, extend it.
6. **Token compression before memory expansion** — Sprint 2 before Sprint 5.
7. **Fix only the error** — PatchEngine constraint; never rewrite working code alongside broken code.
8. **Every MCP server is a skill** — existing `email_server.py`, `memory_server.py`, `rag_server.py`, `image_gen_server.py` auto-register at startup.
9. **All agents read/write the same memory layer** — no siloed memory per agent.
10. **Self-healing is L1→L3 for v2.0, L4→L5 for v2.1** — ship monitor+diagnose+patch-with-approval first.

---

## Self-Healing Maturity Ladder

| Level | Capability | Status |
|---|---|---|
| L1 — Monitor | Detects failures, alerts human | ✅ Shipped (SkillHealthMonitor in skills_routes.py) |
| L2 — Diagnose | Classifies root cause, shows fix | ✅ Shipped (LLM judge + issue list) |
| L3 — Patch with approval | Self-edit + teacher escalation + human review | ✅ Shipped (needs review UI) |
| L4 — Auto-patch low-risk | Auto-commits known safe error type fixes | 🔲 v2.1 scaffold in Sprint 7B |
| L5 — Reflect and improve | Proactively rewrites skills to be better | 🔲 v2.1 scaffold in Sprint 7B |

---

## Complete Commit Checklist

### SPRINT 1 — Foundation Stabilization
> Goal: Any developer can clone and run in under 10 minutes. No video needed.
> Dependency: None. Start here.

- [x] **C01** `fix: audit all integrations — docs/STATUS.md` ✅ DONE
- [x] **C02** `docs: update .env.example — ShadowRealm branding + quick-reference` ✅ DONE
- [x] **C03** `feat: degraded-state reporting` ✅ ALREADY SHIPPED — `src/service_health.py` (bounded concurrent probes, secret scrubbing, ChromaDB/SearXNG/email/ntfy/providers)
- [x] **C05** `feat: GET /api/diagnostics/services health endpoint` ✅ ALREADY SHIPPED — JSON `{overall, services[], timestamp}`
- [ ] **C04** `fix: dead code pass — audit chatgpt_subscription_routes.py, copilot_routes.py, device_flow.py, stale feature flags`
- [ ] **C06** `feat: /status UI page — wire to existing /api/diagnostics/services`
- [ ] **C07** `feat: setup.sh — OS-detect, dep install, .env builder, launch`
- [ ] **C08** `docs: update AGENTS.md — full ShadowRealm identity, stack, active agents, phase context`

---

### SPRINT 2 — Token & Context Compression
> Goal: Never hit a context wall. Agent mode works on small local models.
> Dependency: Sprint 1 complete. Hooks into existing core/middleware.py.

- [ ] **C09** `feat: TokenCounter utility — tracks usage per session, per skill, per MCP call`
- [ ] **C10** `feat: context size profiles — auto-detect model window, select small/medium/large profile`
- [ ] **C11** `feat: slim MCP tool injection — only surface tools relevant to current task`
- [ ] **C12** `feat: auto-compaction at 80% context threshold — summarize via FastAPI middleware`
- [ ] **C13** `feat: LLMLingua compression middleware — runs before every outbound API call`
- [ ] **C14** `feat: token usage panel — live tokens used, compression savings, estimated cost`

---

### SPRINT 3 — CSS & UI Architecture Cleanup
> Goal: Clean, documented, modular CSS. Required before any visual work.
> Dependency: Sprint 1 complete. MUST finish before Sprint 4.

- [ ] **C15** `refactor: audit static/style.css — map all sections, mark dead rules, add headers`
- [ ] **C16** `refactor: extract CSS partials — layout.css, components.css, themes.css, utilities.css`
- [ ] **C17** `fix: modal and window positioning`
- [ ] **C18** `fix: mobile media override audit — comment and pair all desktop/mobile selectors`
- [ ] **C19** `refactor: promote tour-core.js helper — eliminate copy-pasted onboarding scaffolding`
- [ ] **C20** `fix: accessibility pass — keyboard nav, focus states, color contrast, reduced-motion`

---

### SPRINT 4 — ShadowRealm Visual Identity
> Goal: Looks and feels like ShadowRealm. Nothing resembles vanilla Odysseus.
> Dependency: Sprint 3 complete.

- [ ] **C21** `style: design tokens — all colors, typography, spacing as CSS custom properties`
- [ ] **C22** `style: ShadowRealm palette — #0D0D0F base / #7B5CF0 primary / #00E5FF active`
- [ ] **C23** `style: typography — JetBrains Mono for code panels, Inter for UI chrome`
- [ ] **C24** `feat: 3-panel IDE layout — file tree (left) / agent chat (center) / preview+terminal (right)`
- [ ] **C25** `style: redesign sidebar — project switcher, memory tier indicator, agent status badges`
- [ ] **C26** `style: motion + feedback layer — streaming animation, save confirms, loading states`
- [ ] **C27** `style: replace all upstream Odysseus images with ShadowRealm branded assets`

---

### SPRINT 5 — 5-Tier Memory System
> Goal: The AI knows you, your projects, and your history — intelligently and cheaply.
> Dependency: Sprint 2 complete (compression needed before expanding memory).

- [ ] **C28** `feat: scaffold 5-tier memory — hot / warm / cool / episodic / procedural layers`
- [ ] **C29** `feat: integrate mem0 over existing memory_server.py + ChromaDB`
- [ ] **C30** `feat: per-project memory namespacing — isolate context per repo/workspace`
- [ ] **C31** `feat: episodic summarizer — auto-generates session recap on conversation close`
- [ ] **C32** `feat: Notion MCP server — live-sync Notion pages as cool-tier indexed memory`
- [ ] **C33** `feat: Obsidian vault integration — index local vault folder as searchable knowledge`
- [ ] **C34** `feat: memory import — JSON from Claude, ChatGPT, or custom format`
- [ ] **C35** `feat: memory tier visualizer panel — UI showing what is stored at each tier`

---

### SPRINT 6 — Developer Power Layer
> Goal: Full coding workspace. Open Hands as the runtime engine.
> Dependency: Sprint 4 complete (3-panel layout needed). Shell backend already exists.

- [ ] **C36** `feat: add open-hands service to docker-compose.yml`
- [ ] **C37** `feat: embed Open Hands iframe in 3-panel IDE layout`
- [ ] **C38** `feat: xterm.js terminal panel — wire to existing shell_routes.py backend`
- [ ] **C39** `feat: live preview pane — subprocess dev server, renders in iframe`
- [ ] **C40** `feat: auto-refresh preview on file save`
- [ ] **C41** `feat: browser-use integration — AI agent browser control + DOM analysis`
- [ ] **C42** `feat: file tree panel — open/edit/create/delete via MCP filesystem server`
- [ ] **C43** `feat: pre-wire dev MCP bundle at onboarding — GitHub, filesystem, browser-use, Notion`

---

### SPRINT 6B — Agent Pipeline Layer
> Goal: Real multi-agent orchestration. Three frameworks, one router, one memory layer.
> Dependency: Sprint 5 (memory) and Sprint 6 (execution) complete.

- [ ] **C44** `feat: Task Router — classifies requests to research / coding / scheduled pipeline`
- [ ] **C45** `feat: LangGraph research pipeline — query → search → read → summarize → memory_write → report`
- [ ] **C46** `feat: AutoGen coding pipeline — planner → coder → tester → reviewer → deployer`
- [ ] **C47** `feat: CrewAI scheduled pipeline — watcher → analyzer → notifier`
- [ ] **C48** `feat: Pipeline Monitor UI — live Kanban of all active agent tasks + state`
- [ ] **C49** `feat: wire all pipelines to 5-tier memory layer`
- [ ] **C50** `feat: wire all pipelines to Open Hands execution runtime`
- [ ] **C51** `test: pipeline integration tests — verify Task Router dispatches all three types`

---

### SPRINT 7 — Skills Layer Completion
> Goal: Surface and extend what's already running. Add agent bots + UI panels + Teach Mode.
> Dependency: Sprint 6B (pipelines) complete.
> NOTE: Skills engine, LLM-as-judge, self-edit, teacher escalation, nightly audit — ALL ALREADY SHIPPED.
> This sprint is UI wiring + agent persona definition + Teach Mode only.

**Agent Bots — define named personas with skill sets:**
- [ ] **C52** `feat: ShadowCoder — code_write, code_review, test_run, deploy, git_ops`
- [ ] **C53** `feat: ShadowResearcher — web_search, source_read, summarize, memory_write, report_gen`
- [ ] **C54** `feat: ShadowOps — shell_exec, file_manage, service_monitor, cron_schedule`
- [ ] **C55** `feat: ShadowMemory — memory_ingest, memory_compress, memory_retrieve, knowledge_sync`
- [ ] **C56** `feat: ShadowCreative — image_gen, image_edit, doc_write, content_draft`
- [ ] **C57** `feat: Agent Orchestrator — routes to correct bot, multi-agent collaboration`

**Skills UI — surface what's already running:**
- [ ] **C58** `feat: Skill Library panel — browse by agent / tag / pipeline / audit status`
- [ ] **C59** `feat: custom skill builder UI — no-code form wired to existing /api/skills/add`
- [ ] **C60** `feat: skill-to-agent assignment UI — drag/drop onto agent cards`
- [ ] **C61** `feat: skill import/export UI — JSON + skills.sh URL import (backend exists)`

**Teach Mode:**
- [ ] **C62** `feat: Teach Mode toggle — activates AI observation layer`
- [ ] **C63** `feat: DOM/page analysis pipeline`
- [ ] **C64** `feat: interaction capture — records workflow steps with AI annotation`
- [ ] **C65** `feat: Teach Mode Q&A — AI asks what each action means in real time`
- [ ] **C66** `feat: store Teach Mode learnings as versioned procedural skills — wires to existing SkillsManager`

---

### SPRINT 7B — Self-Healing Completion + Reflection Scaffold
> Goal: Complete the 40% of self-healing that isn't shipped yet. Scaffold v2.1 reflection tier.
> Dependency: Sprint 7 complete. Already shipped: test runner, judge, self-edit, teacher escalation, nightly audit.

**Telemetry (not yet shipped):**
- [ ] **C67** `feat: skill_traces table — log every execution (name, agent, tokens, latency, error_type, prompt, response)`
- [ ] **C68** `feat: query_traces MCP tool — agents query own execution history programmatically`
- [ ] **C69** `feat: trace dashboard — per-skill success rate, avg latency, token cost, error breakdown`

**Review UI (not yet shipped — backend logic exists):**
- [ ] **C70** `feat: self-healing review UI — diagnosis + proposed patch + approve/reject/rollback`
- [ ] **C71** `feat: skill quarantine UI — alerts when skill fails all retries, human review queue`
- [ ] **C72** `feat: patch rollback UI — one-click revert to any previous skill version`

**Proactive Reflection (L4–L5 scaffold for v2.1):**
- [ ] **C73** `feat: ReflectionEngine — nightly job reads 24h traces, identifies underperforming patterns`
- [ ] **C74** `feat: improvement proposal queue — structured skill diffs for human review`
- [ ] **C75** `feat: proposal review UI — approve / reject / modify before SkillRegistry commit`
- [ ] **C76** `feat: learning mode toggle — continuous reflection when active`

---

### SPRINT 8 — Onboarding Wizard
> Goal: Zero-to-productive in under 10 minutes. No documentation required.
> Dependency: Sprint 7 complete (quiz wires to skill assignments and agent activation).

- [ ] **C77** `feat: first-run detection — triggers wizard, gracefully skippable`
- [ ] **C78** `feat: onboarding quiz — stack, goals, languages, hardware, model preference`
- [ ] **C79** `feat: wire quiz to system prompt + default model selection`
- [ ] **C80** `feat: wire quiz to default agent skill assignments + active bot selection`
- [ ] **C81** `feat: API key setup step — guided entry with live test-connection per provider`
- [ ] **C82** `feat: memory import step — Claude / ChatGPT / Notion / Obsidian`
- [ ] **C83** `feat: agent activation step — choose bots, preview skill sets`
- [ ] **C84** `feat: no-token path — full local Ollama setup with model recommendations by hardware`
- [ ] **C85** `docs: ONBOARDING.md`

---

### SPRINT 9 — Analytics, QA & Ship
> Goal: Full observability. Every edge smoothed. v2.0.0 tagged and merged.
> Dependency: All previous sprints complete.

- [ ] **C86** `feat: self-hosted PostHog — session tracking, event analytics, funnel views`
- [ ] **C87** `feat: analytics dashboard — token usage, model perf, session stats, cost estimates`
- [ ] **C88** `feat: skill execution analytics — usage, failure rates, token cost per skill`
- [ ] **C89** `feat: Grafana + Prometheus in docker-compose.yml`
- [ ] **C90** `fix: full QA pass — smoke test every sprint deliverable end-to-end`
- [ ] **C91** `fix: cross-platform test — Docker, native Python, Windows, macOS`
- [ ] **C92** `style: final polish — spacing, alignment, responsive layout, all edge cases`
- [ ] **C93** `docs: finalize README, STATUS.md, ONBOARDING.md, ROADMAP.md, CHANGELOG.md, AGENTS.md`
- [ ] **C94** `chore: tag v2.0.0 — merge shadowrealm-v2 → dev → main`

---

## Sprint Summary

| Sprint | Focus | Commits | Est. Time |
|---|---|---|---|
| 1 | Foundation stabilization | C01–C08 (4 done) | ~3 days remaining |
| 2 | Token & context compression | C09–C14 | ~5 days |
| 3 | CSS cleanup | C15–C20 | ~5 days |
| 4 | Visual identity | C21–C27 | ~5 days |
| 5 | 5-tier memory system | C28–C35 | ~9 days |
| 6 | Developer power layer | C36–C43 | ~7 days |
| 6B | Agent pipeline layer | C44–C51 | ~9 days |
| 7 | Skills UI + agent bots + Teach Mode | C52–C66 | ~4 days |
| 7B | Self-healing completion + reflection | C67–C76 | ~6 days |
| 8 | Onboarding wizard | C77–C85 | ~6 days |
| 9 | Analytics, QA, ship | C86–C94 | ~5 days |
| **Total** | | **94 commits (5 already done)** | **~10–11 weeks** |

---

## Branch Strategy

```
main              ← stable releases only (v2.0.0 tag here)
  └── dev         ← integration branch, sprint merges land here
        └── shadowrealm-v2  ← all development work
```

Merge `shadowrealm-v2` → `dev` at end of each sprint.
Merge `dev` → `main` only on C94 v2.0.0 tag.

---

## Current Progress

- [x] C01 — STATUS.md integration audit ✅
- [x] C02 — .env.example branding + quick reference ✅
- [x] C03 — degraded-state reporting ✅ (was already shipped as src/service_health.py)
- [x] C05 — GET /api/diagnostics/services ✅ (was already shipped)
- [x] V2_MASTER_PLAN.md — this file, rebuilt from source audit ✅
- [ ] **C04 — Next up:** dead code pass on chatgpt_subscription_routes.py, copilot_routes.py, device_flow.py

*This file is the single source of truth. Update the checklist as commits land.*
