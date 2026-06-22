# ShadowRealm — Master Development Plan

> **Living Document** — Last updated: June 22, 2026
> **Branch Strategy:** `dev` = upstream Odysseus sync target | `shadowrealm` = your personal trunk
> **Vision:** A universal, self-learning AI OS for any person, any task — open-source, free, and growing smarter with every interaction.

---

## Table of Contents
1. [Core Vision](#1-core-vision)
2. [Universal Learning Philosophy](#2-universal-learning-philosophy)
3. [Architecture Overview](#3-architecture-overview)
4. [What Already Exists](#4-what-already-exists-audit)
5. [The Missing Layers](#5-the-missing-layers)
6. [MCP Server Build Order](#6-mcp-server-build-order)
7. [Skills System](#7-skills-system)
8. [Agent Modes / Presets](#8-agent-modes--presets)
9. [Memory Architecture](#9-memory-architecture)
10. [Universal Task Learning Engine](#10-universal-task-learning-engine)
11. [Background Automation Jobs](#11-background-automation-jobs)
12. [Phased Roadmap](#12-phased-roadmap)
13. [Industry Protocols to Adopt](#13-industry-protocols-to-adopt)
14. [Open-Source Strategy](#14-open-source-strategy)
15. [Swarm Architecture](#15-swarm-architecture)
16. [File Change Manifest](#16-file-change-manifest)

---

## 1. Core Vision

**ShadowRealm is not an app. It is a living AI operating system.**

It starts as a personal Mission Control for one person — Nathaniel — and grows into an open-source platform that any person on earth can deploy for themselves. A nurse. A contractor. A student. A farmer. A musician. Someone who has never written code. ShadowRealm doesn't require the user to define their world upfront. **It learns their world by watching, asking, and researching** until it can operate as a true partner.

**The core promise:**
> *Give ShadowRealm any task. If it knows how, it does it. If it doesn't, it figures it out — through research, by asking you, or by watching you do it once. It remembers forever. It never asks twice.*

**Three non-negotiables:**
1. **Open and free** — MIT licensed, self-hostable, no cloud lock-in, no subscription
2. **Universal** — designed for any person, any profession, any workflow
3. **Genuinely intelligent** — not a chatbot wrapper. A system that plans, learns, acts, and grows

---

## 2. Universal Learning Philosophy

### The Unknown Task Problem
Every AI system today breaks when asked to do something outside its training or tool set. ShadowRealm's core differentiator is **a three-path resolution system for unknown tasks:**

```
User gives ShadowRealm an unknown task
           │
           ▼
    ┌──────────────────────────────────────┐
    │  RESOLUTION ENGINE                   │
    │                                      │
    │  Path 1: RESEARCH                    │
    │  → deep_research.py                  │
    │  → web_tools.py                      │
    │  → RAG knowledge base                │
    │  → Synthesize procedure, execute     │
    │                                      │
    │  Path 2: ASK                         │
    │  → Identify exactly what's missing   │
    │  → Ask ONE targeted question         │
    │  → Learn from answer                 │
    │  → Store in procedural memory        │
    │  → Never ask again                   │
    │                                      │
    │  Path 3: WATCH                       │
    │  → Activate computer_use_server      │
    │  → Ask user to demonstrate once      │
    │  → Record screen + actions           │
    │  → Synthesize into reusable skill    │
    │  → Store in skills/ library          │
    │  → Execute autonomously next time    │
    └──────────────────────────────────────┘
```

### The Three Learning Loops

**Loop 1 — Explicit Feedback**
User says "that's wrong" or "do it like this instead" → system updates its stored procedure immediately.

**Loop 2 — Implicit Signal**
User edits the agent's output → system logs the delta, clusters patterns over time, updates its skill template for that task type.

**Loop 3 — Observation**
User says "watch me" → computer_use_server records the session → vision model synthesizes steps → new skill file written to `skills/` automatically.

### The Skills Library as a Living Community Asset
Every skill learned by ShadowRealm for one user becomes a **community-contributable skill template** in the open-source repo. Skills are sanitized of personal data and submitted as PRs to `skills/community/`. Over time, ShadowRealm ships with a vast library of human workflows — coding, cooking, accounting, medical admin, legal drafting, farming, music production — contributed by the global user base.

---

## 3. Architecture Overview

```
╔══════════════════════════════════════════════════════════════╗
║                  SHADOWREALM OS  v1.0                        ║
║          The Universal Self-Learning AI Operating System     ║
╠══════════════════════════════════════════════════════════════╣
║  PRESENTATION LAYER                                          ║
║  ├── Web UI (existing Odysseus frontend)                     ║
║  ├── CLI interface                                           ║
║  └── Mobile (future: React Native companion app)            ║
╠══════════════════════════════════════════════════════════════╣
║  ORCHESTRATION LAYER                                         ║
║  ├── ShadowRealm Core (Odysseus engine, src/)               ║
║  ├── AGNO AgentOS control plane (agent runtime)             ║
║  ├── ClawTeam swarm coordinator                             ║
║  └── Universal Task Resolution Engine (NEW)                 ║
╠══════════════════════════════════════════════════════════════╣
║  AGENT SWARM                                                 ║
║  ├── DevAgent      → code, GitHub, builds, ADB              ║
║  ├── ChefAgent     → CulinaryOS, recipes, menus             ║
║  ├── OpsAgent      → Ross Manor, calendar, email            ║
║  ├── ResearchAgent → deep research, web, RAG                ║
║  ├── VisionAgent   → OpenHands computer control             ║
║  ├── MemoryAgent   → Letta stateful learning                ║
║  └── [user-defined agents spawned at runtime]               ║
╠══════════════════════════════════════════════════════════════╣
║  UNIVERSAL TASK LEARNING ENGINE                              ║
║  ├── Path 1: Research (deep_research + web_tools)           ║
║  ├── Path 2: Ask (targeted single-question clarification)   ║
║  └── Path 3: Watch (computer_use + vision synthesis)        ║
╠══════════════════════════════════════════════════════════════╣
║  MODEL ROUTING (teacher_escalation.py)                       ║
║  ├── Qwen3.6-Plus  → MCP-native, repo-level coding         ║
║  ├── Llama 4 Scout → 10M ctx, full codebase in RAM         ║
║  ├── DeepSeek V3   → cheap reasoning, summarization        ║
║  ├── Claude 4      → hard planning, creative synthesis      ║
║  ├── Qwen3.5-Omni  → multimodal (text+image+audio)         ║
║  └── Ollama local  → free tier, privacy-sensitive tasks     ║
╠══════════════════════════════════════════════════════════════╣
║  MCP TOOL LAYER (mcp_servers/)                               ║
║  ├── computer_use  ├── notion      ├── github               ║
║  ├── culinaryos    ├── rossmanor   ├── supabase             ║
║  ├── android_adb   ├── email       ├── memory               ║
║  ├── rag           ├── image_gen   ├── discount_locator     ║
║  └── [community MCP servers — plug and play]                ║
╠══════════════════════════════════════════════════════════════╣
║  SKILLS LIBRARY (skills/)                                    ║
║  ├── dev/      ← coding + software development skills       ║
║  ├── culinary/ ← food + restaurant skills                   ║
║  ├── ops/      ← business operations skills                 ║
║  ├── community/← open-source contributed skill templates    ║
║  └── user/     ← privately learned, gitignored             ║
╠══════════════════════════════════════════════════════════════╣
║  MEMORY STACK                                                ║
║  ├── Working    → src/memory.py (in-session)                ║
║  ├── Episodic   → core/session_manager.py (history)        ║
║  ├── Semantic   → ChromaDB + Notion RAG (knowledge)        ║
║  └── Procedural → Letta (self-editing, persistent, learns) ║
╠══════════════════════════════════════════════════════════════╣
║  PERSISTENCE & STATE                                         ║
║  ├── Supabase   → cloud state + event logs                  ║
║  ├── ChromaDB   → local vector store                        ║
║  └── SQLite     → core/database.py session data            ║
╚══════════════════════════════════════════════════════════════╝
```

### File Structure
```
ShadowRealm/
├── AGENTS.md                              ← Codex for all AI coding agents
├── SHADOWREALM_DEVELOPMENT_PLAN.md        ← This file
├── CONTRIBUTING.md                        ← How to contribute skills + MCP servers
├── docker-compose.shadowrealm.yml         ← One-command self-hosted deploy
├── skills/
│   ├── dev/           ← software development skills
│   ├── culinary/      ← food + restaurant skills
│   ├── ops/           ← business operations skills
│   ├── community/     ← open-source contributed (PR welcome)
│   └── user/          ← private, gitignored
├── mcp_servers/
│   ├── computer_use_server.py             ← screen/mouse/keyboard
│   ├── notion_server.py                   ← Second Brain
│   ├── github_server.py                   ← all repos
│   ├── supabase_server.py                 ← persistence
│   ├── culinaryos_server.py               ← food ops
│   ├── rossmanor_server.py                ← HR/attendance
│   ├── android_studio_server.py           ← mobile dev
│   ├── discount_locator_server.py         ← deal alerts
│   ├── email_server.py                    ← EXISTS
│   ├── memory_server.py                   ← EXISTS
│   ├── image_gen_server.py                ← EXISTS
│   └── rag_server.py                      ← EXISTS
├── src/
│   ├── agent_tools/
│   │   ├── computer_use_tools.py          ← NEW
│   │   ├── task_resolution_engine.py      ← NEW (research/ask/watch router)
│   │   ├── skill_synthesizer.py           ← NEW (watch → skill file)
│   │   ├── filesystem_tools.py            ← EXISTS
│   │   ├── subprocess_tools.py            ← EXISTS
│   │   ├── document_tools.py              ← EXISTS
│   │   ├── web_tools.py                   ← EXISTS
│   │   ├── model_interaction_tools.py     ← EXISTS
│   │   └── session_tools.py               ← EXISTS
│   ├── a2a_coordinator.py                 ← NEW (agent-to-agent)
│   └── [60+ engine files]
└── config/
    └── shadowrealm/
        ├── persona.json                   ← identity seed (gitignored)
        └── presets/
            ├── dev_mode.json
            ├── chef_mode.json
            └── ops_mode.json
```

---

## 4. What Already Exists (Audit)

### Engine (`src/`) — Notable Files
| File | Size | Relevance |
|---|---|---|
| `src/agent_loop.py` | 202KB | Core agent loop — read before extending |
| `src/llm_core.py` | 110KB | Multi-model routing, Ollama + cloud |
| `src/tool_implementations.py` | 198KB | All built-in tool implementations |
| `src/tool_schemas.py` | 85KB | Tool definitions exposed to the LLM |
| `src/task_scheduler.py` | 114KB | Full autonomous task scheduling engine |
| `src/deep_research.py` | 40KB | Multi-source deep research agent |
| `src/memory.py` | 16KB | Working + episodic memory |
| `src/memory_vector.py` | 9KB | Vector memory layer |
| `src/memory_provider.py` | 10KB | Memory provider abstraction |
| `src/chroma_client.py` | 2.3KB | ChromaDB vector store |
| `src/visual_report.py` | 71KB | Visual dashboard/report generation |
| `src/caldav_sync.py` | 30KB | Google Calendar two-way sync |
| `src/webhook_manager.py` | 12KB | Inbound/outbound webhooks |
| `src/bg_jobs.py` | 11KB | Background job runner |
| `src/bg_monitor.py` | 6KB | Job health monitor |
| `src/preset_manager.py` | 7.5KB | Agent persona/tool group presets |
| `src/teacher_escalation.py` | 26KB | Multi-model cost escalation routing |
| `src/integrations.py` | 25KB | Integration registry |
| `src/cookbook_serve_lifecycle.py` | 9KB | CulinaryOS-ready: recipe serving lifecycle |
| `src/mcp_manager.py` | 29KB | MCP server registration + management |
| `src/event_bus.py` | 4KB | Internal event pub/sub |
| `src/context_compactor.py` | 19KB | Context window compression |

### Agent Tools (`src/agent_tools/`)
| File | What It Provides |
|---|---|
| `filesystem_tools.py` | Read, write, navigate disk files |
| `subprocess_tools.py` | Shell command execution, terminal |
| `document_tools.py` | Parse + generate documents |
| `web_tools.py` | Web fetch, scraping, search |
| `model_interaction_tools.py` | Agent → other model calls |
| `session_tools.py` | Session context management |

---

## 5. The Missing Layers

### 5.1 Universal Task Resolution Engine ← MOST IMPORTANT NEW FILE
**File:** `src/agent_tools/task_resolution_engine.py`

This is the core of what makes ShadowRealm universal. When the agent encounters an unknown task it routes through three paths:

```python
class TaskResolutionEngine:
    async def resolve(self, task: str, context: UserContext) -> ExecutionPlan:
        # 1. Check skills library + memory
        if skill := await self.skills_store.lookup(task):
            return ExecutionPlan(skill=skill)

        # 2. Check RAG knowledge base
        if knowledge := await self.rag.query(task):
            return ExecutionPlan(synthesized_from=knowledge)

        # 3. Deep research
        if procedure := await self.deep_research.find_procedure(task):
            skill = await self.skill_synthesizer.from_research(procedure)
            await self.skills_store.save(skill)
            return ExecutionPlan(skill=skill)

        # 4. Ask user (ONE targeted question)
        question = await self.clarification_engine.formulate(task, missing_info)
        answer = await self.ask_user(question)
        skill = await self.skill_synthesizer.from_answer(task, answer)
        await self.skills_store.save(skill)
        return ExecutionPlan(skill=skill)

        # 5. Watch user (last resort, most powerful)
        await self.computer_use.start_observation_mode()
        recording = await self.observe_user_demo(task)
        skill = await self.skill_synthesizer.from_observation(recording)
        await self.skills_store.save(skill)
        return ExecutionPlan(skill=skill)
```

### 5.2 Skill Synthesizer
**File:** `src/agent_tools/skill_synthesizer.py`

Converts raw inputs (research findings, user answers, screen recordings) into structured, reusable skill files in `skills/`. Uses a vision model (Qwen3.5-Omni) to interpret screen recordings and extract step-by-step procedures.

### 5.3 Computer Control
**File:** `src/agent_tools/computer_use_tools.py`
**MCP Wrapper:** `mcp_servers/computer_use_server.py`

Stack: `pyautogui` + `playwright` + `mss` + `pytesseract` + `opencv-python`

Tools: `screenshot()`, `click(x,y)`, `type_text(str)`, `key_press(key)`, `scroll()`, `read_screen()`, `find_element()`, `open_app()`, `browser_navigate()`, `browser_click()`, `browser_fill()`

Alternative (open-source, Docker): **OpenHands** (formerly OpenDevin) — higher accuracy on complex computer tasks, MIT licensed, 40k+ stars.

Benchmark comparison for computer use:
- InfantAgent-Next: 7.27% OSWorld (beats Claude Computer Use)
- OpenHands: strong SWE-Bench score, best for code-heavy computer tasks
- pyautogui native: best for simple, deterministic GUI automation

Use pyautogui for simple tasks. Delegate to OpenHands sub-agent for complex web/GUI sessions.

### 5.4 Procedural Memory (Letta)
The 4th memory type — the system learns *how the user works*.
- Self-editing memory blocks that persist indefinitely
- Never resets between sessions
- Learns: preferred output format, work schedule patterns, project priority order, review preferences
- `pip install letta`
- Integrate via `src/memory_provider.py`

### 5.5 A2A (Agent-to-Agent) Coordination
**File:** `src/a2a_coordinator.py`
Google's open Agent-to-Agent protocol for horizontal agent collaboration.
Sub-agents hand off tasks rather than the orchestrator doing everything.

---

## 6. MCP Server Build Order

| Priority | Server | SDK/API | Unlocks |
|---|---|---|---|
| **1** | `computer_use_server.py` | pyautogui, playwright, mss, pytesseract | Full computer control — watch + act |
| **2** | `notion_server.py` | notion-client | Second Brain in RAG |
| **3** | `github_server.py` | PyGithub / httpx | All repos: PR, issues, CI |
| **4** | `supabase_server.py` | supabase-py | Persistent ShadowRealm state |
| **5** | `culinaryos_server.py` | Internal REST | Recipe, inventory, production |
| **6** | `rossmanor_server.py` | AttendanceOnDemand REST | Kiosk events, attendance, scheduling |
| **7** | `android_studio_server.py` | ADB + subprocess | Build/deploy RecipeOS from chat |
| **8** | `discount_locator_server.py` | Walmart/Flipp APIs | Deal alerts at 10%+ |

---

## 7. Skills System

Skills are markdown procedure files. When ShadowRealm needs to do a task, it loads the relevant skill for battle-tested procedure instead of improvising. Skills can be:
- **Hand-written** by you (best for known workflows)
- **Research-synthesized** (auto-generated from deep_research.py)
- **Answer-synthesized** (generated from one clarification question)
- **Observation-synthesized** (generated from watching you work)
- **Community-contributed** (PR to skills/community/)

### Nathaniel's Initial Skill Library
```
skills/dev/
  new_feature.md         ← branch, scaffold, test, PR
  code_review.md         ← security + perf checklist
  android_component.md   ← Kotlin MVVM, Jetpack Compose
  api_endpoint.md        ← REST structure, auth, validation

skills/culinary/
  recipe_scale.md        ← yield%, unit conversions, equipment constraints
  production_plan.md     ← prep schedule, station assignment, time-backward

skills/ops/
  morning_brief.md       ← 6:15 AM data pull + format
  ross_manor_audit.md    ← attendance check + discrepancy threshold

skills/community/        ← open-source contributed (gitignored until PR)
  README.md              ← how to contribute a skill

skills/user/             ← private, gitignored, learned by observation
```

---

## 8. Agent Modes / Presets

Using `src/preset_manager.py`. Tool groups — never expose all tools at once.

| Mode | Trigger | Active Tools | Active Skills |
|---|---|---|---|
| **Dev** | `@dev` | computer_use, github, filesystem, subprocess, android_adb, notion, web, deep_research | skills/dev/ |
| **Chef** | `@chef` | culinaryos, notion, web, image_gen, deep_research | skills/culinary/ |
| **Ops** | `@ops` | rossmanor, caldav, email, supabase, visual_report, notion | skills/ops/ |
| **Universal** | `@auto` (default) | task_resolution_engine routes dynamically | auto-selects |

**Universal Mode** is the key addition — it uses the Task Resolution Engine to dynamically select the right tool group based on what the task actually requires, rather than the user having to know which mode to switch to.

---

## 9. Memory Architecture

| Layer | Type | Status | Implementation |
|---|---|---|---|
| Working | In-context session | ✅ EXISTS | `src/memory.py` |
| Episodic | Conversation history | ✅ EXISTS | `core/session_manager.py` |
| Semantic | Knowledge base + facts | 🔧 EXTEND | `src/chroma_client.py` + Notion RAG |
| Procedural | Learned work patterns | ❌ MISSING | Letta via `src/memory_provider.py` |

### Procedural Memory — What It Learns Per User
- Preferred output format (bullet vs. prose, verbose vs. concise)
- Wake-time and work-time patterns
- Project priority ordering
- Which tasks to auto-execute vs. ask permission
- Recurring decisions and their outcomes
- Vocabulary, terminology, abbreviations the user uses
- Who they email most and how they prefer to respond

---

## 10. Universal Task Learning Engine

This is the section that defines what ShadowRealm is that nothing else is.

### The Principle
**If ShadowRealm doesn't know how to do something, it never fails silently. It never hallucinates a wrong answer. It resolves the gap and learns.**

### Resolution Priority Order
1. **Skills library hit** — fastest, fully deterministic
2. **Procedural memory hit** — learned from this user before
3. **RAG knowledge base** — from Notion, documents, past research
4. **Deep research** — live web research, synthesize into new skill
5. **Single clarifying question** — ask user for the one missing piece
6. **Observation mode** — "Show me once, I'll do it every time after"

### What Gets Stored After Each Resolution
Every time a task is resolved via paths 3–6, ShadowRealm:
1. Writes a new skill file to `skills/user/[task_slug].md`
2. Updates Letta procedural memory with the user's preference signal
3. Indexes the skill in ChromaDB for fast future lookup
4. Optionally (with permission) sanitizes and submits as PR to `skills/community/`

### The "Watch Me" Protocol
Triggered by user saying "watch me" or "let me show you":
1. `computer_use_server` activates observation mode (screen recording + action log)
2. User performs the task naturally
3. Vision model (Qwen3.5-Omni or InfantAgent) interprets recording
4. `skill_synthesizer.py` structures observations into a repeatable skill
5. Skill is validated with user: "I learned this — is this right?"
6. On confirmation: stored permanently, never needs demonstration again

### Skill Quality Tiers
```
Tier 1 — Gold (hand-written or user-validated observation)
  → Executed with full confidence, no confirmation needed

Tier 2 — Silver (research-synthesized or answer-synthesized)
  → Executed with summary shown first, runs unless user objects

Tier 3 — Bronze (first-time inference, no stored procedure)
  → Full plan shown and approved before execution
  → On success, promoted to Silver automatically
```

---

## 11. Background Automation Jobs

Using `src/bg_jobs.py` + `src/task_scheduler.py`:

| Schedule | Job | Output |
|---|---|---|
| Daily 6:15 AM | Morning brief assembly | PRs, calendar, Notion tasks, Ross Manor flags |
| Daily midnight | CI scan across all repos | GitHub issue if any fail |
| On every git push | Lint + test subprocess | Session notification |
| Weekly Sunday 8 PM | Project health dashboard | visual_report.py output |
| Every 2 hours | Discount locator scan | Alert if 10%+ deal found |
| Daily 11 PM | Attendance digest | Ross Manor daily summary |
| Weekly Monday 6 AM | Weekly ops brief | Schedule, staffing, inventory |
| Monthly | Skill library review | Suggest community PR for top user skills |

---

## 12. Phased Roadmap

### Phase 0 — Foundation *(Week 1)*
- [x] Create `shadowrealm` branch from `dev`
- [x] Write master development plan
- [ ] Write `AGENTS.md` codex
- [ ] Write `config/shadowrealm/persona.json`
- [ ] Rebrand surface strings in `src/constants.py`
- [ ] Override `.env.example`

### Phase 1 — Computer Control *(Week 1-2)*
- [ ] `src/agent_tools/computer_use_tools.py`
- [ ] `mcp_servers/computer_use_server.py`
- [ ] Docker setup for OpenHands sub-agent
- [ ] Test: screenshot → OCR → click loop
- [ ] Test: "watch me" observation mode end-to-end

### Phase 2 — Second Brain Integration *(Week 2)*
- [ ] `mcp_servers/notion_server.py`
- [ ] Connect 7 Notion nodes
- [ ] RAG pipeline into ChromaDB
- [ ] Test: ask about Notion project → correct answer

### Phase 3 — Dev Agent Mode *(Week 3)*
- [ ] `mcp_servers/github_server.py`
- [ ] `mcp_servers/android_studio_server.py`
- [ ] Dev mode preset + skills
- [ ] Test: full dev loop from chat → push PR

### Phase 4 — Business Operations *(Week 4)*
- [ ] `mcp_servers/supabase_server.py`
- [ ] `mcp_servers/culinaryos_server.py`
- [ ] `mcp_servers/rossmanor_server.py`
- [ ] Chef + Ops mode presets + skills

### Phase 5 — Memory + Autonomy *(Week 5-6)*
- [ ] Integrate Letta into `src/memory_provider.py`
- [ ] Wire all background automation jobs
- [ ] A2A coordinator scaffold
- [ ] Morning brief fully operational

### Phase 6 — Universal Task Engine *(Week 7-8)*
- [ ] `src/agent_tools/task_resolution_engine.py`
- [ ] `src/agent_tools/skill_synthesizer.py`
- [ ] Research path (deep_research integration)
- [ ] Ask path (clarification engine)
- [ ] Watch path (observation + vision synthesis)
- [ ] Skill quality tier system
- [ ] Universal mode preset

### Phase 7 — Swarm + Open-Source Graduation *(Month 3)*
- [ ] Integrate AGNO as agent runtime (`pip install agno`)
- [ ] Integrate ClawTeam for swarm orchestration
- [ ] Specialist sub-agents (Dev, Chef, Ops, Research, Vision, Memory)
- [ ] Wire OpenHands as VisionAgent (Docker sub-service)
- [ ] Swap default local model to Qwen3.6-Plus via Ollama (MCP-native)
- [ ] Configure Llama 4 Scout for large-context codebase tasks
- [ ] Configure DeepSeek V3 for cheap reasoning
- [ ] `docker-compose.shadowrealm.yml` for one-command deploy

### Phase 8 — Community + Universal Adoption *(Month 4+)*
- [ ] Publish MCP servers as standalone pip packages
- [ ] `skills/community/` open for PR contributions
- [ ] `CONTRIBUTING.md` with skill contribution guide
- [ ] GitHub Actions CI for public repo
- [ ] Public documentation site
- [ ] `shadowrealm init` CLI wizard for new user onboarding
  - Asks 5 questions about who the user is and what they do
  - Auto-configures persona.json
  - Suggests which MCP servers to enable
  - Sets up first skill library based on profession
- [ ] Skill submission pipeline (user skills → sanitize → community PR)
- [ ] Plugin/extension system for third-party MCP servers

---

## 13. Industry Protocols to Adopt

| Protocol | Source | Purpose | Status |
|---|---|---|---|
| MCP | Anthropic | Agent ↔ Tool communication | ✅ Built-in |
| A2A | Google | Agent ↔ Agent coordination | 🔧 Phase 5 |
| AGENTS.md | Community standard | AI coding agent conventions | 📝 Phase 0 |
| OpenHands API | MIT | Open computer use sub-agent | 🔧 Phase 1 |
| AGNO AgentOS | Apache 2.0 | Agent runtime control plane | 🔧 Phase 7 |
| ClawTeam | MIT | Swarm coordination | 🔧 Phase 7 |
| Planning-first loop | Research | Simulate before execute | 🔧 Phase 6 |
| Tool Groups | Best practice | Accuracy preservation | 🔧 Phase 0 |

---

## 14. Open-Source Strategy

### Philosophy
ShadowRealm is free. No subscription. No cloud lock-in. The value is in the platform and the community — not a paywall.

### What Gets Open-Sourced (MIT License)
- The entire `shadowrealm` platform
- All MCP servers as standalone pip packages
- The Skills library (`skills/community/`)
- `AGENTS.md` template
- `docker-compose.shadowrealm.yml`
- `shadowrealm init` CLI onboarding wizard

### What Stays Private Per Deployment
- `config/shadowrealm/persona.json` (gitignored)
- `skills/user/` (gitignored)
- `.env` (gitignored)
- Any proprietary API credentials

### Community Contribution Model
```
User installs ShadowRealm
  → Uses it, ShadowRealm learns new skills via Watch/Ask/Research
  → System prompts: "I learned how to [task]. Share with community?"
  → User reviews sanitized skill file
  → One-click PR to skills/community/
  → Reviewed + merged → available to all ShadowRealm users next update
```

### The Moat
Not data. Not a model. **The community skill library.**
As more users contribute observed + validated workflows across professions,
ShadowRealm becomes the most capable out-of-the-box AI system for real human work.
No other system is building this. It's an open-source flywheel.

---

## 15. Swarm Architecture

Using AGNO (control plane) + ClawTeam (coordination) + custom specialists:

```
ShadowRealm Orchestrator
       │
       ├── DevAgent
       │     Tools: github, filesystem, subprocess, android_adb, computer_use
       │     Skills: skills/dev/
       │     Model: Qwen3.6-Plus (MCP-native coding)
       │
       ├── ChefAgent
       │     Tools: culinaryos, notion, web, image_gen
       │     Skills: skills/culinary/
       │     Model: Llama 4 Scout (large recipe corpus context)
       │
       ├── OpsAgent
       │     Tools: rossmanor, caldav, email, supabase, visual_report
       │     Skills: skills/ops/
       │     Model: DeepSeek V3 (cheap, reliable for structured tasks)
       │
       ├── ResearchAgent
       │     Tools: deep_research, web_tools, rag_server
       │     Skills: (synthesizes new ones)
       │     Model: Claude 4 (best synthesis + reasoning)
       │
       ├── VisionAgent (OpenHands Docker sub-service)
       │     Tools: computer_use, browser, screenshot, ocr
       │     Skills: observation-synthesized
       │     Model: InfantAgent / Qwen3.5-Omni (vision-native)
       │
       └── MemoryAgent (Letta)
             Tools: memory_server, chroma, supabase
             Function: Persistent learning across all agents
             Always running in background
```

---

## 16. File Change Manifest

### Phase 0 (Now)
```
CREATE: AGENTS.md
CREATE: CONTRIBUTING.md
CREATE: config/shadowrealm/persona.json         ← gitignored
CREATE: config/shadowrealm/presets/dev_mode.json
CREATE: config/shadowrealm/presets/chef_mode.json
CREATE: config/shadowrealm/presets/ops_mode.json
MODIFY: src/constants.py                        ← Odysseus → ShadowRealm strings
MODIFY: README.md                               ← full rewrite
MODIFY: .env.example                            ← provider setup
```

### Phase 1-2
```
CREATE: src/agent_tools/computer_use_tools.py
CREATE: mcp_servers/computer_use_server.py
CREATE: mcp_servers/notion_server.py
CREATE: docker-compose.shadowrealm.yml
MODIFY: src/integrations.py                    ← register new MCP servers
```

### Phase 3-4
```
CREATE: mcp_servers/github_server.py
CREATE: mcp_servers/android_studio_server.py
CREATE: mcp_servers/supabase_server.py
CREATE: mcp_servers/culinaryos_server.py
CREATE: mcp_servers/rossmanor_server.py
CREATE: skills/dev/new_feature.md
CREATE: skills/dev/code_review.md
CREATE: skills/dev/android_component.md
CREATE: skills/dev/api_endpoint.md
CREATE: skills/culinary/recipe_scale.md
CREATE: skills/culinary/production_plan.md
CREATE: skills/ops/morning_brief.md
CREATE: skills/ops/ross_manor_audit.md
CREATE: skills/community/README.md
```

### Phase 5-6
```
CREATE: src/agent_tools/task_resolution_engine.py
CREATE: src/agent_tools/skill_synthesizer.py
CREATE: src/a2a_coordinator.py
MODIFY: src/memory_provider.py                 ← integrate Letta
MODIFY: src/agent_loop.py                      ← planning-first upgrade
```

### Phase 7-8
```
CREATE: mcp_servers/discount_locator_server.py
CREATE: shadowrealm_cli/init.py               ← onboarding wizard
MODIFY: src/integrations.py                   ← register swarm agents
MODIFY: src/teacher_escalation.py             ← add Qwen3.6, Llama 4, DeepSeek V3
```

### Do Not Touch Without Deep Review
```
src/agent_loop.py            ← 202KB core loop
src/llm_core.py              ← 110KB model routing
src/tool_implementations.py  ← 198KB built-in tools
core/database.py             ← 103KB data layer
core/auth.py                 ← 30KB auth system
```

---

## Open Questions

- [ ] **Ross Manor API** — document AttendanceOnDemand endpoints
- [ ] **Notion node IDs** — export 7 database IDs for notion_server.py
- [ ] **Supabase schema** — design tables for state, skill store, event log
- [ ] **Local model stack** — confirm Ollama running + which models installed
- [ ] **Target OS** — Linux/Windows/Mac for pyautogui config
- [ ] **OpenHands Docker** — confirm Docker is available on the host
- [ ] **agent_loop.py review** — planning-first upgrade feasibility
- [ ] **Community skill sanitization** — design PII-scrubbing pipeline before Phase 8
