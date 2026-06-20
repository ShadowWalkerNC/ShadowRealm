# ShadowRealm Network — App Contract v1.0

Every app in the **ShadowWalkerNC ecosystem** follows this contract.
This file is identical across all repos. Do not modify it per-app —
use `V1_API.md` for app-specific tool documentation.

---

## Purpose

The ShadowRealm Network (SRN) allows every app to:
- **Discover** what other apps can do (via `/v1/manifest`)
- **Call** other apps as tools over authenticated HTTP
- **Report** health status to the ShadowRealm orchestrator
- Stay **independent** (each app runs and deploys on its own) while being **interconnected** (any app can call any other)

---

## Required Endpoints

Every SRN-compliant app MUST implement these three routes:

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /v1/health` | None | Liveness check — always public |
| `GET /v1/manifest` | Bearer token | Machine-readable tool list |
| `POST /v1/<tool_name>` | Bearer token | Execute a tool |

---

## Authentication

All `/v1/*` routes **except `/v1/health`** require:

```http
Authorization: Bearer <api_key>
X-SRN-App: <calling_app_name>
```

- `api_key` — an app-specific key issued by the receiving app
- `X-SRN-App` — identifies the caller. Used for logging and rate-limiting.

---

## Standard Response Envelope

```json
{ "success": true,  "data": { ... } }
{ "success": false, "error": "Human readable message", "code": "MACHINE_CODE" }
```

HTTP status codes: `200` success · `400` bad input · `401` unauth · `403` forbidden · `404` not found · `500` error

---

## Required `.env` Keys (every app)

```bash
SRN_APP_NAME=your-app-name
SRN_SECRET=srn_live_xxx
SRN_REGISTRY_URL=https://shadowrealm.railway.app
```

---

## App Registry

Canonical list: [`SRN_REGISTRY.json`](./SRN_REGISTRY.json) in `ShadowWalkerNC/ShadowRealm`.

| App | Stack | Role |
|-----|-------|------|
| **post-pilot** | Python/Flask | Social media engine |
| **sigil** | Node/Discord.js | Discord bot + ops |
| **shadowrealm** | Node/Express | Orchestrator |

---

## Versioning

- Contract version lives in this file's header (`v1.0`)
- Breaking changes bump the major version and require migration notes
- Additive changes (new tools, new optional fields) are non-breaking
