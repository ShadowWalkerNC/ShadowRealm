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
5. [Verified Open-Source Tech Stack](#5-verified-open-source-tech-stack)
6. [Coding Workspace (IDE Layer)](#6-coding-workspace-ide-layer)
7. [Multi-Language Support](#7-multi-language-support)
8. [Governance & Trust System](#8-governance--trust-system)
9. [Memory Architecture](#9-memory-architecture)
10. [MCP Registry & Extensibility](#10-mcp-registry--extensibility)
11. [Skills System](#11-skills-system)
12. [Agent Mesh](#12-agent-mesh)
13. [Universal Task Learning Engine](#13-universal-task-learning-engine)
14. [Agent Modes / Presets](#14-agent-modes--presets)
15. [Background Automation Jobs](#15-background-automation-jobs)
16. [Overload Control](#16-overload-control)
17. [Observability & Monitoring](#17-observability--monitoring)
18. [Odysseus Analysis — What to Borrow, What to Avoid](#18-odysseus-analysis--what-to-borrow-what-to-avoid)
19. [Competitive Feature Matrix](#19-competitive-feature-matrix)
20. [What Already Exists (Audit)](#20-what-already-exists-audit)
21. [Phased Roadmap](#21-phased-roadmap)
22. [Industry Protocols to Adopt](#22-industry-protocols-to-adopt)
23. [Open-Source Strategy](#23-open-source-strategy)
24. [Swarm Architecture](#24-swarm-architecture)
25. [File Change Manifest](#25-file-change-manifest)
26. [Open Questions](#26-open-questions)

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
║  ├── Coding Workspace (Monaco Editor + Sandpack + CopilotKit)        ║
║  ├── Chat / Mission Control (existing Odysseus UI, enhanced)         ║
║  ├── CLI interface                                                   ║
║  └── Mobile (future: React Native companion app)                     ║
╠══════════════════════════════════════════════════════════════════════╣
║  ORCHESTRATION LAYER                                                 ║
║  ├── ShadowRealm Core (Odysseus engine, src/)                        ║
║  ├── AGNO AgentOS control plane (agent runtime)                      ║
║  ├── Mastra (TypeScript agent framework for workspace layer)         ║
║  ├── LangGraph (Python multi-agent workflow engine)                  ║
║  ├── Universal Task Resolution Engine                                ║
║  └── OPA Policy Engine (contextual, trust-aware)                     ║
╠══════════════════════════════════════════════════════════════════════╣
║  GOVERNANCE LAYER                                                    ║
║  ├── Skill Trust Pipeline (scan → review → sign → verify → revoke)  ║
║  ├── OPA Contextual Policy Enforcement (Apache 2.0)                  ║
║  ├── Sigstore/cosign Skill Signing (Apache 2.0)                      ║
║  ├── Audit Memory (tamper-evident, append-only, queryable)           ║
║  └── OpenTelemetry Runtime Monitoring (Apache 2.0)                   ║
╠══════════════════════════════════════════════════════════════════════╣
║  AGENT SWARM                                                         ║
║  ├── DevAgent      → code, GitHub, builds, ADB, live preview         ║
║  ├── ChefAgent     → CulinaryOS, recipes, menus                      ║
║  ├── OpsAgent      → Ross Manor, calendar, email                     ║
║  ├── ResearchAgent → deep research, web, RAG (LlamaIndex)            ║
║  ├── VisionAgent   → OpenHands + Browser Use computer control        ║
║  ├── MemoryAgent   → Letta stateful learning                         ║
║  ├── GovernanceAgent → OPA policy, Sigstore audit, anomaly detection ║
║  └── [user-defined agents spawned at runtime]                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  UNIVERSAL TASK LEARNING ENGINE                                      ║
║  ├── Path 1: Research (deep_research + web_tools + LlamaIndex RAG)   ║
║  ├── Path 2: Ask (targeted single-question clarification)            ║
║  └── Path 3: Watch (computer_use + Browser Use + vision synthesis)   ║
╠══════════════════════════════════════════════════════════════════════╣
║  MODEL ROUTING (teacher_escalation.py)                               ║
║  ├── Qwen3.6-Plus  → MCP-native, repo-level coding                  ║
║  ├── Llama 4 Scout → 10M ctx, full codebase in RAM                  ║
║  ├── DeepSeek V3   → cheap reasoning, summarization                 ║
║  ├── Claude 4      → hard planning, creative synthesis               ║
║  ├── Qwen3.5-Omni  → multimodal (text+image+audio)                  ║
║  └── Ollama local  → free tier, privacy-sensitive tasks              ║
╠══════════════════════════════════════════════════════════════════════╣
║  MCP TOOL LAYER (mcp_servers/)                                       ║
║  ├── computer_use  ├── notion      ├── github                        ║
║  ├── culinaryos    ├── rossmanor   ├── supabase                      ║
║  ├── android_adb   ├── email       ├── memory                        ║
║  ├── rag           ├── image_gen   ├── discount_locator              ║
║  └── [community MCP servers — plug and play via registry]            ║
╠══════════════════════════════════════════════════════════════════════╣
║  SKILLS LIBRARY (skills/)                                            ║
║  ├── dev/      ← coding + software development skills                ║
║  ├── culinary/ ← food + restaurant skills                            ║
║  ├── ops/      ← business operations skills                          ║
║  ├── community/← open-source contributed skill templates             ║
║  └── user/     ← privately learned, gitignored                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  MEMORY STACK                                                        ║
║  ├── Working     → in-session state (src/memory.py)                  ║
║  ├── Declarative → facts, docs, references (Qdrant + LlamaIndex)     ║
║  ├── Procedural  → learned workflows (Letta)                         ║
║  ├── Policy      → permissions, preferences, limits (OPA)            ║
║  └── Audit       → signed tamper-evident history (Sigstore)          ║
╠══════════════════════════════════════════════════════════════════════╣
║  PERSISTENCE & STATE                                                 ║
║  ├── Supabase + pgvector  → cloud state + vector search              ║
║  ├── ElectricSQL          → local-first offline sync                 ║
║  ├── Qdrant               → high-perf local vector store             ║
║  └── SQLite               → core/database.py session data            ║
╠══════════════════════════════════════════════════════════════════════╣
║  REAL-TIME & COLLABORATION                                           ║
║  ├── Yjs   → multi-agent conflict-free co-editing (MIT)              ║
║  ├── Vite  → HMR dev server for live preview (MIT)                   ║
║  └── SSE / WebSockets → live agent output streaming                  ║
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
│   │   ├── python.md
│   │   ├── kotlin.md
│   │   ├── typescript.md
│   │   ├── sql.md
│   │   ├── web.md
│   │   └── shell.md
│   ├── architecture/
│   ├── standards/
│   ├── examples/
│   └── adrs/
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
│   │   ├── governance_engine.py               ← NEW (wraps OPA)
│   │   ├── policy_engine.py                   ← NEW (OPA rules)
│   │   ├── audit_logger.py                    ← NEW (Sigstore)
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
│   ├── ide/                                   ← Monaco Editor + CopilotKit
│   ├── preview/                               ← Sandpack live preview
│   └── terminal/                              ← Embedded terminal
├── observability/
│   ├── otel-collector.yml                     ← OpenTelemetry config
│   ├── prometheus.yml
│   └── plutono/                               ← Plutono dashboard (Apache 2.0)
└── config/
    └── shadowrealm/
        ├── persona.json                       ← identity seed (gitignored)
        ├── trust_policy.json                  ← OPA governance rules
        ├── opa/
        │   └── policies/                      ← .rego policy files
        └── presets/
            ├── dev_mode.json
            ├── chef_mode.json
            └── ops_mode.json
```

---

## 5. Verified Open-Source Tech Stack

**Every technology listed here is confirmed free, open-source, and carries a permissive license. No proprietary dependencies. No subscriptions. No AGPL contamination.**

### License Reference Table

| Technology | Role | License | Notes |
|---|---|---|---|
| **Monaco Editor** | Code editor engine (VS Code core) | MIT | Microsoft — same engine as VS Code |
| **CodeMirror 6** | Lightweight editor alternative | MIT | Best for mobile/embedded views |
| **Sandpack** | In-browser live preview (Node.js in browser) | MIT | By CodeSandbox — zero server setup |
| **Vite** | HMR dev server + bundler | MIT | Fastest live reload available |
| **React** | UI framework | MIT | Industry standard |
| **TypeScript** | Typed JavaScript | Apache 2.0 | Full stack type safety |
| **Tailwind CSS** | Utility-first CSS | MIT | Already in stack |
| **Radix UI** | Accessible component primitives | MIT | Unstyled, composable |
| **shadcn/ui** | Pre-built Radix component library | MIT | Dark theme ready |
| **CopilotKit** | Agent panel React UI components | MIT | Battle-tested agent chat + actions |
| **Mastra** | TypeScript agent framework | Apache 2.0 | Drops into Next.js natively |
| **LangGraph** | Python multi-agent workflow engine | MIT | Complex stateful agent graphs |
| **Browser Use** | Browser/web automation | MIT | 50k+ stars, Playwright-based |
| **OpenCode** | Terminal-native AI coding | MIT | 75+ model providers, LSP support |
| **Yjs** | CRDT real-time co-editing | MIT | Multi-agent conflict-free file edits |
| **ElectricSQL** | Local-first offline sync (SQLite ↔ Postgres) | Apache 2.0 | Works with Supabase directly |
| **OPA (Open Policy Agent)** | Contextual policy enforcement engine | Apache 2.0 | Production standard for policy-as-code |
| **Sigstore / cosign** | Skill signing + verification | Apache 2.0 | Same toolchain as container signing |
| **OpenTelemetry** | Distributed tracing across agents + tools | Apache 2.0 | CNCF standard, vendor-neutral |
| **Prometheus** | Runtime metrics collection | Apache 2.0 | Industry standard |
| **Plutono** | Metrics dashboard (Apache fork of Grafana) | Apache 2.0 | No AGPL contamination |
| **Sentry** | Error tracking (self-hosted) | MIT | Full self-host available |
| **LlamaIndex** | RAG pipelines over docs, Notion, GitHub | MIT | Replaces custom RAG glue code |
| **Qdrant** | High-performance local vector store | Apache 2.0 | Faster + more scalable than ChromaDB |
| **pgvector** | Vector search inside Supabase/Postgres | MIT | Eliminates separate vector DB if desired |
| **fastembed** | Local embeddings, no API cost | Apache 2.0 | Already in Odysseus stack |
| **Letta** | Stateful self-editing procedural memory | Apache 2.0 | Already planned |
| **AGNO** | Agent runtime control plane | Apache 2.0 | Already planned |
| **OpenHands** | Computer use sub-agent | MIT | Already planned |

### License Policy
- **Allowed:** MIT, Apache 2.0, BSD-2, BSD-3, ISC
- **Allowed with care:** LGPL (link only, do not modify)
- **Rejected:** AGPL, GPL, SSPL, BSL, proprietary
- All dependencies must be audited before adding to `requirements.txt` or `package.json`
- AGPL check runs automatically in CI via `license-checker` before every merge

---

## 6. Coding Workspace (IDE Layer)

ShadowRealm's coding workspace is built on **Monaco Editor + Sandpack + CopilotKit**, giving it VS Code-class editing, instant live preview, and a native AI agent panel — all in the browser, all open-source.

```
┌─────────────────────────────────────────────────────────────────┐
│  SHADOWREALM CODING WORKSPACE                                   │
├──────────┬──────────────────────────┬──────────────────────────┤
│          │                          │                          │
│  FILE    │   MONACO EDITOR          │   AGENT PANEL            │
│  TREE    │  (VS Code engine)        │   (CopilotKit)           │
│          │  · IntelliSense          │   · chat scoped to file  │
│          │  · multi-cursor          │   · explain selection    │
│          │  · go-to-definition      │   · skill picker         │
│          │  · inline diff           │   · memory inspector     │
│          │  · accept/reject patch   │   · model selector       │
│          │  · LSP per language      │   · action trace         │
├──────────┴──────────────────────────┴──────────────────────────┤
│              SANDPACK LIVE PREVIEW                              │
│   (Node.js in browser — React, Vue, Vanilla JS, HTML)          │
│   Auto-refresh on file save or agent patch apply               │
│   Mobile viewport · before/after comparison · Vite HMR        │
├─────────────────────────────────────────────────────────────────┤
│  TERMINAL  │  TEST RUNNER  │  OTEL LOGS  │  AUDIT  │  SEARCH  │
└─────────────────────────────────────────────────────────────────┘
```

### Editor: Monaco (MIT)
- The actual VS Code editor engine, open-sourced by Microsoft
- IntelliSense, multi-cursor, go-to-definition, symbol search
- Inline diff / patch review with accept / reject per hunk
- Keyboard shortcuts identical to VS Code — no learning curve
- Agent-proposed edits rendered as inline diffs, never auto-applied

### Live Preview: Sandpack (MIT)
- Runs a full Node.js sandbox in the browser — no server required
- Supports React, Vue, Next.js, Vanilla JS, HTML/CSS out of the box
- Instant hot-reload on every file change or agent patch
- Agent can inspect the rendered DOM and screenshot for before/after comparison
- Vite HMR for server-rendered projects outside the browser sandbox

### Agent Panel: CopilotKit (MIT)
- Battle-tested React components for agent chat, state streaming, and tool actions
- Scoped to the currently open file or project — not a global chatbox
- Explain any selected code block in plain English
- Skill picker: browse and invoke skills from `skills/dev/`
- Memory inspector: what the agent currently knows about this project
- Model selector: choose which model handles the current task
- Action trace: every tool call logged with what was invoked and why

### LSP Integration (per language)
Language Server Protocol gives the editor real intelligence — not just syntax highlighting:
| Language | LSP Server | What it enables |
|---|---|---|
| Python | `pyright` (MIT) | Type checking, autocomplete, go-to-def |
| Kotlin | `kotlin-language-server` (Apache 2.0) | Android SDK types, MVVM patterns |
| TypeScript | `typescript-language-server` (MIT) | Full TS type system, React JSX |
| SQL | `sqls` (MIT) | Schema-aware completions |
| HTML/CSS | `vscode-html-languageservice` (MIT) | Tag completion, CSS variables |

### Yjs Real-Time Co-Editing (MIT)
- Yjs CRDTs allow multiple agents (e.g. DevAgent + GovernanceAgent) to edit the same file simultaneously without conflicts
- Changes merge automatically — no lock/unlock required
- Enables future multi-user collaboration with zero architectural changes

### Beginner Mode
Because Nathaniel is a hobbyist, the agent defaults to:
- Plain English explanation alongside every code change
- "What is this file for?" always answerable
- "Why is this pattern standard?" always answerable
- Common mistakes and alternatives surfaced proactively
- Glossary of terms inline on hover
- "Guide me" mode: agent walks through writing code together step by step

---

## 7. Multi-Language Support

ShadowRealm must understand not just syntax but **project structure, framework conventions, testing patterns, build tools, and deployment flow** for every language in the stack.

### Primary Stack
| Language | Frameworks / Tools | LSP | Doc File |
|---|---|---|---|
| Python | FastAPI, SQLAlchemy, pytest, pip | pyright | `docs/languages/python.md` |
| Kotlin | Android SDK, Jetpack Compose, MVVM, Gradle | kotlin-language-server | `docs/languages/kotlin.md` |
| TypeScript | React, Next.js, Node.js, Jest, pnpm | typescript-language-server | `docs/languages/typescript.md` |
| HTML/CSS/JS | Tailwind, Vanilla JS, responsive patterns | vscode-html-languageservice | `docs/languages/web.md` |
| SQL | PostgreSQL, Supabase, pgvector, migrations | sqls | `docs/languages/sql.md` |
| Shell | Bash, zsh, Docker scripts, CI pipelines | shellcheck | `docs/languages/shell.md` |

### Per-Language Doc Structure
Each `docs/languages/*.md` must include:
1. Language overview in plain English
2. Project structure standard
3. Naming conventions
4. Core patterns (classes, functions, modules, errors)
5. Testing standards
6. Build and run instructions
7. Common mistakes and how to avoid them
8. Industry standard practices
9. Gold standard example files (linked to `docs/examples/`)
10. Anti-patterns

### Cross-Language Project Understanding
A full-stack task may involve TypeScript frontend, Python backend, SQL data layer, and YAML deployment. The agent:
- Understands data flow across all layers
- Names variables consistently across languages
- Catches mismatches between frontend and API contracts
- Handles database migrations safely

---

## 8. Governance & Trust System

This is ShadowRealm's primary differentiator. **Governance is not an add-on. It is the foundation.**

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

### Policy Engine: OPA (Apache 2.0)
Open Policy Agent is the production standard for policy-as-code. ShadowRealm uses it to enforce every skill execution decision:
- Policies written as `.rego` files in `config/shadowrealm/opa/policies/`
- Every tool invocation passes through OPA before execution
- Policy decisions are logged to the audit store
- Rules cover: skill trust tier, tool sensitivity, action reversibility, user role, time constraints
- Policy files are version-controlled, reviewed, and signed like code

### Skill Signing: Sigstore / cosign (Apache 2.0)
Sigstore is the same open-source toolchain used to sign container images and npm packages. ShadowRealm uses it to sign every skill:
- Each skill gets a cryptographic signature at review time
- Signature is verified before every execution
- If the skill file changes after signing, the signature is immediately invalid
- Revocation is instant — set skill to Tier X, signature check fails, execution blocked
- Audit log records every signing event with timestamp and identity

### Skill Trust Pipeline
```
DRAFT → SCAN → REVIEW → SIGN → QUARANTINE → ACTIVATE → MONITOR → [REVOKE if needed]
  │       │       │        │         │           │           │
  │   static   human    cosign    isolated     live      OpenTelemetry
  │   + dep    or AI    issued     sandbox     execution  anomaly
  │   scan     review                           with      detection
  │                                             audit
  │
  └── If any stage fails → blocked, logged to audit store, reported to GovernanceAgent
```

### Trust Tiers
| Tier | Label | Who can execute | Scope |
|---|---|---|---|
| 0 | Draft | Nobody | Not executable |
| 1 | Sandboxed | Agent only, isolated | No production data |
| 2 | Reviewed | Agent, limited scope | Scoped by OPA policy |
| 3 | Signed | Agent, production scope | Owner-approved + cosign |
| 4 | Community | Agent + users | Signed, revocable |
| X | Revoked | Nobody | Disabled immediately |

### Autonomy Tiers
| Level | Name | Description |
|---|---|---|
| 1 | Observe | Agent watches, records, never acts |
| 2 | Advise | Agent suggests, user approves every step |
| 3 | Act with approval | Agent proposes plan, waits for one approval |
| 4 | Autonomous | Agent executes, logs, notifies |

High-risk or irreversible actions always require Level 3 minimum, regardless of skill trust tier.

---

## 9. Memory Architecture

Memory is split into five distinct layers, never mixed into one undifferentiated store.

| Layer | Type | What it stores | Implementation |
|---|---|---|---|
| Working | In-context | Current task state | `src/memory.py` |
| Declarative | Long-term | Facts, docs, references, projects | Qdrant + LlamaIndex RAG |
| Procedural | Learning | Workflows, patterns, how-to | Letta (self-editing, persistent) |
| Policy | Governance | Permissions, preferences, limits | OPA + `config/trust_policy.json` |
| Audit | Governance | Signed tamper-evident action history | Sigstore + append-only Supabase |

### Vector Store: Qdrant (Apache 2.0)
Qdrant replaces ChromaDB as the primary vector store for declarative memory:
- Significantly faster query performance at scale
- Better filtering and payload indexing
- Runs locally in Docker — no cloud dependency
- Compatible with fastembed for local embeddings (no API cost)
- pgvector in Supabase used as a secondary/cloud replica

### RAG: LlamaIndex (MIT)
LlamaIndex handles all RAG pipeline construction:
- Connectors for Notion, GitHub repos, local files, web pages
- Chunking, embedding, indexing handled automatically
- Query engines for multi-source synthesis
- Replaces custom RAG glue code in existing `rag_server.py`

### Local-First Sync: ElectricSQL (Apache 2.0)
ElectricSQL keeps local SQLite in sync with Supabase/Postgres:
- Works offline — all reads and writes go to local SQLite first
- Syncs to Supabase when connection is available
- Conflict resolution built in via CRDTs
- Means ShadowRealm works fully without internet connection

### What Procedural Memory Learns Per User
- Preferred output format (bullet vs. prose, verbose vs. concise)
- Wake-time and work-time patterns
- Project priority ordering
- Which tasks to auto-execute vs. ask permission
- Recurring decisions and their outcomes
- Vocabulary, terminology, abbreviations the user uses
- Which languages and frameworks they favor
- Coding style preferences

---

## 10. MCP Registry & Extensibility

MCPs are the extension surface of ShadowRealm. Any MCP server can be added without modifying core code.

### MCP Registry (`src/mcp_registry.py`)
- Maintains catalogue of all available MCP servers
- Tracks trust tier, capabilities, version, author
- Enables search, favorites, and per-mode activation
- Applies OPA policy before exposing any tool to the agent

### MCP Build Order
| Priority | Server | SDK/API | Unlocks |
|---|---|---|---|
| **1** | `computer_use_server.py` | Browser Use (MIT) + pyautogui | Computer control, watch mode |
| **2** | `notion_server.py` | notion-client | Second Brain in RAG |
| **3** | `github_server.py` | PyGithub / httpx | All repos: PR, issues, CI |
| **4** | `supabase_server.py` | supabase-py | Persistent ShadowRealm state |
| **5** | `culinaryos_server.py` | Internal REST | Recipe, inventory, production |
| **6** | `rossmanor_server.py` | AttendanceOnDemand REST | Kiosk events, attendance |
| **7** | `android_studio_server.py` | ADB + subprocess | Build/deploy RecipeOS from chat |
| **8** | `discount_locator_server.py` | Walmart/Flipp APIs | Deal alerts at 10%+ |

### Overload Prevention
- Enable only relevant MCPs per mode/task
- Cache tool capabilities locally
- Group MCPs by mode — tool groups, not tool dumps
- OPA trust-check every MCP before its tools are exposed
- Community MCP servers start at Tier 1 (sandboxed) until reviewed

---

## 11. Skills System

Skills are structured procedure files. When ShadowRealm needs to do a task, it loads the relevant skill instead of improvising.

### Skill Sources
- **Hand-written** by the user (Tier 3 by default)
- **Research-synthesized** (auto-generated from deep_research.py, Tier 2)
- **Answer-synthesized** (generated from one clarification question, Tier 2)
- **Observation-synthesized** (generated from watching you work, Tier 2 until validated)
- **Community-contributed** (PR to skills/community/, starts at Tier 1)

### Skill Trust Tiers
```
Tier 3 — Gold (hand-written or owner-validated + cosign signature)
  → Executed with full confidence, no confirmation

Tier 2 — Silver (research-synthesized or answer-synthesized)
  → Plan shown first, runs unless user objects

Tier 1 — Bronze (first-time inference, community unvalidated)
  → Full plan shown and approved before execution
  → On success, promoted to Silver automatically

Tier X — Revoked
  → Blocked, cosign signature check fails, cannot execute
```

### Skill Lifecycle State Machine
```
authored → scanned → reviewed → cosign-signed → active → otel-monitored
                                                               │
                                                       drift detected?
                                                               │
                                                       cosign revoked → blocked
```

### Nathaniel's Initial Skill Library
```
skills/dev/
  new_feature.md          ← branch, scaffold, test, PR
  code_review.md          ← security + perf checklist
  android_component.md    ← Kotlin MVVM, Jetpack Compose
  api_endpoint.md         ← REST structure, auth, validation
  debug_session.md        ← systematic debugging workflow
  live_preview_setup.md   ← start Sandpack/Vite + preview

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

## 12. Agent Mesh

```
ShadowRealm Orchestrator (OPA policy + OpenTelemetry audit)
       │
       ├── DevAgent
       │     Tools: github, filesystem, subprocess, android_adb, computer_use, live_preview
       │     Framework: Mastra (TypeScript) + LangGraph (Python)
       │     Skills: skills/dev/
       │     Model: Qwen3.6-Plus
       │     Memory: Qdrant project procedural memory
       │
       ├── ChefAgent
       │     Tools: culinaryos, notion, web, image_gen
       │     Skills: skills/culinary/
       │     Model: Llama 4 Scout
       │     Memory: culinary procedural memory
       │
       ├── OpsAgent
       │     Tools: rossmanor, caldav, email, supabase, visual_report
       │     Skills: skills/ops/
       │     Model: DeepSeek V3
       │     Memory: ops procedural memory
       │
       ├── ResearchAgent
       │     Tools: deep_research, web_tools, LlamaIndex RAG
       │     Skills: synthesizes new ones
       │     Model: Claude 4
       │     Memory: Qdrant declarative knowledge base
       │
       ├── VisionAgent (OpenHands Docker sub-service)
       │     Tools: Browser Use, computer_use, screenshot, OCR
       │     Skills: observation-synthesized
       │     Model: Qwen3.5-Omni
       │
       ├── MemoryAgent (Letta)
       │     Tools: memory_server, Qdrant, Supabase + ElectricSQL
       │     Function: Persistent learning across all agents
       │     Always running in background
       │
       └── GovernanceAgent
             Tools: OPA policy engine, Sigstore/cosign, OpenTelemetry, audit_logger
             Function: Reviews trust decisions, policy exceptions, flags anomalies
             Alerts on: unsigned skill execution, OPA policy bypass, anomalous tool use
```

---

## 13. Universal Task Learning Engine

### The Principle
**If ShadowRealm doesn't know how to do something, it never fails silently. It never hallucinates. It resolves the gap and learns.**

### Resolution Priority Order
1. **Skills library hit** — fastest, fully deterministic, cosign-verified
2. **Procedural memory hit** — learned from this user before (Letta)
3. **RAG knowledge base** — from Notion, documents, past research (LlamaIndex + Qdrant)
4. **Deep research** — live web research, synthesize into new skill
5. **Single clarifying question** — ask user for the one missing piece
6. **Observation mode** — "Show me once, I'll do it every time after"

### What Gets Stored After Each Resolution
1. New skill file written to `skills/user/[task_slug].md`
2. Letta procedural memory updated with preference signal
3. Skill indexed in Qdrant for fast future lookup
4. Skill enters cosign trust pipeline before activation
5. Optionally sanitized and submitted as PR to `skills/community/`

### The "Watch Me" Protocol
1. `computer_use_server` activates via Browser Use observation mode
2. User performs the task naturally
3. Vision model (Qwen3.5-Omni) interprets recording
4. `skill_synthesizer.py` structures observations into repeatable skill
5. Skill validated with user: "I learned this — is this right?"
6. On confirmation: stored permanently, enters cosign pipeline
7. Never needs demonstration again

---

## 14. Agent Modes / Presets

| Mode | Trigger | Active Tools | Active Skills |
|---|---|---|---|
| **Dev** | `@dev` | github, filesystem, subprocess, android_adb, computer_use, notion, web, live_preview | skills/dev/ |
| **Chef** | `@chef` | culinaryos, notion, web, image_gen, deep_research | skills/culinary/ |
| **Ops** | `@ops` | rossmanor, caldav, email, supabase, visual_report, notion | skills/ops/ |
| **Research** | `@research` | deep_research, web_tools, LlamaIndex RAG, notion | synthesizes new |
| **Universal** | `@auto` (default) | task_resolution_engine routes dynamically | auto-selects |

---

## 15. Background Automation Jobs

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
| On skill modification | cosign re-sign check | Alert if signature invalid → block execution |
| Continuous | OPA policy sync | Reload policies from config/ on change |

---

## 16. Overload Control

### Rules
1. Never load all MCP tools globally — use OPA-enforced tool groups per mode
2. Never load all skills at once — lazy-load relevant skills per task
3. Summarize sessions periodically via `src/context_compactor.py`
4. Use subagents for cross-domain tasks (Mastra routes to correct agent)
5. Keep skill procedure files short and structured (max 500 lines enforced)
6. Cap working memory and prune low-value context automatically
7. Re-ground the agent after long multi-step runs
8. OpenTelemetry tracks token use per task — alert on excess

### What This Means in Practice
- Dev agent only sees Dev tools
- Chef agent only sees Culinary tools
- Unknown tasks start with minimal context, expand only as needed
- The orchestrator routes, so no single agent is overloaded
- Every skill file has a maximum size limit enforced at write time

---

## 17. Observability & Monitoring

Full observability is built in from day one using the CNCF open-source stack. No proprietary monitoring tools, no SaaS lock-in.

### Stack
| Tool | Role | License |
|---|---|---|
| **OpenTelemetry** | Distributed tracing across all agents and tools | Apache 2.0 |
| **Prometheus** | Runtime metrics: memory, token use, task success, latency | Apache 2.0 |
| **Plutono** | Metrics dashboards (Apache 2.0 fork of Grafana — no AGPL) | Apache 2.0 |
| **Sentry (self-hosted)** | Error tracking across workspace UI and backend | MIT |

### What Gets Traced
- Every agent action (tool call, model call, skill invocation)
- Every OPA policy decision (allow/deny + reason)
- Every cosign verification event (pass/fail)
- Token usage per task, per agent, per model
- Skill execution time and success rate
- Memory read/write operations
- MCP server health

### Governance Integration
- OpenTelemetry traces feed directly into the GovernanceAgent
- Anomalous patterns (unexpected tool use, policy bypasses, signature failures) trigger alerts
- All audit events are append-only and tamper-evident via Sigstore
- Audit trail is queryable from the workspace bottom bar

---

## 18. Odysseus Analysis — What to Borrow, What to Avoid

### What to Borrow
| Pattern | Why |
|---|---|
| All-in-one workspace concept | Right product shape |
| Docker-first onboarding | clone → cp .env → compose up |
| Hardware-aware model recommendation | Friction reduction for local models |
| Deep research UX | Multi-step research with citations |
| MCP tool externalization | Architecturally sound |
| Branch strategy (dev + main) | Clean upstream sync |

### What to Avoid
| Problem | ShadowRealm Solution |
|---|---|
| No skill trust tiers | cosign trust pipeline from day one |
| No skill signing | Sigstore/cosign — revoke on modification |
| Single ChromaDB memory store | Qdrant + LlamaIndex + Letta + OPA + Sigstore audit |
| No multi-agent architecture | Full specialist agent mesh via LangGraph + Mastra |
| AGPL license | MIT — no copyleft contamination |
| No contextual policy | OPA policy engine evaluates every sensitive action |
| Prompt injection from email/web | Treat external content as untrusted, sanitize before agent |

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

## 19. Competitive Feature Matrix

| Feature | VS Code Copilot | Cursor | Windsurf | ShadowRealm |
|---|---|---|---|---|
| Multi-file editing | ✅ | ✅ | ✅ | ✅ Monaco |
| Live preview | ⚠️ partial | ⚠️ partial | ✅ | ✅ Sandpack |
| Persistent memory | ✅ | ✅ | ⚠️ | ✅ Letta + Qdrant |
| Plugin/MCP ecosystem | ✅ | ⚠️ | ⚠️ | ✅ full registry |
| Debug/trace panel | ✅ | ✅ | ⚠️ | ✅ OpenTelemetry |
| Terminal integration | ✅ | ✅ | ✅ | ✅ auditable |
| Skill trust tiers | ❌ | ❌ | ❌ | ✅ |
| Skill signing | ❌ | ❌ | ❌ | ✅ Sigstore |
| Policy engine | ❌ | ❌ | ❌ | ✅ OPA |
| Audit trail | ❌ | ❌ | ❌ | ✅ tamper-evident |
| Beginner teaching mode | ❌ | ❌ | ❌ | ✅ |
| Self-hosted / local | ❌ | ❌ | ❌ | ✅ |
| Multi-agent mesh | ❌ | ❌ | ❌ | ✅ LangGraph + Mastra |
| Task learning engine | ❌ | ❌ | ❌ | ✅ |
| Watch mode | ❌ | ❌ | ❌ | ✅ Browser Use |
| Real-time co-editing | ❌ | ❌ | ❌ | ✅ Yjs CRDTs |
| Context overload control | ⚠️ | ⚠️ | ⚠️ | ✅ by design |
| 100% open source | ⚠️ | ❌ | ❌ | ✅ MIT |

---

## 20. What Already Exists (Audit)

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
| `src/memory_provider.py` | 10KB | Memory provider abstraction ← Qdrant + Letta go here |
| `src/chroma_client.py` | 2.3KB | ChromaDB ← replace with Qdrant client |
| `src/visual_report.py` | 71KB | Visual dashboard/report generation |
| `src/caldav_sync.py` | 30KB | Google Calendar two-way sync |
| `src/webhook_manager.py` | 12KB | Inbound/outbound webhooks |
| `src/bg_jobs.py` | 11KB | Background job runner |
| `src/bg_monitor.py` | 6KB | Job health monitor |
| `src/preset_manager.py` | 7.5KB | Agent persona/tool group presets |
| `src/teacher_escalation.py` | 26KB | Multi-model cost escalation routing |
| `src/integrations.py` | 25KB | Integration registry |
| `src/cookbook_serve_lifecycle.py` | 9KB | CulinaryOS-ready recipe serving lifecycle |
| `src/mcp_manager.py` | 29KB | MCP server registration + management |
| `src/event_bus.py` | 4KB | Internal event pub/sub |
| `src/context_compactor.py` | 19KB | Context window compression ← KEY for overload control |

---

## 21. Phased Roadmap

### Phase 0 — Foundation *(Week 1)*
- [x] Create `shadowrealm` branch from `dev`
- [x] Write master development plan
- [ ] Write `AGENTS.md` codex
- [ ] Write `config/shadowrealm/persona.json`
- [ ] Write `config/shadowrealm/trust_policy.json` + initial OPA `.rego` policies
- [ ] Rebrand surface strings in `src/constants.py`
- [ ] Create `docs/languages/` structure
- [ ] Override `.env.example`
- [ ] Add `license-checker` to CI (block AGPL/GPL/SSPL deps)

### Phase 1 — Computer Control *(Week 1-2)*
- [ ] `src/agent_tools/computer_use_tools.py` (wraps Browser Use)
- [ ] `mcp_servers/computer_use_server.py`
- [ ] Docker setup for OpenHands sub-agent
- [ ] Test: screenshot → OCR → click loop
- [ ] Test: "watch me" observation mode end-to-end

### Phase 2 — Second Brain Integration *(Week 2)*
- [ ] `mcp_servers/notion_server.py`
- [ ] LlamaIndex RAG pipeline → Qdrant
- [ ] Replace `src/chroma_client.py` with `src/qdrant_client.py`
- [ ] Test: ask about Notion project → correct answer

### Phase 3 — Dev Agent + Coding Workspace *(Week 3)*
- [ ] `mcp_servers/github_server.py`
- [ ] `mcp_servers/android_studio_server.py`
- [ ] `workspace/ide/` — Monaco Editor + CopilotKit
- [ ] `workspace/preview/` — Sandpack + Vite
- [ ] LSP servers wired per language
- [ ] Yjs co-editing layer
- [ ] Dev mode preset + `skills/dev/`
- [ ] `docs/languages/` all six language guides
- [ ] Beginner mode + glossary
- [ ] Test: full dev loop — chat → edit → preview → push PR

### Phase 4 — Business Operations *(Week 4)*
- [ ] `mcp_servers/supabase_server.py`
- [ ] ElectricSQL local-first sync wired
- [ ] `mcp_servers/culinaryos_server.py`
- [ ] `mcp_servers/rossmanor_server.py`
- [ ] Chef + Ops mode presets + skills

### Phase 5 — Memory + Autonomy *(Week 5-6)*
- [ ] Integrate Letta into `src/memory_provider.py`
- [ ] Separate declarative (Qdrant) / procedural (Letta) / policy (OPA) / audit (Sigstore) stores
- [ ] Wire all background automation jobs
- [ ] A2A coordinator scaffold
- [ ] Morning brief fully operational

### Phase 6 — Governance Layer *(Week 6-7)*
- [ ] `src/agent_tools/governance_engine.py` (wraps OPA)
- [ ] `src/agent_tools/policy_engine.py` (OPA .rego policy files)
- [ ] `src/agent_tools/audit_logger.py` (Sigstore cosign)
- [ ] Skill trust pipeline (scan → review → cosign → verify)
- [ ] Trust tiers 0–4 + revocation
- [ ] GovernanceAgent wired to monitor all skill activations
- [ ] Autonomy tier enforcement

### Phase 7 — Observability *(Week 7)*
- [ ] OpenTelemetry collector wired across all agents and tools
- [ ] Prometheus metrics exporter
- [ ] Plutono dashboards (token use, task success, policy decisions, error rates)
- [ ] Sentry self-hosted error tracking
- [ ] Audit trail panel in workspace bottom bar

### Phase 8 — Universal Task Engine *(Week 7-8)*
- [ ] `src/agent_tools/task_resolution_engine.py`
- [ ] `src/agent_tools/skill_synthesizer.py`
- [ ] Research path (LlamaIndex + deep_research)
- [ ] Ask path (clarification engine)
- [ ] Watch path (Browser Use + vision synthesis)
- [ ] Skill quality tier system
- [ ] Universal mode preset

### Phase 9 — Swarm + Open-Source Graduation *(Month 3)*
- [ ] Integrate AGNO as agent runtime
- [ ] LangGraph wired for Python multi-agent workflows
- [ ] Mastra wired for TypeScript workspace agent layer
- [ ] All specialist sub-agents wired
- [ ] Wire OpenHands as VisionAgent
- [ ] `docker-compose.shadowrealm.yml` for one-command deploy
- [ ] MCP registry with community plugin support

### Phase 10 — Community + Universal Adoption *(Month 4+)*
- [ ] Publish MCP servers as standalone pip packages
- [ ] `skills/community/` open for PR contributions
- [ ] `CONTRIBUTING.md` with skill contribution guide
- [ ] GitHub Actions CI with license-checker
- [ ] Public documentation site
- [ ] `shadowrealm init` CLI wizard for new user onboarding
- [ ] Skill submission pipeline (user skills → PII scrub → community PR)

---

## 22. Industry Protocols to Adopt

| Protocol | Source | License | Purpose | Status |
|---|---|---|---|---|
| MCP | Anthropic | MIT | Agent ↔ Tool communication | ✅ Built-in |
| A2A | Google | Apache 2.0 | Agent ↔ Agent coordination | 🔧 Phase 5 |
| LSP | Microsoft | MIT | Editor ↔ Language intelligence | 🔧 Phase 3 |
| AGENTS.md | Community | MIT | AI coding agent conventions | 📝 Phase 0 |
| OpenHands API | MIT | MIT | Open computer use sub-agent | 🔧 Phase 1 |
| AGNO AgentOS | Apache 2.0 | Apache 2.0 | Agent runtime control plane | 🔧 Phase 9 |
| OPA Policy | Apache 2.0 | Apache 2.0 | Policy-as-code enforcement | 🔧 Phase 6 |
| Sigstore | Apache 2.0 | Apache 2.0 | Tamper-evident skill signing | 🔧 Phase 6 |
| OpenTelemetry | Apache 2.0 | Apache 2.0 | Distributed observability | 🔧 Phase 7 |
| Yjs CRDT | MIT | MIT | Conflict-free collaborative editing | 🔧 Phase 3 |
| Planning-first loop | Research | — | Simulate before execute | 🔧 Phase 8 |
| Tool Groups | Best practice | — | Accuracy preservation / no overload | 🔧 Phase 0 |

---

## 23. Open-Source Strategy

### Philosophy
ShadowRealm is free. No subscription. No cloud lock-in. License: **MIT**. No AGPL contamination. Every dependency must pass the license audit gate in CI.

### What Gets Open-Sourced
- The entire ShadowRealm platform
- All MCP servers as standalone pip packages
- The Skills library (`skills/community/`)
- `AGENTS.md` template
- `docker-compose.shadowrealm.yml`
- `shadowrealm init` CLI onboarding wizard
- Governance engine, OPA policies, and policy engine
- Language documentation templates
- Observability configs (OTel, Prometheus, Plutono)

### What Stays Private Per Deployment
- `config/shadowrealm/persona.json` (gitignored)
- `skills/user/` (gitignored)
- `.env` (gitignored)
- Any proprietary API credentials

### The Moat
**The community skill library + governed trust pipeline.**
As users contribute validated workflows, ShadowRealm becomes the most capable out-of-the-box AI system for real human work — with a cosign-signed trust pipeline that no other open-source system has.

---

## 24. Swarm Architecture

```
ShadowRealm Orchestrator (OPA + OpenTelemetry + cosign audit)
       │
       ├── DevAgent       → Qwen3.6-Plus   → skills/dev/      → Mastra + LangGraph
       ├── ChefAgent      → Llama 4 Scout  → skills/culinary/ → LangGraph
       ├── OpsAgent       → DeepSeek V3    → skills/ops/      → LangGraph
       ├── ResearchAgent  → Claude 4       → synthesizes      → LlamaIndex + LangGraph
       ├── VisionAgent    → Qwen3.5-Omni   → observation      → Browser Use + OpenHands
       ├── MemoryAgent    → Letta          → always running   → Qdrant + ElectricSQL
       └── GovernanceAgent→ Claude 4       → always watching  → OPA + Sigstore + OTel
```

---

## 25. File Change Manifest

### Phase 0 (Now)
```
CREATE: AGENTS.md
CREATE: CONTRIBUTING.md
CREATE: config/shadowrealm/persona.json             ← gitignored
CREATE: config/shadowrealm/trust_policy.json
CREATE: config/shadowrealm/opa/policies/skill.rego  ← OPA skill policy
CREATE: config/shadowrealm/opa/policies/tool.rego   ← OPA tool policy
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
CREATE: src/agent_tools/computer_use_tools.py       ← wraps Browser Use (MIT)
CREATE: mcp_servers/computer_use_server.py
CREATE: mcp_servers/notion_server.py
CREATE: src/qdrant_client.py                        ← replace chroma_client.py
CREATE: docker-compose.shadowrealm.yml
MODIFY: src/integrations.py                         ← register new MCP servers
```

### Phase 3 — Coding Workspace
```
CREATE: workspace/ide/                              ← Monaco Editor + CopilotKit (React)
CREATE: workspace/preview/                          ← Sandpack + Vite
CREATE: workspace/terminal/                         ← Embedded terminal
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
CREATE: src/agent_tools/governance_engine.py        ← wraps OPA
CREATE: src/agent_tools/policy_engine.py            ← OPA .rego loader
CREATE: src/agent_tools/audit_logger.py             ← Sigstore cosign
CREATE: src/skill_registry.py
CREATE: src/mcp_registry.py
MODIFY: src/memory_provider.py                      ← integrate Letta + Qdrant
MODIFY: src/agent_loop.py                           ← planning-first + autonomy tiers
```

### Phase 7
```
CREATE: observability/otel-collector.yml
CREATE: observability/prometheus.yml
CREATE: observability/plutono/                      ← dashboard configs
```

### Phase 8-9
```
CREATE: src/agent_tools/task_resolution_engine.py
CREATE: src/agent_tools/skill_synthesizer.py
CREATE: src/a2a_coordinator.py
CREATE: mcp_servers/discount_locator_server.py
CREATE: shadowrealm_cli/init.py
MODIFY: src/integrations.py                         ← register swarm agents
MODIFY: src/teacher_escalation.py                   ← add Qwen3.6, Llama 4, DeepSeek V3
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

## 26. Open Questions

- [ ] **Ross Manor API** — document AttendanceOnDemand endpoints
- [ ] **Notion node IDs** — export 7 database IDs for notion_server.py
- [ ] **Supabase schema** — design tables for state, skill store, event log, audit trail, pgvector columns
- [ ] **Local model stack** — confirm Ollama running + which models installed
- [ ] **Target OS** — Linux/Windows/Mac for Browser Use + pyautogui config
- [ ] **OpenHands Docker** — confirm Docker is available on the host
- [ ] **agent_loop.py review** — planning-first upgrade feasibility
- [ ] **Community skill sanitization** — design PII-scrubbing pipeline before Phase 10
- [ ] **ElectricSQL shape** — define which tables sync locally vs. cloud-only
- [ ] **OPA policy scope** — write initial .rego policies for skill tiers and tool sensitivity
- [ ] **Plutono dashboard design** — define which metrics panels are most useful day-to-day
- [ ] **Qdrant collections** — define collection schema for declarative, procedural, and skill index
