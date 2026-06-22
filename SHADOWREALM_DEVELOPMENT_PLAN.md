# ShadowRealm — Master Development Plan

> **Living Document** — Last updated: June 22, 2026  
> **Branch Strategy:** `dev` = upstream Odysseus sync target | `shadowrealm` = your personal trunk  
> **Vision:** A Mission Control AI system unlike anything else — full computer control, multi-agent coordination, deep ecosystem integration across all active projects.

---

## Table of Contents
1. [Project Identity](#1-project-identity)
2. [Architecture Overview](#2-architecture-overview)
3. [What Already Exists](#3-what-already-exists-audit)
4. [The Missing Layers](#4-the-missing-layers)
5. [MCP Server Build Order](#5-mcp-server-build-order)
6. [Skills System](#6-skills-system)
7. [Agent Modes / Presets](#7-agent-modes--presets)
8. [Memory Architecture](#8-memory-architecture)
9. [Background Automation Jobs](#9-background-automation-jobs)
10. [Phased Roadmap](#10-phased-roadmap)
11. [Industry Protocols to Adopt](#11-industry-protocols-to-adopt)
12. [File Change Manifest](#12-file-change-manifest)

---

## 1. Project Identity

**ShadowRealm** is a fork of Odysseus (`pewdiepie-archdaemon/odysseus`, `dev` branch) rebranded and extended into a personal Mission Control AI — a system that knows your full context, controls your computer, writes and deploys your code, manages your restaurant operations, and runs background jobs autonomously.

**Owner:** Nathaniel — Chef-developer, entrepreneur, Bangor Maine  
**Active Projects ShadowRealm must know:**
- `CulinaryOS` — Restaurant management + recipe platform
- `RecipeOS` — Android app (Kotlin), recipe scaling + inventory
- `NexCMS` — Content management system for restaurant/food sites
- `ShadowRealm` — This system (self-aware)
- `Bible Evidence Explorer` — Theological reasoning + knowledge system
- `Discount Locator` — Searches nearby stores for 10%+ discounted items
- `Ross Manor` — AttendanceOnDemand kiosk API integration

**Core Philosophy:**
- Tool Groups per mode — never expose all tools at once (accuracy collapses at scale)
- Planning-first agent loop — simulate before executing
- Procedural memory — the system learns how Nathaniel works, not just what he knows
- Local-first cost optimization — Ollama handles cheap tasks, Claude/GPT-4 handles complex ones

---

## 2. Architecture Overview

```
ShadowRealm
├── AGENTS.md                         ← Codex for all AI coding agents (Claude Code, Gemini, Codex)
├── SHADOWREALM_DEVELOPMENT_PLAN.md   ← This file
├── skills/                           ← Reusable behavioral skill templates
│   ├── dev/
│   │   ├── new_feature.md
│   │   ├── code_review.md
│   │   ├── android_component.md
│   │   └── api_endpoint.md
│   ├── culinary/
│   │   ├── recipe_scale.md
│   │   └── production_plan.md
│   └── ops/
│       ├── morning_brief.md
│       └── ross_manor_audit.md
├── mcp_servers/
│   ├── computer_use_server.py        ← NEW: screen/mouse/keyboard control
│   ├── notion_server.py              ← NEW: 7-node Second Brain as RAG source
│   ├── github_server.py              ← NEW: all repos — PR, issues, CI status
│   ├── supabase_server.py            ← NEW: ShadowRealm persistent state
│   ├── culinaryos_server.py          ← NEW: recipe, inventory, production data
│   ├── rossmanor_server.py           ← NEW: AttendanceOnDemand kiosk API
│   ├── android_studio_server.py      ← NEW: ADB build/deploy/test RecipeOS
│   ├── discount_locator_server.py    ← NEW: deal alerts at 10%+ threshold
│   ├── email_server.py               ← EXISTS (96KB)
│   ├── memory_server.py              ← EXISTS (9.6KB)
│   ├── image_gen_server.py           ← EXISTS (7KB)
│   └── rag_server.py                 ← EXISTS (6.5KB)
├── src/
│   ├── agent_tools/
│   │   ├── computer_use_tools.py     ← NEW: pyautogui + playwright + mss + pytesseract
│   │   ├── filesystem_tools.py       ← EXISTS (19KB)
│   │   ├── subprocess_tools.py       ← EXISTS: shell/terminal execution
│   │   ├── document_tools.py         ← EXISTS (27KB)
│   │   ├── web_tools.py              ← EXISTS
│   │   ├── model_interaction_tools.py← EXISTS
│   │   └── session_tools.py          ← EXISTS (19KB)
│   └── [60+ engine files — do not modify without review]
└── config/shadowrealm/
    ├── persona.json                  ← Identity seed loaded at every session
    └── presets/
        ├── dev_mode.json
        ├── chef_mode.json
        └── ops_mode.json
```

---

## 3. What Already Exists (Audit)

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
| `src/caldav_writeback.py` | 11KB | Calendar write-back |
| `src/webhook_manager.py` | 12KB | Inbound/outbound webhooks |
| `src/bg_jobs.py` | 11KB | Background job runner |
| `src/bg_monitor.py` | 6KB | Job health monitor |
| `src/preset_manager.py` | 7.5KB | Agent persona/tool group presets |
| `src/reminder_personas.py` | 3.6KB | Persona-aware reminders |
| `src/teacher_escalation.py` | 26KB | Multi-model cost escalation routing |
| `src/integrations.py` | 25KB | Integration registry |
| `src/cookbook_serve_lifecycle.py` | 9KB | **CulinaryOS-relevant: recipe serving lifecycle** |
| `src/copilot.py` | 9KB | Copilot mode |
| `src/mcp_manager.py` | 29KB | MCP server registration + management |
| `src/mcp_oauth.py` | 7.4KB | OAuth for MCP servers |
| `src/event_bus.py` | 4KB | Internal event pub/sub |
| `src/context_compactor.py` | 19KB | Context window compression |
| `src/embedding_lanes.py` | 14KB | Embedding pipeline lanes |

### Agent Tools (`src/agent_tools/`)
| File | What It Provides |
|---|---|
| `filesystem_tools.py` | Read, write, navigate disk files |
| `subprocess_tools.py` | Shell command execution, terminal |
| `document_tools.py` | Parse + generate documents |
| `web_tools.py` | Web fetch, scraping, search |
| `model_interaction_tools.py` | Agent → other model calls |
| `session_tools.py` | Session context management |

### MCP Servers (`mcp_servers/`)
| File | What It Provides |
|---|---|
| `email_server.py` | Email read/send |
| `memory_server.py` | Persistent agent memory |
| `rag_server.py` | Retrieval-augmented generation |
| `image_gen_server.py` | Image generation |

---

## 4. The Missing Layers

### 4.1 Computer Control (Highest Priority)
What Claude Computer Use, Google Gemini with Project Mariner, and OpenAI Operator all have:  
**Screen capture + mouse + keyboard control.**

Implementation stack:
- `pyautogui` — cross-platform mouse, keyboard, screenshot
- `playwright` — browser automation (click, fill forms, scrape dynamic pages)
- `mss` — fast multi-screen capture
- `pytesseract` — OCR on screenshots so the agent can *read* what's on screen
- `opencv-python` — screen element detection / template matching

File to create: `src/agent_tools/computer_use_tools.py`  
MCP wrapper: `mcp_servers/computer_use_server.py`

Tools to expose:
```python
screenshot(monitor=0)           # capture current screen
click(x, y, button='left')      # mouse click
double_click(x, y)              # double click
type_text(text, interval=0.05)  # keyboard input
key_press(key)                  # single key (Enter, Tab, Escape, etc.)
scroll(x, y, clicks)            # scroll wheel
read_screen(region=None)        # OCR full screen or region
find_element(template_path)     # find image on screen, return coords
open_app(app_name)              # launch application
browser_navigate(url)           # playwright browser nav
browser_click(selector)         # playwright DOM click
browser_fill(selector, value)   # playwright form fill
browser_screenshot()            # headless browser screenshot
```

### 4.2 Procedural Memory
The 4th memory type — the system learns *how Nathaniel works*, not just facts.
- Learns preferred output format over time
- Learns that 6:30 AM = morning brief mode
- Learns that Ross Manor issues get checked before recipe work
- Learns which repos Nathaniel reviews vs. lets the agent auto-merge

Implementation: integrate **mem0** or **Letta** as a `memory_provider` in `src/memory_provider.py`

### 4.3 A2A (Agent-to-Agent) Coordination
Google's Agent-to-Agent protocol for horizontal agent collaboration.  
Makes CulinaryOS agent, Dev agent, and Ops agent hand off tasks to each other rather than each being isolated.

### 4.4 Skills Layer
See Section 6. A `skills/` directory of markdown prompt templates encoding *how* to do a class of task.

### 4.5 AGENTS.md Codex
See Section 11. The conventions file every AI coding tool reads on session start.

---

## 5. MCP Server Build Order

### Priority 1 — Computer Control
**File:** `mcp_servers/computer_use_server.py`  
**Dependencies:** `pyautogui`, `playwright`, `mss`, `pytesseract`, `opencv-python`  
**Why first:** This is the single capability that separates ShadowRealm from every tool you've already used. Everything else is integration — this is control.

```bash
pip install pyautogui playwright mss pytesseract opencv-python
python -m playwright install chromium
```

### Priority 2 — Notion (Second Brain)
**File:** `mcp_servers/notion_server.py`  
**Dependencies:** `notion-client`  
**API:** Notion Integration Token (Internal Integration)  
**Nodes to connect (your 7-node Second Brain):**
1. Projects Hub
2. Task Manager
3. Knowledge Base
4. Daily Journal / Planning
5. Recipe / Food Notes
6. Financial Tracker
7. Resources / References

**Integration point:** Feed Notion pages into `src/chroma_client.py` via `src/rag_server.py`

### Priority 3 — GitHub
**File:** `mcp_servers/github_server.py`  
**Dependencies:** `PyGithub` or `httpx`  
**Tools:** list_repos, get_pr, review_pr, create_issue, check_ci_status, get_diff, push_file  
**Repos:** CulinaryOS, RecipeOS, NexCMS, ShadowRealm, BibleEvidenceExplorer, DiscountLocator

### Priority 4 — Supabase
**File:** `mcp_servers/supabase_server.py`  
**Dependencies:** `supabase-py`  
**Purpose:** ShadowRealm persistent state — agent decisions, event logs, session memory overflow, project state snapshots

### Priority 5 — CulinaryOS
**File:** `mcp_servers/culinaryos_server.py`  
**Dependencies:** Internal REST API  
**Hook into:** `src/cookbook_serve_lifecycle.py` (already exists)  
**Tools:** get_recipe, scale_recipe, get_inventory, create_production_plan, get_menu

### Priority 6 — Ross Manor
**File:** `mcp_servers/rossmanor_server.py`  
**Dependencies:** AttendanceOnDemand REST API  
**Tools:** get_clock_events, get_schedule, flag_discrepancy, get_daily_summary  
**Background job:** Daily attendance digest at 6:15 AM before morning brief

### Priority 7 — Android Studio / ADB
**File:** `mcp_servers/android_studio_server.py`  
**Dependencies:** ADB (Android Debug Bridge), `subprocess_tools.py`  
**Tools:** build_apk, run_tests, deploy_to_device, get_logcat, list_devices  
**Purpose:** Build, test, and deploy RecipeOS from chat without touching Android Studio

### Priority 8 — Discount Locator
**File:** `mcp_servers/discount_locator_server.py`  
**Dependencies:** Walmart API, Flipp API, store-specific scrapers  
**Tools:** search_deals, get_store_discounts, filter_by_threshold  
**Trigger:** Proactive alerts when 10%+ deals are found at configured stores

---

## 6. Skills System

Skills are markdown files that encode *how* to do a class of task. The agent loads the relevant skill file before starting work, giving it battle-tested procedure rather than improvising each time.

### Dev Skills
```
skills/dev/new_feature.md
  - Branch naming convention
  - Scaffold structure by project (Android = Kotlin MVVM, Web = TypeScript)
  - Test file creation pattern
  - PR template
  - Commit message format

skills/dev/code_review.md
  - Security checklist
  - Performance flags to look for
  - Style guide reminders
  - Required test coverage threshold

skills/dev/android_component.md
  - Kotlin coroutines pattern
  - ViewModel + Repository pattern for RecipeOS
  - Room database migration process
  - Jetpack Compose component structure

skills/dev/api_endpoint.md
  - REST endpoint structure
  - Auth middleware requirements
  - Input validation pattern
  - Response schema standard
  - Error handling format
```

### Culinary Skills
```
skills/culinary/recipe_scale.md
  - Unit conversion tables
  - Yield percentage logic
  - Equipment capacity constraints
  - Rounding rules for commercial quantities

skills/culinary/production_plan.md
  - How to generate prep schedules from a recipe list
  - Station assignment logic
  - Time-backward scheduling from service time
  - Allergen flagging procedure
```

### Ops Skills
```
skills/ops/morning_brief.md
  - What to pull (GitHub activity, calendar, Notion tasks, Ross Manor)
  - Format: bullets, no prose, sorted by urgency
  - Threshold for flagging vs. informing
  - Delivery time: 6:15 AM before wake

skills/ops/ross_manor_audit.md
  - AttendanceOnDemand query procedure
  - Discrepancy threshold (> 5 min = flag)
  - Escalation path
  - Report format
```

---

## 7. Agent Modes / Presets

Using `src/preset_manager.py`. Never expose all tools simultaneously — accuracy collapses above ~10 tools.

### Dev Mode (`config/shadowrealm/presets/dev_mode.json`)
**Active tools:**
- `computer_use_server` — screen control
- `github_server` — repo operations  
- `filesystem_tools` — read/write code
- `subprocess_tools` — run tests, builds
- `android_studio_server` — RecipeOS deploys
- `notion_server` — pull project docs
- `web_tools` — docs lookup
- `deep_research` — architecture research

**Active skills:** `skills/dev/`  
**Trigger:** `@dev` or "switch to dev mode"

### Chef Mode (`config/shadowrealm/presets/chef_mode.json`)
**Active tools:**
- `culinaryos_server` — recipe + inventory
- `notion_server` — food notes + research
- `web_tools` — ingredient sourcing, technique lookup
- `image_gen_server` — plating visualization
- `deep_research` — menu R&D, food history

**Active skills:** `skills/culinary/`  
**Trigger:** `@chef` or "switch to chef mode"

### Ops Mode (`config/shadowrealm/presets/ops_mode.json`)
**Active tools:**
- `rossmanor_server` — attendance
- `caldav_sync` — scheduling
- `email_server` — communications
- `supabase_server` — state + logs
- `visual_report` — dashboard generation
- `notion_server` — task + financial tracker

**Active skills:** `skills/ops/`  
**Trigger:** `@ops` or "switch to ops mode"

---

## 8. Memory Architecture

Four-layer memory stack (current state + targets):

| Layer | Type | Status | Implementation |
|---|---|---|---|
| Working | In-context session | ✅ EXISTS | `src/memory.py` |
| Episodic | Conversation history | ✅ EXISTS | `core/session_manager.py` |
| Semantic | Knowledge base + facts | 🔧 EXTEND | `src/chroma_client.py` + Notion RAG feed |
| Procedural | Learned work patterns | ❌ MISSING | Add `mem0` or `Letta` via `src/memory_provider.py` |

### Procedural Memory Implementation
- Library: `mem0ai` (pip install mem0ai)
- Learns: preferred output format, wake-time behavior, project priority ordering, review vs. auto-merge preferences
- Stored in: Supabase (persistent) + local ChromaDB (fast retrieval)
- Updated: after each session based on explicit feedback or implicit signals

---

## 9. Background Automation Jobs

Using `src/bg_jobs.py` + `src/task_scheduler.py`:

| Schedule | Job | Output |
|---|---|---|
| Daily 6:15 AM | Morning brief assembly | PRs, calendar, Notion tasks, Ross Manor flags |
| Daily midnight | CI scan across all repos | GitHub issue if failing |
| On every git push | Lint + test subprocess | Session notification |
| Weekly Sunday 8 PM | Project health dashboard | `visual_report.py` output |
| Every 2 hours (business hours) | Discount locator scan | Alert if 10%+ deal found |
| Daily 11 PM | Attendance digest | Ross Manor daily summary |
| Weekly Monday 6 AM | Weekly ops brief | Schedule, staffing, inventory levels |

---

## 10. Phased Roadmap

### Phase 0 — Foundation *(Week 1)*
- [x] Create `shadowrealm` branch from `dev`
- [ ] Write `AGENTS.md` codex
- [ ] Write `config/shadowrealm/persona.json`
- [ ] Rebrand surface strings (`src/constants.py`, `odysseus-ui.service`, `Odysseus.spec`)
- [ ] Override `.env.example` with your provider setup

### Phase 1 — Computer Control *(Week 1-2)*
- [ ] `src/agent_tools/computer_use_tools.py`
- [ ] `mcp_servers/computer_use_server.py`
- [ ] Register in `src/integrations.py`
- [ ] Test: screenshot → OCR → click loop

### Phase 2 — Second Brain Integration *(Week 2)*
- [ ] `mcp_servers/notion_server.py`
- [ ] Connect 7 Notion nodes
- [ ] Feed into `src/chroma_client.py` via `src/rag_server.py`
- [ ] Test: ask ShadowRealm about a Notion project → correct answer

### Phase 3 — Dev Agent Mode *(Week 3)*
- [ ] `mcp_servers/github_server.py`
- [ ] `mcp_servers/android_studio_server.py`
- [ ] `config/shadowrealm/presets/dev_mode.json`
- [ ] `skills/dev/` — 4 skill files
- [ ] Test: full dev loop from chat (ask → write code → run tests → push PR)

### Phase 4 — Business Operations *(Week 4)*
- [ ] `mcp_servers/supabase_server.py`
- [ ] `mcp_servers/culinaryos_server.py`
- [ ] `mcp_servers/rossmanor_server.py`
- [ ] `config/shadowrealm/presets/chef_mode.json`
- [ ] `config/shadowrealm/presets/ops_mode.json`
- [ ] `skills/culinary/` + `skills/ops/`

### Phase 5 — Memory + Autonomy *(Week 5-6)*
- [ ] Integrate `mem0` into `src/memory_provider.py`
- [ ] Configure all background automation jobs in `src/task_scheduler.py`
- [ ] Wire morning brief job with all data sources
- [ ] A2A protocol scaffold for cross-agent handoffs

### Phase 6 — Procedural Learning + Polish *(Ongoing)*
- [ ] Procedural memory tuning
- [ ] Discount locator server
- [ ] `AGENTS.md` refinement as work patterns solidify
- [ ] Upstream sync cadence established

---

## 11. Industry Protocols to Adopt

### AGENTS.md / Codex File
The AI-native README standard in 2026. Claude Code reads `CLAUDE.md`, Google Codex reads `AGENTS.md`. Place at repo root on `shadowrealm` branch. Encodes:
- Branch strategy
- Code style per language (Python async-first, Kotlin MVVM, TypeScript)
- Active projects + repo locations
- Files requiring human review before commit
- Forbidden actions (no force push to `dev`, no `.env` commits)
- Preferred output format (concise, no fluff, direct answers)

### MCP (Model Context Protocol) — Anthropic
- Already the architecture of this repo
- All new integrations go in `mcp_servers/` — never write proprietary tool calling
- OAuth flow for external services available in `src/mcp_oauth.py`

### A2A (Agent-to-Agent) — Google
- Horizontal agent coordination protocol
- Allows CulinaryOS agent, Dev agent, Ops agent to hand off tasks
- Implement as `src/a2a_coordinator.py` in Phase 5

### Planning-First Agent Loop
- Upgrade `src/agent_loop.py` to simulate outcome before execution
- Phase-level reflection (not just step-level)
- Critical for high-stakes autonomous jobs (overnight CI scans, attendance audits)

### Tool Groups (Accuracy Preservation)
- Agent accuracy drops from 96% → <15% as tool count grows
- Tool Groups enforced via `src/preset_manager.py`
- Max ~10 tools exposed per mode at any time

---

## 12. File Change Manifest

Complete list of every file to create or modify, with status:

### Create (New Files)
```
AGENTS.md
SHADOWREALM_DEVELOPMENT_PLAN.md        ← this file
skills/dev/new_feature.md
skills/dev/code_review.md
skills/dev/android_component.md
skills/dev/api_endpoint.md
skills/culinary/recipe_scale.md
skills/culinary/production_plan.md
skills/ops/morning_brief.md
skills/ops/ross_manor_audit.md
mcp_servers/computer_use_server.py
mcp_servers/notion_server.py
mcp_servers/github_server.py
mcp_servers/supabase_server.py
mcp_servers/culinaryos_server.py
mcp_servers/rossmanor_server.py
mcp_servers/android_studio_server.py
mcp_servers/discount_locator_server.py
src/agent_tools/computer_use_tools.py
src/a2a_coordinator.py
config/shadowrealm/persona.json
config/shadowrealm/presets/dev_mode.json
config/shadowrealm/presets/chef_mode.json
config/shadowrealm/presets/ops_mode.json
```

### Modify (Existing Files)
```
src/constants.py          → rename Odysseus → ShadowRealm display strings
odysseus-ui.service       → rename service + internal strings
Odysseus.spec             → rename to ShadowRealm.spec
README.md                 → full rewrite for ShadowRealm
.env.example              → override with your provider setup
src/integrations.py       → register all new MCP servers
src/memory_provider.py    → integrate mem0 for procedural memory
docs/                     → swap Odysseus wordmark assets
```

### Do Not Touch (Without Deep Review)
```
src/agent_loop.py         ← 202KB core loop
src/llm_core.py           ← 110KB model routing
src/tool_implementations.py ← 198KB built-in tools
core/database.py          ← 103KB data layer
core/auth.py              ← 30KB auth system
```

---

## Notes & Open Questions

- [ ] **Ross Manor API surface** — need to finish investigating AttendanceOnDemand endpoints before building server
- [ ] **Notion 7-node structure** — document exact database IDs before building Notion server
- [ ] **Supabase schema** — design tables for ShadowRealm state before building server
- [ ] **Local model setup** — confirm Ollama is running locally and which models (llama3, mistral, etc.) for `teacher_escalation.py` cost routing
- [ ] **Computer Use OS** — confirm target OS (Linux/Windows/Mac) for `pyautogui` config
- [ ] **`src/agent_loop.py` review** — determine if planning-first upgrade is needed before Phase 5
