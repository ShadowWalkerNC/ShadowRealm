# ShadowRealm v2.0 — Master Build Plan

> **Branch:** `shadowrealm-v2` → merges to `dev` → merges to `main` on v2.0.0 tag  
> **Target Score:** 9 / 10  
> **Total Commits:** 94  
> **Total Sprints:** 10  
> **Estimated Duration:** 14–16 weeks solo  
> **Last Updated:** 2026-06-29

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     ShadowRealm UI                          │
│      (Open WebUI base — chat, agents, workspace panels)     │
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
│  (Code sandbox)      │  (GitHub,      │  (System access)    │
│                      │  Notion, Files)│                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│               Skills Engine + SkillRegistry                  │
│                                                             │
│  ShadowCoder │ ShadowResearcher │ ShadowOps │ ShadowMemory  │
│  ShadowCreative │ Custom Agents │ Teach Mode                │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│          Self-Healing + Reflection Engine                    │
│                                                             │
│  Telemetry → DiagnosisEngine → PatchEngine → SkillRegistry  │
│  ReflectionEngine → Proposal Queue → Human Review → Commit  │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│                  5-Tier Memory Layer                         │
│                                                             │
│  Hot (context) → Warm (ChromaDB) → Cool (Notion/Obsidian)  │
│  → Episodic (summaries) → Procedural (skills)               │
└─────────────────────────────────────────────────────────────┘
```

---

## Design Rules (Never Break These)

1. **One framework per pipeline type** — LangGraph=Research, AutoGen=Coding, CrewAI=Scheduled. Never mixed.
2. **One commit per task** — atomic, reversible, readable git history.
3. **Never build on unstable ground** — each sprint must be stable before the next begins.
4. **CSS cleanup before any UI work** — Sprint 3 must complete before Sprint 4 starts.
5. **Skills engine before self-healing** — SkillRegistry must exist before the PatchEngine can write to it.
6. **Token compression before memory expansion** — Sprint 2 before Sprint 5.
7. **Fix only the error** — PatchEngine constraint; never rewrite working code alongside broken code.
8. **Every MCP server is a skill** — existing `email_server.py`, `memory_server.py`, `rag_server.py`, `image_gen_server.py` auto-register at startup.
9. **All agents read/write the same memory layer** — no siloed memory per agent.
10. **Self-healing is L1→L3 for v2.0, L4→L5 for v2.1** — ship monitor+diagnose+patch-with-approval first.

---

## Self-Healing Maturity Ladder

| Level | Capability | Target Version |
|---|---|---|
| L1 — Monitor | Detects failures, alerts human | v2.0 |
| L2 — Diagnose | Classifies root cause, shows fix | v2.0 |
| L3 — Patch with approval | Generates fix, human approves before commit | v2.0 |
| L4 — Auto-patch low-risk | Auto-commits known safe error type fixes | v2.1 |
| L5 — Reflect and improve | Proactively rewrites skills to be better | v2.1 |

---

## Complete Commit Checklist

### SPRINT 1 — Foundation Stabilization
> Goal: Any developer can clone and run in under 10 minutes. No video needed.
> Dependency: None. Start here.

- [x] **C01** `fix: audit all integrations — docs/STATUS.md with working/broken/untested per service` ✅ DONE
- [x] **C02** `docs: update .env.example — ShadowRealm branding, quick-reference header, all provider stubs` ✅ DONE
- [ ] **C03** `fix: improve degraded-state reporting — ChromaDB, SearXNG, email, ntfy show clear error UI`
- [ ] **C04** `fix: dead code pass — remove stale routes, feature flags, and unreachable UI states`
- [ ] **C05** `feat: add GET /api/status health endpoint — JSON response, green/yellow/red per service`
- [ ] **C06** `feat: add /status UI page — visual dashboard of all service states at startup`
- [ ] **C07** `feat: create setup.sh — OS-detect, dependency install, interactive .env builder, launch`
- [ ] **C08** `docs: update AGENTS.md — full project identity, stack, active agents, phase context`

---

### SPRINT 2 — Token & Context Compression
> Goal: Never hit a context wall. Agent mode works on small local models.
> Dependency: Sprint 1 complete. Hooks into core/middleware.py.

- [ ] **C09** `feat: add TokenCounter utility — tracks usage per session, per skill, per MCP call`
- [ ] **C10** `feat: add context size profiles — auto-detect model window, select small/medium/large profile`
- [ ] **C11** `feat: slim MCP tool injection — only surface tools relevant to current task, not all tools`
- [ ] **C12** `feat: implement auto-compaction — summarize conversation at 80% context threshold via FastAPI middleware`
- [ ] **C13** `feat: integrate LLMLingua prompt compression — runs before every outbound API call`
- [ ] **C14** `feat: add token usage panel — live display of tokens used, compression savings, estimated cost`

---

### SPRINT 3 — CSS & UI Architecture Cleanup
> Goal: Clean, documented, modular CSS. Required before any visual work.
> Dependency: Sprint 1 complete. MUST finish before Sprint 4.

- [ ] **C15** `refactor: audit static/style.css — map all sections, mark dead rules, add section headers`
- [ ] **C16** `refactor: extract CSS into logical partials — layout.css, components.css, themes.css, utilities.css`
- [ ] **C17** `fix: modal and window positioning — repair fragile popup/dropdown/fixed-position behavior`
- [ ] **C18** `fix: mobile media override audit — comment and pair all desktop/mobile selector rules`
- [ ] **C19** `refactor: promote tour-core.js helper — eliminate copy-pasted onboarding scaffolding`
- [ ] **C20** `fix: accessibility pass — keyboard nav, focus states, color contrast, reduced-motion support`

---

### SPRINT 4 — ShadowRealm Visual Identity
> Goal: Looks and feels like ShadowRealm. Nothing resembles vanilla Open WebUI.
> Dependency: Sprint 3 complete.

- [ ] **C21** `style: define design tokens — all colors, typography, spacing as CSS custom properties`
- [ ] **C22** `style: apply ShadowRealm palette — #0D0D0F base, #7B5CF0 primary, #00E5FF active states`
- [ ] **C23** `style: set global typography — JetBrains Mono for code panels, Inter for all UI chrome`
- [ ] **C24** `feat: build 3-panel IDE layout mode — file tree (left), agent chat (center), preview+terminal (right)`
- [ ] **C25** `style: redesign sidebar — project switcher, memory tier indicator, active agent status badges`
- [ ] **C26** `style: add motion and feedback layer — token streaming animation, save confirms, loading states`
- [ ] **C27** `style: replace all upstream Odysseus images in docs/ with ShadowRealm branded assets`

