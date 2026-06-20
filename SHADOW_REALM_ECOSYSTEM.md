# 🌑 ShadowRealm Ecosystem

> **The single source of truth for all ShadowWalkerNC projects.**
> Every tool, API, and app connects here. This document is the master blueprint.

---

## 🏛️ What Is ShadowRealm?

ShadowRealm is the **central hub SaaS platform** that:
- Acts as the main API gateway and MCP server router for all sub-projects
- Hosts ShadowBot (AI assistant) accessible via web browser AND local desktop install
- Exposes every sub-project as a registered **MCP tool** callable by ShadowBot
- Provides a unified auth system (one login, all tools)
- Works fully **offline/local** and also **over the internet** (hybrid deployment)
- Serves as the launchpad for forking/contributing to individual projects

---

## 🗂️ Project Registry

All active ShadowWalkerNC projects are registered here. Each project is an independent repo **and** an MCP-connected module inside ShadowRealm.

| Project | Repo | Type | Language | Status | ShadowRealm MCP Tool Name |
|---|---|---|---|---|---|
| **ShadowBot** | [ShadowWalkerNC/ShadowBot](https://github.com/ShadowWalkerNC/ShadowBot) | AI Agent / Orchestration Core | — | 🟡 In Progress | `shadowbot_agent` |
| **CulinaryOS** | [ShadowWalkerNC/CulinaryOS](https://github.com/ShadowWalkerNC/CulinaryOS) | Android App + Web ERP + REST API | Kotlin / React / Supabase | 🟢 Active | `culinaryos_api` |
| **RecipeOS** | [ShadowWalkerNC/RecipeOS](https://github.com/ShadowWalkerNC/RecipeOS) | Android App | Kotlin | 🟢 Active | `recipeos_api` |
| **NexCMS** | [ShadowWalkerNC/NexCMS](https://github.com/ShadowWalkerNC/NexCMS) | Website Builder / CMS | React / Supabase | 🟢 Active | `nexcms_api` |
| **Post-Pilot** | [ShadowWalkerNC/Post-Pilot](https://github.com/ShadowWalkerNC/Post-Pilot) | Social Media Auto-Publisher | Python / Meta Graph API | 🟢 Active | `postpilot_api` |
| **RestRevive-AI** | [ShadowWalkerNC/RestRevive-AI](https://github.com/ShadowWalkerNC/RestRevive-AI) | Restaurant Intelligence Platform | React / Supabase / Anthropic | 🟡 Early Stage | `restrevive_api` |
| **BibleDesk** | [ShadowWalkerNC/BibleDesk](https://github.com/ShadowWalkerNC/BibleDesk) | Theological Research / AI Evidence | React / Supabase / Anthropic | 🟡 Early Stage | `bibledesk_api` |
| **Shoreline** | [ShadowWalkerNC/Shoreline](https://github.com/ShadowWalkerNC/Shoreline) | Sylvia Ross Mission Control (Private) | JavaScript | 🔒 Private | `shoreline_api` |

---

## 🏗️ ShadowRealm Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     🌑 SHADOW REALM HUB                     │
│         Web App (Browser) + Desktop App (Local/Electron)    │
├──────────────────┬──────────────────┬───────────────────────┤
│   Auth Layer     │  ShadowBot AI    │   Dashboard / UI      │
│ (Single Sign-On) │  (MCP Orchestr.) │   (All Tools Access)  │
├──────────────────┴──────────────────┴───────────────────────┤
│                    🔌 MCP SERVER ROUTER                     │
│  (Each project registers as an MCP tool endpoint below)     │
├────────────┬────────────┬────────────┬────────────┬─────────┤
│ culinaryos │  recipeos  │  nexcms    │ postpilot  │ ...more │
│   _api     │   _api     │   _api     │   _api     │         │
├────────────┴────────────┴────────────┴────────────┴─────────┤
│              📡 SHADOW REALM MASTER API GATEWAY             │
│         (REST + WebSocket, local + internet-accessible)     │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

1. **ShadowRealm API Gateway** — Central REST API that proxies requests to all sub-project APIs
2. **ShadowBot Orchestrator** — AI agent (Odysseus framework) that can invoke any registered MCP tool
3. **Auth Module** — JWT-based unified auth; one account unlocks all tools
4. **MCP Tool Registry** — JSON config file listing every tool, its endpoint, its schema, and its permissions
5. **Web Portal** — React/Next.js frontend accessible in browser
6. **Desktop Shell** — Electron wrapper for full local operation (offline-capable)
7. **Plugin Manifest Standard** — How each new project registers itself into ShadowRealm (see below)

---

## 🔌 How Projects Connect to ShadowRealm

Every project (current or future) connects by following the **Shadow Plugin Standard**:

### 1. Create a `shadowrealm.plugin.json` file in your project root

```json
{
  "id": "culinaryos",
  "name": "CulinaryOS",
  "version": "1.0.0",
  "description": "Culinary intelligence platform — recipes, inventory, kitchen ERP",
  "mcp_tool_name": "culinaryos_api",
  "base_url": "https://api.culinaryos.app",
  "local_port": 4001,
  "auth_required": true,
  "endpoints": [
    { "name": "get_recipes", "method": "GET", "path": "/recipes" },
    { "name": "scale_recipe", "method": "POST", "path": "/recipes/scale" },
    { "name": "get_inventory", "method": "GET", "path": "/inventory" }
  ],
  "shadowbot_capabilities": [
    "Search and retrieve recipes",
    "Scale recipe ingredients",
    "Check kitchen inventory levels"
  ],
  "repo": "https://github.com/ShadowWalkerNC/CulinaryOS",
  "forkable": true,
  "tags": ["culinary", "restaurant", "inventory", "recipes"]
}
```

### 2. Add a `CONTRIBUTING.md` so community can fork and contribute

Every public project repo should have a `CONTRIBUTING.md` explaining:
- How to run locally
- How to register a new endpoint in `shadowrealm.plugin.json`
- How to submit a PR back to the project
- How that project connects to the ShadowRealm hub

### 3. Register in `mcp-registry.json` in THIS repo

The file `mcp-registry.json` in ShadowRealm is the master list ShadowBot reads at runtime to know which tools exist.

---

## 📋 MCP Tool Registry (`mcp-registry.json`)

This file lives in `ShadowWalkerNC/ShadowRealm` and is the single file ShadowBot loads at startup.

```json
{
  "version": "1.0.0",
  "tools": [
    {
      "tool_name": "culinaryos_api",
      "repo": "ShadowWalkerNC/CulinaryOS",
      "plugin_manifest": "https://raw.githubusercontent.com/ShadowWalkerNC/CulinaryOS/main/shadowrealm.plugin.json"
    },
    {
      "tool_name": "recipeos_api",
      "repo": "ShadowWalkerNC/RecipeOS",
      "plugin_manifest": "https://raw.githubusercontent.com/ShadowWalkerNC/RecipeOS/main/shadowrealm.plugin.json"
    },
    {
      "tool_name": "nexcms_api",
      "repo": "ShadowWalkerNC/NexCMS",
      "plugin_manifest": "https://raw.githubusercontent.com/ShadowWalkerNC/NexCMS/main/shadowrealm.plugin.json"
    },
    {
      "tool_name": "postpilot_api",
      "repo": "ShadowWalkerNC/Post-Pilot",
      "plugin_manifest": "https://raw.githubusercontent.com/ShadowWalkerNC/Post-Pilot/main/shadowrealm.plugin.json"
    },
    {
      "tool_name": "restrevive_api",
      "repo": "ShadowWalkerNC/RestRevive-AI",
      "plugin_manifest": "https://raw.githubusercontent.com/ShadowWalkerNC/RestRevive-AI/main/shadowrealm.plugin.json"
    },
    {
      "tool_name": "bibledesk_api",
      "repo": "ShadowWalkerNC/BibleDesk",
      "plugin_manifest": "https://raw.githubusercontent.com/ShadowWalkerNC/BibleDesk/main/shadowrealm.plugin.json"
    }
  ]
}
```

---

## 🚀 Phased Action Plan

### Phase 1 — Standardize All Existing Repos (This Week)
- [ ] Add `shadowrealm.plugin.json` to: CulinaryOS, RecipeOS, NexCMS, Post-Pilot, RestRevive-AI, BibleDesk
- [ ] Add `CONTRIBUTING.md` to all public repos
- [ ] Create `mcp-registry.json` in this ShadowRealm repo
- [ ] Tag all repos with GitHub topic: `shadowrealm-ecosystem`

### Phase 2 — Build the MCP Server Router (Week 2–3)
- [ ] Create `ShadowRealm/server/` — Node.js/Express MCP gateway
- [ ] On startup: reads `mcp-registry.json`, fetches each plugin manifest, registers tools
- [ ] Each tool becomes a callable API route: `POST /mcp/invoke/{tool_name}/{endpoint_name}`
- [ ] Add JWT auth middleware
- [ ] Deploy to Railway/Render (internet) + run locally on port 3000

### Phase 3 — ShadowBot Integration (Week 3–4)
- [ ] ShadowBot reads the MCP server's tool list at runtime
- [ ] ShadowBot can call any registered tool via natural language commands
- [ ] Web chat interface for ShadowBot in the ShadowRealm portal

### Phase 4 — Web Portal + Desktop App (Week 4–6)
- [ ] Next.js portal: dashboard showing all tools, their status, and quick-launch
- [ ] Electron wrapper for desktop (local-first, offline-capable)
- [ ] Users can download the app OR access at shadowrealm.app (or your domain)

### Phase 5 — SaaS + Contributor Layer (Week 6+)
- [ ] Public users can access ShadowBot + approved tools via web
- [ ] Private tools (Shoreline) remain gated behind auth
- [ ] Contributors fork individual project repos → submit PRs → auto-updates flow into ShadowRealm via plugin manifest versioning

---

## 📐 New Project Onboarding Standard

**Every new project you build from this point forward must follow this checklist before being considered "ShadowRealm-ready":**

- [ ] Repo created under `ShadowWalkerNC`
- [ ] `shadowrealm.plugin.json` added at root (defines MCP tool name, endpoints, capabilities)
- [ ] `CONTRIBUTING.md` added
- [ ] `README.md` includes "Part of the ShadowRealm Ecosystem" badge/section with link back here
- [ ] Added to `mcp-registry.json` in this repo
- [ ] Row added to the Project Registry table above
- [ ] GitHub topic `shadowrealm-ecosystem` added to repo
- [ ] Local dev port assigned (no conflicts — see port allocation below)

### Port Allocation (Local Dev)

| Project | Local Port |
|---|---|
| ShadowRealm Gateway | 3000 |
| CulinaryOS API | 4001 |
| RecipeOS API | 4002 |
| NexCMS API | 4003 |
| Post-Pilot API | 4004 |
| RestRevive-AI API | 4005 |
| BibleDesk API | 4006 |
| Shoreline API | 4007 |
| Next New Project | 4008+ |

---

## 🤝 Contributing to Individual Projects

Each project repo is independently forkable. Contributors should:
1. Fork the individual project repo (e.g., [CulinaryOS](https://github.com/ShadowWalkerNC/CulinaryOS))
2. Follow that project's `CONTRIBUTING.md`
3. Submit PRs to the project repo — NOT to this ShadowRealm hub repo
4. This hub only receives updates when the plugin manifest or registry changes

---

## 📁 This Repo's File Structure

```
ShadowRealm/
├── SHADOW_REALM_ECOSYSTEM.md   ← You are here (master blueprint)
├── mcp-registry.json           ← Master tool registry ShadowBot reads
├── README.md                   ← Public-facing intro
├── server/                     ← MCP gateway server (Phase 2)
│   ├── index.js
│   ├── routes/
│   └── middleware/
├── portal/                     ← Web dashboard (Phase 4)
└── desktop/                    ← Electron shell (Phase 4)
```

---

*Last updated: June 20, 2026 | Maintained by [@ShadowWalkerNC](https://github.com/ShadowWalkerNC)*
