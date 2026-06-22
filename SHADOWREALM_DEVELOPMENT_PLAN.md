# ShadowRealm — Master Development Plan

> **Living Document** — Last updated: June 22, 2026
> **Branch Strategy:** `dev` = upstream Odysseus sync target | `shadowrealm` = your personal trunk
> **Vision:** A universal, self-learning, governed AI operating system — open-source, self-hostable, free forever.

---

## Table of Contents
1. [Core Vision](#1-core-vision)
2. [What ShadowRealm Is](#2-what-shadowrealm-is)
3. [Universal Learning Philosophy](#3-universal-learning-philosophy)
4. [Architecture Overview](#4-architecture-overview)
5. [Coding Workspace (IDE Layer)](#5-coding-workspace-ide-layer)
6. [Multi-Language Support](#6-multi-language-support)
7. [Governance & Trust System](#7-governance--trust-system)
8. [Memory Architecture](#8-memory-architecture)
9. [MCP Registry & Extensibility](#9-mcp-registry--extensibility)
10. [Skills System](#10-skills-system)
11. [Agent Mesh](#11-agent-mesh)
12. [Universal Task Learning Engine](#12-universal-task-learning-engine)
13. [Agent Modes / Presets](#13-agent-modes--presets)
14. [Background Automation Jobs](#14-background-automation-jobs)
15. [Overload Control](#15-overload-control)
16. [Odysseus Analysis — What to Borrow, What to Avoid](#16-odysseus-analysis--what-to-borrow-what-to-avoid)
17. [Competitive Feature Matrix](#17-competitive-feature-matrix)
18. [What Already Exists (Audit)](#18-what-already-exists-audit)
19. [Phased Roadmap](#19-phased-roadmap)
20. [Industry Protocols to Adopt](#20-industry-protocols-to-adopt)
21. [Open-Source Strategy](#21-open-source-strategy)
22. [Swarm Architecture](#22-swarm-architecture)
23. [File Change Manifest](#23-file-change-manifest)
24. [Open Questions](#24-open-questions)

---

## 1. Core Vision

**ShadowRealm is not an app. It is a living AI operating system.**

It starts as personal Mission Control for one person — Nathaniel — and grows into an open-source platform that any person on earth can deploy for themselves. A nurse. A contractor. A student. A farmer. A musician. A hobbyist developer. Someone who has never written code. ShadowRealm doesn't require the user to define their world upfront. **It learns their world by watching, asking, and researching** until it can operate as a true partner.

**The core promise:**
> *Give ShadowRealm any task. If it knows how, it does it. If it doesn't, it figures it out — through research, by asking you, or by watching you do it once. It remembers forever. It never asks twice. It never executes without trust.*

**Four non-negotiables:**
1. **Open and free** — MIT licensed, self-hostable, no cloud lock-in, no subscription
2. **Universal** — designed for any person, any profession, any workflow
3. **Genuinely intelligent** — not a chatbot wrapper. A system that plans, learns, acts, and grows
4. **Verifiably safe** — every skill is trusted, every action is audited, every sensitive operation is governed

---

## 2. What ShadowRealm Is

ShadowRealm is a **universal, self-learning, governed AI operating system** that can:

- Learn any person's workflows through research, clarification, and observation
- Convert demonstrations into reusable, trusted skills
- Run software tools and MCP servers
- Coordinate a mesh of specialized sub-agents
- Write, edit, and debug code across all stack languages
- Show a live preview of code output in real time
- Enforce trust and approval policies on every skill and tool
- Keep a permanent, auditable memory of how work gets done

### Design Principle: Small Core, Open Surface
The base app handles only essentials: file system, model routing, memory, agent loop, policy engine, and UI shell. Everything else comes from skills and MCP servers. This keeps the system extensible without bloating the core or overloading the agent.

---

## 3. Universal Learning Philosophy

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
User says "that's wrong" or "do it like this instead" → system updates stored procedure immediately.

**Loop 2 — Implicit Signal**
User edits the agent's output → system logs the delta, clusters patterns over time, updates skill template for that task type.

**Loop 3 — Observation**
User says "watch me" → computer_use_server records the session → vision model synthesizes steps → new skill file written to `skills/` automatically.

### The Skills Library as a Living Community Asset
Every skill learned by ShadowRealm becomes a **community-contributable skill template**. Skills are sanitized of personal data and submitted as PRs to `skills/community/`. Over time, ShadowRealm ships with a vast library of human workflows — coding, cooking, accounting, medical admin, legal drafting, farming, music production — contributed by the global user base.

---

## 4. Architecture Overview

```
╔══════════════════════════════════════════════════════════════════════╗
║                    SHADOWREALM OS  v2.0                              ║
║           Universal Self-Learning Governed AI Operating System       ║
╠══════════════════════════════════════════════════════════════════════╣
║  PRESENTATION LAYER                                                  ║
║  ├── Coding Workspace (IDE: editor + live preview + agent panel)     ║
║  ├── Chat / Mission Control (existing Odysseus UI, enhanced)         ║
║  ├── CLI interface                                                   ║
║  └── Mobile (future: React Native companion app)                     ║
╠══════════════════════════════════════════════════════════════════════╣
║  ORCHESTRATION LAYER                                                 ║
║  ├── ShadowRealm Core (Odysseus engine, src/)                       ║
║  ├── AGNO AgentOS control plane (agent runtime)                     ║
║  ├── ClawTeam swarm coordinator                                     ║
║  ├── Universal Task Resolution Engine                               ║
║  └── Policy Engine (contextual, trust-aware)                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  GOVERNANCE LAYER                                                    ║
║  ├── Skill Trust Pipeline (scan → review → sign → verify → revoke)  ║
║  ├── Contextual Policy Enforcement                                  ║
║  ├── Approval Workflow (for new/modified skills)                    ║
║  ├── Audit Memory (tamper-evident, signed, queryable)               ║
║  └── Runtime Monitoring + Anomaly Detection                         ║
╠══════════════════════════════════════════════════════════════════════╣
║  AGENT SWARM                                                         ║
║  ├── DevAgent      → code, GitHub, builds, ADB, live preview        ║
║  ├── ChefAgent     → CulinaryOS, recipes, menus                     ║
║  ├── OpsAgent      → Ross Manor, calendar, email                    ║
║  ├── ResearchAgent → deep research, web, RAG                        ║
║  ├── VisionAgent   → OpenHands computer control                     ║
║  ├── MemoryAgent   → Letta stateful learning                        ║
║  ├── GovernanceAgent → skill review, trust decisions, policy exceptions ║
║  └── [user-defined agents spawned at runtime]                       ║
╠══════════════════════════════════════════════════════════════════════╣
║  UNIVERSAL TASK LEARNING ENGINE                                      ║
║  ├── Path 1: Research (deep_research + web_tools)                   ║
║  ├── Path 2: Ask (targeted single-question clarification)           ║
║  └── Path 3: Watch (computer_use + vision synthesis)                ║
╠══════════════════════════════════════════════════════════════════════╣
║  MODEL ROUTING (teacher_escalation.py)                               ║
║  ├── Qwen3.6-Plus  → MCP-native, repo-level coding                 ║
║  ├── Llama 4 Scout → 10M ctx, full codebase in RAM                 ║
║  ├── DeepSeek V3   → cheap reasoning, summarization                ║
║  ├── Claude 4      → hard planning, creative synthesis              ║
║  ├── Qwen3.5-Omni  → multimodal (text+image+audio)                 ║
║  └── Ollama local  → free tier, privacy-sensitive tasks             ║
╠══════════════════════════════════════════════════════════════════════╣
║  MCP TOOL LAYER (mcp_servers/)                                       ║
║  ├── computer_use  ├── notion      ├── github                       ║
║  ├── culinaryos    ├── rossmanor   ├── supabase                     ║
║  ├── android_adb   ├── email       ├── memory                       ║
║  ├── rag           ├── image_gen   ├── discount_locator             ║
║  └── [community MCP servers — plug and play via registry]           ║
╠══════════════════════════════════════════════════════════════════════╣
║  SKILLS LIBRARY (skills/)                                            ║
║  ├── dev/      ← coding + software development skills               ║
║  ├── culinary/ ← food + restaurant skills                           ║
║  ├── ops/      ← business operations skills                         ║
║  ├── community/← open-source contributed skill templates            ║
║  └── user/     ← privately learned, gitignored                     ║
╠══════════════════════════════════════════════════════════════════════╣
║  MEMORY STACK                                                        ║
║  ├── Working    → in-session state (src/memory.py)                  ║
║  ├── Declarative → facts, documents, references (ChromaDB + RAG)   ║
║  ├── Procedural → learned workflows (Letta)                        ║
║  ├── Policy     → permissions, preferences, limits                 ║
║  └── Audit      → signed tamper-evident action history             ║
╠══════════════════════════════════════════════════════════════════════╣
║  PERSISTENCE & STATE                                                 ║
║  ├── Supabase   → cloud state + event logs                          ║
║  ├── ChromaDB   → local vector store                                ║
║  └── SQLite     → core/database.py session data                    ║
╚══════════════════════════════════════════════════════════════════════╝
```

### File Structure
```
ShadowRealm/
├── AGENTS.md                                  ← Codex for all AI coding agents
├── SHADOWREALM_DEVELOPMENT_PLAN.md            ← This file
├── CONTRIBUTING.md                            ← How to contribute skills + MCP servers
├── docker-compose.shadowrealm.yml             ← One-command self-hosted deploy
├── docs/
│   ├── languages/
│   │   ├── python.md                          ← Language guide + standards
│   │   ├── kotlin.md
│   │   ├── typescript.md
│   │   ├── sql.md
│   │   ├── web.md                             ← HTML/CSS/JS
│   │   └── shell.md
│   ├── architecture/                          ← System design decisions
│   ├── standards/                             ← Coding standards per language
│   ├── examples/                              ← Gold standard reference files
│   └── adrs/                                  ← Architecture Decision Records
├── skills/
│   ├── dev/
│   ├── culinary/
│   ├── ops/
│   ├── community/
│   └── user/                                  ← private, gitignored
├── mcp_servers/
│   ├── computer_use_server.py
│   ├── notion_server.py
│   ├── github_server.py
│   ├── supabase_server.py
│   ├── culinaryos_server.py
│   ├── rossmanor_server.py
│   ├── android_studio_server.py
│   ├── discount_locator_server.py
│   ├── email_server.py                        ← EXISTS
│   ├── memory_server.py                       ← EXISTS
│   ├── image_gen_server.py                    ← EXISTS
│   └── rag_server.py                          ← EXISTS
├── src/
│   ├── agent_tools/
│   │   ├── computer_use_tools.py              ← NEW
│   │   ├── task_resolution_engine.py          ← NEW
│   │   ├── skill_synthesizer.py               ← NEW
│   │   ├── governance_engine.py               ← NEW
│   │   ├── policy_engine.py                   ← NEW
│   │   ├── audit_logger.py                    ← NEW
│   │   ├── filesystem_tools.py                ← EXISTS
│   │   ├── subprocess_tools.py                ← EXISTS
│   │   ├── document_tools.py                  ← EXISTS
│   │   ├── web_tools.py                       ← EXISTS
│   │   ├── model_interaction_tools.py         ← EXISTS
│   │   └── session_tools.py                   ← EXISTS
│   ├── a2a_coordinator.py                     ← NEW
│   ├── skill_registry.py                      ← NEW
│   ├── mcp_registry.py                        ← NEW
│   └── [60+ engine files]
├── workspace/
│   ├── ide/                                   ← Coding workspace UI
│   ├── preview/                               ← Live preview panel
│   └── terminal/                              ← Embedded terminal
└── config/
    └── shadowrealm/
        ├── persona.json                       ← identity seed (gitignored)
        ├── trust_policy.json                  ← governance rules
        └── presets/
            ├── dev_mode.json
            ├── chef_mode.json
            └── ops_mode.json
```

---

## 5. Coding Workspace (IDE Layer)

ShadowRealm should feel like a Visual Studio-class AI development studio. The layout is three-panel with a bottom bar:

```
┌─────────────────────────────────────────────────────────────────┐
│  SHADOWREALM CODING WORKSPACE                                   │
├──────────┬──────────────────────────┬──────────────────────────┤
│          │                          │                          │
│  FILE    │      CODE EDITOR         │    AGENT PANEL           │
│  TREE    │   (tabs, split panes,    │   (chat, explain,        │
│          │    syntax highlight,     │    skill picker,         │
│          │    diff view, lint)      │    memory inspector,     │
│          │                          │    model selector)       │
│          │                          │                          │
├──────────┴──────────────────────────┴──────────────────────────┤
│                   LIVE PREVIEW                                  │
│            (web app, docs, UI, reports)                         │
│            Auto-refresh on file save or patch apply            │
├─────────────────────────────────────────────────────────────────┤
│  TERMINAL  │  TEST RUNNER  │  LOGS  │  AUDIT TRAIL  │  SEARCH  │
└─────────────────────────────────────────────────────────────────┘
```

### Editor Features
- File explorer with project tree
- Syntax highlighting for all stack languages
- Tabs and split panes
- Inline diff / patch review
- Symbol search and navigation
- Lint, diagnostics, type hints
- Agent-proposed edits with accept / reject controls
- Keyboard shortcuts consistent with VS Code

### Live Preview Panel
- Auto-run local dev server for web projects
- Render app in embedded browser panel
- Refresh on file save or agent patch apply
- Agent can inspect rendered output
- Before/after visual comparison for UI changes
- Preview markdown, HTML, dashboards, reports
- Mobile viewport simulation

### Agent Panel
- Chat interface scoped to current file or project
- Explain any selected code in plain English
- Skill picker and MCP tool picker
- Memory inspector (what the agent currently knows about this project)
- Model selector (choose which model handles the task)
- Action trace (what tools were called and why)

### Bottom Bar
- Embedded terminal (scoped and auditable)
- Test runner with inline results
- Logs panel
- Audit trail (actions taken this session)
- Full-project search

### Beginner Mode
Because Nathaniel is a hobbyist, the agent defaults to:
- Plain English explanations alongside every code change
- "What is this file for?" always answerable
- "Why is this pattern standard?" always answerable
- Common mistakes and alternatives surfaced proactively
- Glossary of terms inline on hover
- "Guide me" mode where agent walks through writing it together

---

## 6. Multi-Language Support

ShadowRealm must understand not just syntax but **project structure, framework conventions, testing patterns, build tools, and deployment flow** for every language in the stack.

### Primary Stack
| Language | Frameworks / Tools | Documentation File |
|---|---|---|
| Python | FastAPI, SQLAlchemy, pytest, pip | `docs/languages/python.md` |
| Kotlin | Android SDK, Jetpack Compose, MVVM, Gradle | `docs/languages/kotlin.md` |
| TypeScript | React, Next.js, Node.js, Jest, npm/pnpm | `docs/languages/typescript.md` |
| HTML/CSS/JS | Tailwind, Vanilla JS, responsive patterns | `docs/languages/web.md` |
| SQL | PostgreSQL, Supabase, migrations, schema design | `docs/languages/sql.md` |
| Shell | Bash, zsh, Docker scripts, CI pipelines | `docs/languages/shell.md` |

### Secondary Support
- Markdown and docs-as-code
- YAML and JSON for config
- Docker and Compose files
- Framework-specific conventions

### Per-Language Doc Structure (each `docs/languages/*.md` must include)
1. Language overview in plain English
2. Project structure standard (file and folder layout)
3. Naming conventions
4. Core patterns (classes, functions, modules, errors)
5. Testing standards
6. Build and run instructions
7. Common mistakes and how to avoid them
8. Industry standard practices
9. Gold standard example files (linked to `docs/examples/`)
10. Anti-patterns

### Agent Behavior Per Language
- Load the relevant language doc before editing
- Explain any change that introduces a new pattern
- Flag deviation from documented standards
- Suggest refactors toward industry conventions
- For multi-language tasks, explain how the pieces connect

### Cross-Language Project Understanding
A full-stack task may involve TypeScript frontend, Python backend, SQL data layer, and YAML deployment. The agent should:
- Understand data flow across layers
- Name variables consistently across languages
- Catch mismatches between frontend and API contracts
- Handle migrations safely

---

## 7. Governance & Trust System

This is ShadowRealm's primary differentiator over every existing tool including Odysseus. **Governance is not an add-on. It is the foundation.**

### Core Principle
> If the system cannot explain why an action is allowed, the action is denied.

### Threat Model
ShadowRealm must defend against:
- Malicious skill injection
- Prompt injection via external content (email, web, documents)
- Privilege escalation through tool use
- Context poisoning
- Unauthorized data access
- Cross-agent collusion
- Silent policy bypass
- Post-review skill tampering
- Malicious MCP servers
- Supply chain attacks on dependencies

### Skill Trust Pipeline
Every skill must pass all stages before activation:

```
DRAFT → SCAN → REVIEW → SIGN → QUARANTINE → ACTIVATE → MONITOR → [REVOKE if needed]
  │       │       │        │         │           │           │
  │   static   human    sig        isolated     live      runtime
  │   + dep    or AI    issued     run test    execution  anomaly
  │   scan     review                           with      detection
  │                                             audit
  │
  └── If any stage fails → blocked, logged, reported
```

### Trust Tiers
| Tier | Label | Who can execute | Scope |
|---|---|---|---|
| 0 | Draft | Nobody | Not executable |
| 1 | Sandboxed | Agent only, isolated | No production data |
| 2 | Reviewed | Agent, limited scope | Scoped by policy |
| 3 | Signed | Agent, production scope | Owner-approved |
| 4 | Community | Agent + users | Signed, revocable |
| X | Revoked | Nobody | Disabled immediately |

### Contextual Policy Engine
Permission depends on:
- Skill trust tier
- Task type and risk classification
- Tool sensitivity
- Destination system
- Action reversibility
- User role
- Time and context constraints

### Audit Memory (Required for every sensitive action)
Every consequential action must record:
- Agent identity
- Delegator
- Skill name + version
- Policy version
- Tool invoked
- Scope issued
- Approval state
- Result
- Retention state
- Timestamp

### Revocation Rule
If a skill changes after signing, the signature becomes invalid immediately. The skill is blocked until re-reviewed and re-signed. This is the primary defense against post-review tampering.

### Autonomy Tiers
Not all tasks should run at the same autonomy level:
| Level | Name | Description |
|---|---|---|
| 1 | Observe | Agent watches, records, never acts |
| 2 | Advise | Agent suggests, user approves every step |
| 3 | Act with approval | Agent proposes plan, waits for one approval |
| 4 | Autonomous | Agent executes, logs, notifies |

High-risk or irreversible actions always require Level 3 minimum, regardless of skill trust tier.

---

## 8. Memory Architecture

Memory is split into four distinct layers. They are never mixed into one undifferentiated store.

| Layer | Type | What it stores | Implementation |
|---|---|---|---|
| Working | In-context | Current task state | `src/memory.py` |
| Declarative | Long-term | Facts, docs, references, projects | ChromaDB + Notion RAG |
| Procedural | Learning | Workflows, patterns, how-to | Letta (self-editing, persistent) |
| Policy | Governance | Permissions, preferences, limits | `config/trust_policy.json` + DB |
| Audit | Governance | Signed tamper-evident action history | Append-only store, Supabase |

### What Procedural Memory Learns Per User
- Preferred output format (bullet vs. prose, verbose vs. concise)
- Wake-time and work-time patterns
- Project priority ordering
- Which tasks to auto-execute vs. ask permission
- Recurring decisions and their outcomes
- Vocabulary, terminology, abbreviations the user uses
- Who they email most and how they prefer to respond
- Which languages and frameworks they favor
- Coding style preferences

### Memory Overload Controls
- Summarize long sessions periodically using `src/context_compactor.py`
- Prune low-value context automatically
- Re-ground the agent after long runs
- Keep skill docs short and structured
- Use subagents rather than one giant context window
- Working memory is session-scoped and reset between tasks

### Orchestrator vs. Agent Memory Placement
Based on LEGOMem research: orchestrator memory is critical for planning and delegation. Per-agent memory improves execution accuracy. Both are needed and should be separate stores.

---

## 9. MCP Registry & Extensibility

MCPs are the extension surface of ShadowRealm. Any MCP server can be added without modifying core code.

### MCP Registry (`src/mcp_registry.py`)
- Maintains the catalogue of all available MCP servers
- Tracks trust tier, capabilities, version, author
- Enables search, favorites, and per-mode activation
- Applies policy controls before exposing tool to agent

### MCP Categories
| Category | Examples |
|---|---|
| Filesystem & project | computer_use, filesystem, subprocess |
| Code & development | github, android_adb, linting |
| Research & knowledge | deep_research, rag, web_tools |
| Business & comms | email, calendar, rossmanor |
| Data | supabase, chromadb, sqlite |
| Design & preview | image_gen, live_preview |
| Personal & domain | culinaryos, notion, discount_locator |
| Community plugins | Any third-party MCP server |

### MCP Build Order
| Priority | Server | SDK/API | Unlocks |
|---|---|---|---|
| **1** | `computer_use_server.py` | pyautogui, playwright, mss, pytesseract | Computer control, watch mode |
| **2** | `notion_server.py` | notion-client | Second Brain in RAG |
| **3** | `github_server.py` | PyGithub / httpx | All repos: PR, issues, CI |
| **4** | `supabase_server.py` | supabase-py | Persistent ShadowRealm state |
| **5** | `culinaryos_server.py` | Internal REST | Recipe, inventory, production |
| **6** | `rossmanor_server.py` | AttendanceOnDemand REST | Kiosk events, attendance |
| **7** | `android_studio_server.py` | ADB + subprocess | Build/deploy RecipeOS from chat |
| **8** | `discount_locator_server.py` | Walmart/Flipp APIs | Deal alerts at 10%+ |

### Overload Prevention for MCPs
- Enable only relevant MCPs per mode/task (never expose all at once)
- Cache tool capabilities locally
- Group MCPs by mode — tool groups, not tool dumps
- Trust-check every MCP before its tools are exposed to the agent
- Community MCP servers start at Tier 1 (sandboxed) until reviewed

---

## 10. Skills System

Skills are structured procedure files. When ShadowRealm needs to do a task, it loads the relevant skill instead of improvising. This reduces prompt size, improves reliability, and enables governance.

### Skill Sources
- **Hand-written** by the user (highest quality, Tier 3 by default)
- **Research-synthesized** (auto-generated from deep_research.py, Tier 2)
- **Answer-synthesized** (generated from one clarification question, Tier 2)
- **Observation-synthesized** (generated from watching you work, Tier 2 until validated)
- **Community-contributed** (PR to skills/community/, starts at Tier 1)

### Skill Trust Tiers
```
Tier 3 — Gold (hand-written or owner-validated)
  → Executed with full confidence, no confirmation

Tier 2 — Silver (research-synthesized or answer-synthesized)
  → Plan shown first, runs unless user objects

Tier 1 — Bronze (first-time inference, community unvalidated)
  → Full plan shown and approved before execution
  → On success, promoted to Silver automatically

Tier X — Revoked
  → Blocked, cannot execute
```

### Skill Lifecycle State Machine
```
authored → scanned → reviewed → signed → active → monitored
                                                       │
                                               drift detected?
                                                       │
                                                   revoked
```

### Nathaniel's Initial Skill Library
```
skills/dev/
  new_feature.md          ← branch, scaffold, test, PR
  code_review.md          ← security + perf checklist
  android_component.md    ← Kotlin MVVM, Jetpack Compose
  api_endpoint.md         ← REST structure, auth, validation
  debug_session.md        ← systematic debugging workflow
  live_preview_setup.md   ← start dev server + preview

skills/culinary/
  recipe_scale.md         ← yield%, unit conversions, equipment constraints
  production_plan.md      ← prep schedule, station assignment, time-backward

skills/ops/
  morning_brief.md        ← 6:15 AM data pull + format
  ross_manor_audit.md     ← attendance check + discrepancy threshold

skills/community/
  README.md               ← how to contribute a skill

skills/user/              ← private, gitignored, learned by observation
```

---

## 11. Agent Mesh

ShadowRealm uses specialized sub-agents rather than one monolithic agent. Each agent has a narrower domain, smaller tool exposure, and its own memory allocation.

```
ShadowRealm Orchestrator
       │
       ├── DevAgent
       │     Tools: github, filesystem, subprocess, android_adb, computer_use, live_preview
       │     Skills: skills/dev/
       │     Model: Qwen3.6-Plus (MCP-native coding)
       │     Memory: project procedural memory
       │
       ├── ChefAgent
       │     Tools: culinaryos, notion, web, image_gen
       │     Skills: skills/culinary/
       │     Model: Llama 4 Scout (large recipe corpus context)
       │     Memory: culinary procedural memory
       │
       ├── OpsAgent
       │     Tools: rossmanor, caldav, email, supabase, visual_report
       │     Skills: skills/ops/
       │     Model: DeepSeek V3 (cheap, reliable for structured tasks)
       │     Memory: ops procedural memory
       │
       ├── ResearchAgent
       │     Tools: deep_research, web_tools, rag_server
       │     Skills: (synthesizes new ones)
       │     Model: Claude 4 (best synthesis + reasoning)
       │     Memory: declarative knowledge base
       │
       ├── VisionAgent (OpenHands Docker sub-service)
       │     Tools: computer_use, browser, screenshot, ocr
       │     Skills: observation-synthesized
       │     Model: InfantAgent / Qwen3.5-Omni (vision-native)
       │
       ├── MemoryAgent (Letta)
       │     Tools: memory_server, chroma, supabase
       │     Function: Persistent learning across all agents
       │     Always running in background
       │
       └── GovernanceAgent
             Tools: skill_registry, audit_logger, policy_engine
             Function: Reviews trust decisions, policy exceptions, flags anomalies
             Alerts on: unsigned skill execution, policy bypass, anomalous tool use
```

---

## 12. Universal Task Learning Engine

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
2. Updates Letta procedural memory with preference signal
3. Indexes the skill in ChromaDB for fast future lookup
4. Applies the skill trust pipeline before activation
5. Optionally sanitizes and submits as PR to `skills/community/`

### The "Watch Me" Protocol
1. `computer_use_server` activates observation mode (screen recording + action log)
2. User performs the task naturally
3. Vision model (Qwen3.5-Omni or InfantAgent) interprets recording
4. `skill_synthesizer.py` structures observations into repeatable skill
5. Skill is validated with user: "I learned this — is this right?"
6. On confirmation: stored permanently, enters trust pipeline
7. Never needs demonstration again

---

## 13. Agent Modes / Presets

Using `src/preset_manager.py`. Tool groups — never expose all tools at once.

| Mode | Trigger | Active Tools | Active Skills |
|---|---|---|---|
| **Dev** | `@dev` | computer_use, github, filesystem, subprocess, android_adb, notion, web, live_preview | skills/dev/ |
| **Chef** | `@chef` | culinaryos, notion, web, image_gen, deep_research | skills/culinary/ |
| **Ops** | `@ops` | rossmanor, caldav, email, supabase, visual_report, notion | skills/ops/ |
| **Research** | `@research` | deep_research, web_tools, rag, notion | synthesizes new |
| **Universal** | `@auto` (default) | task_resolution_engine routes dynamically | auto-selects |

**Universal Mode** dynamically selects the right tool group based on what the task actually requires, so the user never needs to know which mode to switch to.

---

## 14. Background Automation Jobs

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
| On skill modification | Re-sign check | Alert if signature invalid |

---

## 15. Overload Control

Context overload is one of the top failure modes in agentic systems. ShadowRealm prevents it at every layer.

### Rules
1. Never load all MCP tools globally — use tool groups per mode
2. Never load all skills at once — lazy-load relevant skills per task
3. Summarize sessions periodically via `src/context_compactor.py`
4. Use subagents for tasks that cross domains (don't pile everything into one context)
5. Keep skill procedure files short and structured
6. Cap working memory and prune low-value context automatically
7. Re-ground the agent after long multi-step runs
8. Audit token use per task and alert on excess

### What This Means in Practice
- The Dev agent only sees Dev tools
- The Chef agent only sees Culinary tools
- A new unknown task starts with minimal context and expands only as needed
- The orchestrator handles routing so no single agent is overloaded
- Every skill file has a maximum size limit enforced at write time

---

## 16. Odysseus Analysis — What to Borrow, What to Avoid

Odysseus (pewdiepie-archdaemon/odysseus, AGPL-3.0) is the strongest existing reference for a local-first AI workspace. It validates the market but leaves the hard problems unsolved.

### What to Borrow
| Pattern | Why |
|---|---|
| All-in-one workspace concept | Right product shape for the target user |
| Docker-first onboarding | Frictionless: clone → cp .env → compose up |
| Hardware-aware model recommendation (Cookbook) | Genuine friction reduction for local model users |
| Deep research UX | Multi-step research with citations differentiates from chat |
| MCP tool externalization | Architecturally sound extension pattern |
| Branch strategy (dev + main) | Clean upstream sync model |

### What to Avoid
| Problem | ShadowRealm Solution |
|---|---|
| No skill trust tiers | Implement trust pipeline from day one |
| No skill signing | Sign all skills, revoke on modification |
| Single ChromaDB memory store | Separate declarative / procedural / policy / audit memory |
| No multi-agent architecture | Full specialist agent mesh |
| AGPL license | MIT license — no copyleft contamination |
| Single maintainer | Build community + contribution structures early |
| Prompt injection from email/web | Treat external content as untrusted, sanitize before agent |
| No contextual policy | Policy engine evaluates every sensitive action |

### Scoring Comparison
| Dimension | Odysseus | ShadowRealm Target |
|---|---|---|
| Product Vision | ★★★★★ | ★★★★★ |
| Architecture | ★★★☆☆ | ★★★★★ |
| Security | ★★☆☆☆ | ★★★★★ |
| Governance | ★☆☆☆☆ | ★★★★★ |
| Memory | ★★☆☆☆ | ★★★★★ |
| Multi-Agent | ★☆☆☆☆ | ★★★★★ |
| License | ★★☆☆☆ (AGPL) | ★★★★★ (MIT) |
| Coding Workspace | ★★★☆☆ | ★★★★★ |

---

## 17. Competitive Feature Matrix

| Feature | VS Code Copilot | Cursor | Windsurf | ShadowRealm |
|---|---|---|---|---|
| Multi-file editing | ✅ | ✅ | ✅ | ✅ |
| Live preview | ⚠️ partial | ⚠️ partial | ✅ | ✅ first-class |
| Persistent memory | ✅ | ✅ | ⚠️ | ✅ multi-layer |
| Plugin/MCP ecosystem | ✅ | ⚠️ | ⚠️ | ✅ full registry |
| Debug/trace panel | ✅ | ✅ | ⚠️ | ✅ |
| Terminal integration | ✅ | ✅ | ✅ | ✅ auditable |
| Skill trust tiers | ❌ | ❌ | ❌ | ✅ |
| Skill signing | ❌ | ❌ | ❌ | ✅ |
| Audit trail | ❌ | ❌ | ❌ | ✅ |
| Beginner teaching mode | ❌ | ❌ | ❌ | ✅ |
| Self-hosted / local | ❌ | ❌ | ❌ | ✅ |
| Multi-agent mesh | ❌ | ❌ | ❌ | ✅ |
| Task learning engine | ❌ | ❌ | ❌ | ✅ |
| Watch mode | ❌ | ❌ | ❌ | ✅ |
| Context overload control | ⚠️ | ⚠️ | ⚠️ | ✅ by design |
| Open source | ⚠️ | ❌ | ❌ | ✅ MIT |

---

## 18. What Already Exists (Audit)

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
| `src/context_compactor.py` | 19KB | Context window compression ← KEY for overload control |

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

## 19. Phased Roadmap

### Phase 0 — Foundation *(Week 1)*
- [x] Create `shadowrealm` branch from `dev`
- [x] Write master development plan
- [ ] Write `AGENTS.md` codex
- [ ] Write `config/shadowrealm/persona.json`
- [ ] Write `config/shadowrealm/trust_policy.json`
- [ ] Rebrand surface strings in `src/constants.py`
- [ ] Create `docs/languages/` structure
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

### Phase 3 — Dev Agent + Coding Workspace *(Week 3)*
- [ ] `mcp_servers/github_server.py`
- [ ] `mcp_servers/android_studio_server.py`
- [ ] Coding workspace UI (editor + agent panel + live preview)
- [ ] Dev mode preset + skills
- [ ] Multi-language doc files (`docs/languages/`)
- [ ] Beginner teaching mode
- [ ] Test: full dev loop from chat → push PR + preview

### Phase 4 — Business Operations *(Week 4)*
- [ ] `mcp_servers/supabase_server.py`
- [ ] `mcp_servers/culinaryos_server.py`
- [ ] `mcp_servers/rossmanor_server.py`
- [ ] Chef + Ops mode presets + skills

### Phase 5 — Memory + Autonomy *(Week 5-6)*
- [ ] Integrate Letta into `src/memory_provider.py` (procedural memory)
- [ ] Separate declarative / policy / audit memory stores
- [ ] Wire all background automation jobs
- [ ] A2A coordinator scaffold
- [ ] Morning brief fully operational

### Phase 6 — Governance Layer *(Week 6-7)*
- [ ] `src/agent_tools/governance_engine.py`
- [ ] `src/agent_tools/policy_engine.py`
- [ ] `src/agent_tools/audit_logger.py`
- [ ] Skill trust pipeline (scan → review → sign → verify)
- [ ] Trust tiers 0–4 + revocation
- [ ] GovernanceAgent wired to monitor all skill activations
- [ ] Autonomy tier enforcement (observe / advise / act-with-approval / autonomous)

### Phase 7 — Universal Task Engine *(Week 7-8)*
- [ ] `src/agent_tools/task_resolution_engine.py`
- [ ] `src/agent_tools/skill_synthesizer.py`
- [ ] Research path (deep_research integration)
- [ ] Ask path (clarification engine)
- [ ] Watch path (observation + vision synthesis)
- [ ] Skill quality tier system
- [ ] Universal mode preset
- [ ] Overload control audit + tuning

### Phase 8 — Swarm + Open-Source Graduation *(Month 3)*
- [ ] Integrate AGNO as agent runtime
- [ ] Integrate ClawTeam for swarm orchestration
- [ ] All specialist sub-agents wired
- [ ] Wire OpenHands as VisionAgent
- [ ] `docker-compose.shadowrealm.yml` for one-command deploy
- [ ] MCP registry with community plugin support

### Phase 9 — Community + Universal Adoption *(Month 4+)*
- [ ] Publish MCP servers as standalone pip packages
- [ ] `skills/community/` open for PR contributions
- [ ] `CONTRIBUTING.md` with skill contribution guide
- [ ] GitHub Actions CI for public repo
- [ ] Public documentation site
- [ ] `shadowrealm init` CLI wizard for new user onboarding
- [ ] Skill submission pipeline (user skills → sanitize → community PR)

---

## 20. Industry Protocols to Adopt

| Protocol | Source | Purpose | Status |
|---|---|---|---|
| MCP | Anthropic | Agent ↔ Tool communication | ✅ Built-in |
| A2A | Google | Agent ↔ Agent coordination | 🔧 Phase 5 |
| AGENTS.md | Community standard | AI coding agent conventions | 📝 Phase 0 |
| OpenHands API | MIT | Open computer use sub-agent | 🔧 Phase 1 |
| AGNO AgentOS | Apache 2.0 | Agent runtime control plane | 🔧 Phase 8 |
| ClawTeam | MIT | Swarm coordination | 🔧 Phase 8 |
| Skill Cards | Emerging | Skill metadata + trust metadata | 🔧 Phase 6 |
| Policy-as-Prompt | Research | LLM-enforceable governance rules | 🔧 Phase 6 |
| Signed Provenance | Research | Tamper-evident audit trails | 🔧 Phase 6 |
| Planning-first loop | Research | Simulate before execute | 🔧 Phase 7 |
| Tool Groups | Best practice | Accuracy preservation / no overload | 🔧 Phase 0 |
| AMDM Monitoring | Research | Multi-axis anomaly detection | 🔧 Phase 8 |

---

## 21. Open-Source Strategy

### Philosophy
ShadowRealm is free. No subscription. No cloud lock-in. The value is in the platform and community — not a paywall. License: **MIT** (explicitly not AGPL — no copyleft contamination).

### What Gets Open-Sourced
- The entire ShadowRealm platform
- All MCP servers as standalone pip packages
- The Skills library (`skills/community/`)
- `AGENTS.md` template
- `docker-compose.shadowrealm.yml`
- `shadowrealm init` CLI onboarding wizard
- Governance engine and policy engine
- Language documentation templates

### What Stays Private Per Deployment
- `config/shadowrealm/persona.json` (gitignored)
- `skills/user/` (gitignored)
- `.env` (gitignored)
- Any proprietary API credentials

### The Moat
Not data. Not a model. **The community skill library + governance system.**
As more users contribute observed + validated workflows across professions, ShadowRealm becomes the most capable out-of-the-box AI system for real human work — with a trust pipeline that no other open-source system has.

### Community Contribution Model
```
User installs ShadowRealm
  → ShadowRealm learns new skills via Watch/Ask/Research
  → System prompts: "I learned how to [task]. Share with community?"
  → User reviews sanitized skill file
  → One-click PR to skills/community/
  → Reviewed + signed + merged → available to all users
```

---

## 22. Swarm Architecture

Using AGNO (control plane) + ClawTeam (coordination) + custom specialists:

```
ShadowRealm Orchestrator (Policy-enforcing, audit-logging)
       │
       ├── DevAgent       → Qwen3.6-Plus   → skills/dev/      → github, filesystem, live_preview
       ├── ChefAgent      → Llama 4 Scout  → skills/culinary/ → culinaryos, notion
       ├── OpsAgent       → DeepSeek V3    → skills/ops/      → rossmanor, caldav, email
       ├── ResearchAgent  → Claude 4       → synthesizes      → deep_research, rag, web
       ├── VisionAgent    → Qwen3.5-Omni   → observation      → computer_use, browser
       ├── MemoryAgent    → Letta          → always running   → memory_server, chroma
       └── GovernanceAgent→ Claude 4       → always watching  → skill_registry, audit_logger
```

---

## 23. File Change Manifest

### Phase 0 (Now)
```
CREATE: AGENTS.md
CREATE: CONTRIBUTING.md
CREATE: config/shadowrealm/persona.json             ← gitignored
CREATE: config/shadowrealm/trust_policy.json
CREATE: config/shadowrealm/presets/dev_mode.json
CREATE: config/shadowrealm/presets/chef_mode.json
CREATE: config/shadowrealm/presets/ops_mode.json
CREATE: docs/languages/python.md
CREATE: docs/languages/kotlin.md
CREATE: docs/languages/typescript.md
CREATE: docs/languages/sql.md
CREATE: docs/languages/web.md
CREATE: docs/languages/shell.md
CREATE: docs/architecture/README.md
CREATE: docs/standards/README.md
MODIFY: src/constants.py                            ← Odysseus → ShadowRealm strings
MODIFY: README.md                                   ← full rewrite
MODIFY: .env.example                                ← provider setup
```

### Phase 1-2
```
CREATE: src/agent_tools/computer_use_tools.py
CREATE: mcp_servers/computer_use_server.py
CREATE: mcp_servers/notion_server.py
CREATE: docker-compose.shadowrealm.yml
MODIFY: src/integrations.py                        ← register new MCP servers
```

### Phase 3 — Coding Workspace
```
CREATE: workspace/ide/                              ← editor UI
CREATE: workspace/preview/                          ← live preview panel
CREATE: workspace/terminal/                         ← embedded terminal
CREATE: mcp_servers/github_server.py
CREATE: mcp_servers/android_studio_server.py
CREATE: skills/dev/new_feature.md
CREATE: skills/dev/code_review.md
CREATE: skills/dev/android_component.md
CREATE: skills/dev/api_endpoint.md
CREATE: skills/dev/debug_session.md
CREATE: skills/dev/live_preview_setup.md
```

### Phase 4
```
CREATE: mcp_servers/supabase_server.py
CREATE: mcp_servers/culinaryos_server.py
CREATE: mcp_servers/rossmanor_server.py
CREATE: skills/culinary/recipe_scale.md
CREATE: skills/culinary/production_plan.md
CREATE: skills/ops/morning_brief.md
CREATE: skills/ops/ross_manor_audit.md
CREATE: skills/community/README.md
```

### Phase 5-6
```
CREATE: src/agent_tools/governance_engine.py
CREATE: src/agent_tools/policy_engine.py
CREATE: src/agent_tools/audit_logger.py
CREATE: src/skill_registry.py
CREATE: src/mcp_registry.py
MODIFY: src/memory_provider.py                     ← integrate Letta
MODIFY: src/agent_loop.py                          ← planning-first + autonomy tiers
```

### Phase 7-8
```
CREATE: src/agent_tools/task_resolution_engine.py
CREATE: src/agent_tools/skill_synthesizer.py
CREATE: src/a2a_coordinator.py
CREATE: mcp_servers/discount_locator_server.py
CREATE: shadowrealm_cli/init.py                    ← onboarding wizard
MODIFY: src/integrations.py                        ← register swarm agents
MODIFY: src/teacher_escalation.py                  ← add Qwen3.6, Llama 4, DeepSeek V3
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

## 24. Open Questions

- [ ] **Ross Manor API** — document AttendanceOnDemand endpoints
- [ ] **Notion node IDs** — export 7 database IDs for notion_server.py
- [ ] **Supabase schema** — design tables for state, skill store, event log, audit trail
- [ ] **Local model stack** — confirm Ollama running + which models installed
- [ ] **Target OS** — Linux/Windows/Mac for pyautogui config
- [ ] **OpenHands Docker** — confirm Docker is available on the host
- [ ] **agent_loop.py review** — planning-first upgrade feasibility
- [ ] **Community skill sanitization** — design PII-scrubbing pipeline before Phase 9
- [ ] **IDE framework choice** — evaluate Monaco Editor (VS Code core) vs. CodeMirror for workspace
- [ ] **Live preview server** — evaluate Vite HMR vs. custom dev server for preview panel
- [ ] **Audit store** — evaluate append-only log format + Supabase vs. local SQLite
- [ ] **Skill signing toolchain** — evaluate GPG vs. Sigstore for skill signatures