---

### SPRINT 5 — 5-Tier Memory System
> Goal: The AI knows you, your projects, and your history — intelligently and cheaply.
> Dependency: Sprint 2 complete (compression needed before expanding memory).

- [ ] **C28** `feat: scaffold 5-tier memory architecture — hot / warm / cool / episodic / procedural layers`
- [ ] **C29** `feat: integrate mem0 as orchestration layer over existing memory_server.py and ChromaDB`
- [ ] **C30** `feat: add per-project memory namespacing — isolate context per repo/workspace, no cross-bleed`
- [ ] **C31** `feat: build episodic summarizer — auto-generates session recap stored on conversation close`
- [ ] **C32** `feat: build Notion MCP server — live-sync Notion pages as cool-tier indexed memory`
- [ ] **C33** `feat: build Obsidian vault integration — index local vault folder as searchable knowledge base`
- [ ] **C34** `feat: add memory import tool — JSON import from Claude, ChatGPT, or custom format`
- [ ] **C35** `feat: add memory tier visualizer — UI panel showing what is stored at each tier`

---

### SPRINT 6 — Developer Power Layer
> Goal: Full coding workspace. Open Hands as the coding runtime engine.
> Dependency: Sprint 4 complete (3-panel layout needed for dev panels).

- [ ] **C36** `feat: add open-hands service to docker-compose.yml — sandboxed autonomous coding agent`
- [ ] **C37** `feat: embed Open Hands iframe in 3-panel IDE layout as the right-side dev panel`
- [ ] **C38** `feat: embed xterm.js terminal panel — full bash/shell command execution in-browser`
- [ ] **C39** `feat: add live preview pane — spawns local dev server subprocess, renders output in iframe`
- [ ] **C40** `feat: add auto-refresh on file save to live preview pane`
- [ ] **C41** `feat: integrate browser-use library — AI agent browser control and DOM analysis capability`
- [ ] **C42** `feat: add file tree panel — open/edit/create/delete files via MCP filesystem server`
- [ ] **C43** `feat: pre-wire dev MCP bundle — GitHub, filesystem, browser-use, Notion all active at onboarding`

---

### SPRINT 6B — Agent Pipeline Layer
> Goal: Real multi-agent orchestration. Three frameworks, one router, one memory layer.
> Dependency: Sprint 5 (memory) and Sprint 6 (execution runtime) complete.

