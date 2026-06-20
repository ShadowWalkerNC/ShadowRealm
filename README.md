# ShadowRealm

> The orchestrator for the ShadowWalkerNC app ecosystem.

ShadowRealm is the central nervous system of the **ShadowRealm Network (SRN)** — a mesh of independent apps that can discover and call each other as tools.

## What It Does

- **Registry** — `SRN_REGISTRY.json` is the single source of truth listing every app in the network
- **Health Monitor** — pings every app's `/v1/health` every 60s and reports status
- **Manifest Fetcher** — loads every app's `/v1/manifest` on startup so it knows what each app can do
- **Tool Dispatcher** — routes `call tool X on app Y` requests across the network
- **Orchestrator** — chains multi-app workflows (e.g. Sigil event → Post-Pilot publish)

## Network Apps

| App | Role | Stack |
|-----|------|-------|
| [Post-Pilot](https://github.com/ShadowWalkerNC/Post-Pilot) | Social media engine | Python/Flask |
| [Sigil](https://github.com/ShadowWalkerNC/Sigil) | Discord bot + culinary ops | Node/Discord.js |
| ShadowRealm *(this)* | Orchestrator | Node/Express |

## Architecture

```
ShadowRealm
├── SRN_REGISTRY.json            ← source of truth: all apps
├── orchestrator/
│   ├── registry.js              ← loads + caches SRN_REGISTRY.json
│   ├── manifest_fetcher.js      ← fetches /v1/manifest from each app
│   ├── health_monitor.js        ← polls /v1/health, reports outages
│   └── tool_dispatcher.js       ← routes tool calls to the right app
├── server.js                    ← Express entry point + /v1/* routes
├── package.json
└── .env.example
```

## Quick Start

```bash
npm install
cp .env.example .env
# fill in SRN_SECRET (must match all other SRN apps)
node server.js
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/v1/health` | None | Liveness check |
| `GET` | `/v1/manifest` | Bearer | ShadowRealm's own tool list |
| `GET` | `/v1/health_status` | Bearer | Status of all SRN apps |
| `GET` | `/v1/apps` | Bearer | All registered apps + cached tools |
| `GET` | `/v1/find_tool?tool=name` | Bearer | Find which app owns a tool |
| `POST` | `/v1/call_tool` | Bearer | Dispatch a tool call to any app |

## Calling a Tool

```bash
curl -X POST https://shadowrealm.railway.app/v1/call_tool \
  -H 'Authorization: Bearer srn_live_xxx' \
  -H 'X-SRN-App: my-app' \
  -H 'Content-Type: application/json' \
  -d '{"app": "post-pilot", "tool": "publish_post", "input": {"caption": "Brisket Tacos 🔥", "platforms": ["fb","ig"]}}'
```

## Status

🛠️ **Building** — foundation committed. Post-Pilot Session 12 wires up the first real `/v1/` tools.
