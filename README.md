# ShadowRealm

The **orchestrator, app registry, and AI agent dispatcher** for the ShadowWalkerNC ecosystem.

ShadowRealm is the hub that connects all ShadowWalkerNC apps — it knows what every app can do, routes events between them, and provides a single AI agent interface across the entire network.

---

## The Network

| App | Stack | Purpose | SRN Ready |
|-----|-------|---------|----------|
| [Post-Pilot](https://github.com/ShadowWalkerNC/Post-Pilot) | Python/Flask | Social media posting engine | 🔨 Building |
| [Sigil](https://github.com/ShadowWalkerNC/Sigil) | Node/Discord.js | Discord bot — culinary ops + community | 🔨 Building |
| [CulinaryOS](https://github.com/ShadowWalkerNC/CulinaryOS) | Kotlin + React/Supabase | Culinary intelligence platform | 📋 Planned |
| [Sylvia-Ross-MC](https://github.com/ShadowWalkerNC/Sylvia-Ross-MC) | JavaScript | Mission control dashboard | 📋 Planned |
| [ShadowBot](https://github.com/ShadowWalkerNC/ShadowBot) | TBD | AI agent system (Odysseus) | 📋 Planned |
| [NexCMS](https://github.com/ShadowWalkerNC/NexCMS) | React/Supabase | Website builder + CMS | 📋 Planned |
| [RecipeOS](https://github.com/ShadowWalkerNC/RecipeOS) | Kotlin/Android | Recipe + kitchen management | 📋 Planned |
| [RestRevive AI](https://github.com/ShadowWalkerNC/RestRevive-AI) | React/Supabase | Restaurant ops intelligence | 📋 Planned |
| [BibleDesk](https://github.com/ShadowWalkerNC/BibleDesk) | React/Supabase | AI Bible evidence platform | 📋 Planned |

---

## How It Works

Every app in the network:
1. Exposes `GET /v1/health` and `GET /v1/manifest`
2. Implements `POST /v1/<tool>` routes for callable actions
3. Is registered in `SRN_REGISTRY.json`

ShadowRealm fetches every app's manifest on startup and can call any tool on any app as if it were a local function.

```
ShadowRealm
  ├── fetches /v1/manifest from all apps
  ├── routes events between apps
  ├── provides unified AI agent interface
  └── monitors /v1/health on all apps
```

---

## Files

| File | Purpose |
|------|---------|
| `SRN_REGISTRY.json` | Master list of all apps in the network |
| `SHADOWREALM_NETWORK.md` | The contract every app must implement |
| `orchestrator/` | ShadowRealm runtime (coming soon) |

---

## Contract

See [SHADOWREALM_NETWORK.md](./SHADOWREALM_NETWORK.md) for the full spec every app must follow.

---

*ShadowWalkerNC ecosystem — independent apps, interconnected network.*