- [ ] **C44** `feat: scaffold Task Router — classifies incoming requests to correct pipeline (research/coding/scheduled)`
- [ ] **C45** `feat: integrate LangGraph — research pipeline (query → search → read → summarize → memory_write → report)`
- [ ] **C46** `feat: integrate AutoGen — coding pipeline (planner → coder → tester → reviewer → deployer)`
- [ ] **C47** `feat: integrate CrewAI — scheduled pipeline (watcher → analyzer → notifier)`
- [ ] **C48** `feat: build Pipeline Monitor UI — live Kanban board showing all active agent tasks and state`
- [ ] **C49** `feat: wire all pipelines to 5-tier memory layer — every agent reads and writes same store`
- [ ] **C50** `feat: wire all pipelines to Open Hands execution runtime for code tasks`
- [ ] **C51** `test: add pipeline integration tests — verify Task Router correctly dispatches all three types`

---

### SPRINT 7 — Skills Engine
> Goal: Custom skills, agent assignment, multi-skill parallel execution, skill stacking.
> Dependency: Sprint 6B (pipelines) complete. This is the biggest sprint.

**Schema & Registry:**
- [ ] **C52** `feat: define Skill schema — name, version, trigger, tools[], memory_scope, pipeline, agent_id, tags`
- [ ] **C53** `feat: build SkillRegistry — central versioned store, queryable by agent, tag, pipeline, or status`
- [ ] **C54** `feat: build Skill executor — runs a skill, injects correct tools, respects memory scope and token budget`
- [ ] **C55** `feat: add multi-skill parallel execution — run N skills simultaneously with shared memory write lock`
- [ ] **C56** `feat: add skill stacking — define chains where output of skill A feeds input of skill B`
- [ ] **C57** `feat: wire all existing MCP servers as auto-registered skills at startup`

**Agent Bots:**
- [ ] **C58** `feat: create ShadowCoder agent — skills: code_write, code_review, test_run, deploy, git_ops`
- [ ] **C59** `feat: create ShadowResearcher agent — skills: web_search, source_read, summarize, memory_write, report_gen`
- [ ] **C60** `feat: create ShadowOps agent — skills: shell_exec, file_manage, service_monitor, cron_schedule`
- [ ] **C61** `feat: create ShadowMemory agent — skills: memory_ingest, memory_compress, memory_retrieve, knowledge_sync`
- [ ] **C62** `feat: create ShadowCreative agent — skills: image_gen, image_edit, doc_write, content_draft`
- [ ] **C63** `feat: build Agent Orchestrator — routes tasks to correct bot, supports multi-agent collaboration`

**Skill UI:**
- [ ] **C64** `feat: build Skill Library panel — browse skills by agent, tag, pipeline, or execution status`
- [ ] **C65** `feat: build custom skill builder UI — create skills via form, no code required`
- [ ] **C66** `feat: build skill-to-agent assignment UI — drag/drop skills onto agent cards`
- [ ] **C67** `feat: add skill import/export — JSON format, shareable between ShadowRealm instances`

**Teach Mode:**
- [ ] **C68** `feat: scaffold Teach Mode toggle — activates AI observation and clarification Q&A layer`
- [ ] **C69** `feat: build DOM/page analysis pipeline — AI reads and maps structure of any active webpage`
- [ ] **C70** `feat: build interaction capture — records user workflow steps with AI annotation`
- [ ] **C71** `feat: implement Teach Mode clarification Q&A — AI asks what actions mean in real time`
- [ ] **C72** `feat: store Teach Mode learnings as versioned procedural skills in SkillRegistry`

---

### SPRINT 7B — Self-Healing & Reflection Engine
> Goal: The workspace detects broken skills, fixes them, and improves itself over time.
> Dependency: Sprint 7 (SkillRegistry + telemetry hooks) complete.

**Telemetry Foundation:**
- [ ] **C73** `feat: add skill execution telemetry — log every run to skill_traces table (name, agent, tokens, duration, success, error_type, prompt, response)`
- [ ] **C74** `feat: add query_traces MCP tool — agents can query their own execution history programmatically`
- [ ] **C75** `feat: add trace dashboard — per-skill success rate, avg latency, token cost, error breakdown`

**Reactive Self-Healing (L1–L3):**
- [ ] **C76** `feat: build SkillHealthMonitor — watches skill_traces, flags skills with 2+ consecutive failures`
- [ ] **C77** `feat: build DiagnosisEngine — classifies failure type: tool_fail / overflow / hallucination / dependency / malformed_output`
- [ ] **C78** `feat: build PatchEngine — generates constrained fix (fix only the error), versions patch, writes to SkillRegistry`
- [ ] **C79** `feat: add patch idempotency marker — prevents double-patching same failure instance`
- [ ] **C80** `feat: add skill quarantine — disables skill after 5 failed patch attempts, alerts human`
- [ ] **C81** `feat: add patch rollback — one-click revert to any previous skill version`
- [ ] **C82** `feat: add self-healing review UI — shows diagnosis, proposed patch, approve/reject/rollback controls`

**Proactive Reflection (L4–L5, target v2.1 — scaffold now):**
- [ ] **C83** `feat: build ReflectionEngine — nightly job reads 24h traces, identifies underperforming patterns`
- [ ] **C84** `feat: add improvement proposal queue — reflection generates structured skill diffs for review`
- [ ] **C85** `feat: add proposal review UI — approve/reject/modify before commit to SkillRegistry`
- [ ] **C86** `feat: add learning mode toggle — when active, reflection runs continuously not just nightly`

---

### SPRINT 8 — Onboarding Wizard
> Goal: Zero-to-productive in under 10 minutes. No documentation needed.
> Dependency: Sprint 7 complete (quiz wires to skill assignments and agent activation).

- [ ] **C87** `feat: first-run detection — triggers wizard on fresh install, gracefully skippable`
- [ ] **C88** `feat: build onboarding quiz — 15 questions: stack, goals, languages, hardware, preferred model`
- [ ] **C89** `feat: wire quiz results to system prompt personalization and default model selection`
- [ ] **C90** `feat: wire quiz results to default agent skill assignments and active bot selection`
- [ ] **C91** `feat: API key setup step — guided entry with live test-connection button per provider`
- [ ] **C92** `feat: memory import step — import from Claude/ChatGPT JSON, Notion, or Obsidian`
- [ ] **C93** `feat: agent activation step — choose which bots to enable, preview their skill sets`
- [ ] **C94** `feat: no-token-required path — full local Ollama setup option with model recommendations by hardware`
- [ ] **C95** `docs: write ONBOARDING.md — full wizard flow, customization options, skip paths`

---

### SPRINT 9 — Analytics, QA & Ship
> Goal: Full observability. Every rough edge smoothed. v2.0.0 tagged and merged.
> Dependency: All previous sprints complete.

- [ ] **C96** `feat: integrate self-hosted PostHog — session tracking, event analytics, funnel views`
- [ ] **C97** `feat: build analytics dashboard — token usage, model perf, session stats, cost estimates`
- [ ] **C98** `feat: add skill execution analytics — most-used skills, failure rates, token cost per skill`
- [ ] **C99** `feat: add Grafana + Prometheus to docker-compose.yml — system-level metrics and alerting`
- [ ] **C100** `fix: full QA pass — smoke test every sprint deliverable end-to-end`
- [ ] **C101** `fix: cross-platform test — verify Docker, native Python, Windows, macOS all pass`
- [ ] **C102** `style: final polish pass — spacing, alignment, responsive layout, all edge cases`
- [ ] **C103** `docs: finalize README, STATUS.md, ONBOARDING.md, ROADMAP.md, CHANGELOG.md, AGENTS.md`
- [ ] **C104** `chore: tag v2.0.0 — merge shadowrealm-v2 → dev → main`

---

## Sprint Summary

| Sprint | Focus | Commits | Est. Time |
|---|---|---|---|
| 1 | Foundation stabilization | C01–C08 | 1 week |
| 2 | Token & context compression | C09–C14 | 1 week |
| 3 | CSS cleanup | C15–C20 | 1 week |
| 4 | Visual identity | C21–C27 | 1 week |
| 5 | 5-tier memory system | C28–C35 | 2 weeks |
| 6 | Developer power layer | C36–C43 | 1.5 weeks |
| 6B | Agent pipeline layer | C44–C51 | 2 weeks |
| 7 | Skills engine + agent bots | C52–C72 | 3 weeks |
| 7B | Self-healing + reflection | C73–C86 | 2 weeks |
| 8 | Onboarding wizard | C87–C95 | 1.5 weeks |
| 9 | Analytics, QA, ship | C96–C104 | 1 week |
| **Total** | | **104 commits** | **~17 weeks** |

---

## Branch Strategy

```
main              ← stable releases only (v2.0.0 tag here)
  └── dev         ← integration branch, sprint merges land here
        └── shadowrealm-v2  ← all development work
```

Merge `shadowrealm-v2` → `dev` at end of each sprint.  
Merge `dev` → `main` only on C104 v2.0.0 tag.

---

## Current Progress

- [x] C01 — STATUS.md integration audit
- [x] C02 — .env.example branding + quick reference
- [ ] C03 — Next up

*This file is the single source of truth. Update the checklist as commits land.*
