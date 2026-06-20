# Post-Pilot → ShadowRealm Network Bridge

This document describes how **Post-Pilot**, **Sigil**, and **ShadowRealm** communicate within the SRN ecosystem.

---

## Architecture

```
Discord User
    │
    │  /post topic:"Taco Tuesday is back!"
    ▼
SIGIL (Discord bot — Railway)
    │
    │  POST https://<POSTPILOT_URL>/v1/generate_and_publish
    │  Authorization: Bearer <POSTPILOT_API_KEY>
    │  X-SRN-App: sigil
    ▼
POST-PILOT (Flask — Render)
    │
    ├── OpenAI → generate caption + hashtags
    │
    ├── Facebook Graph API
    ├── Instagram Content API
    ├── TikTok Open API
    ├── YouTube Data API
    ├── Google My Business API
    └── Post-Pilot Website Hub
    │
    ▼
SIGIL replies with embed:
    ✅ Published! [caption] [hashtags] ✅ Facebook ✅ Instagram
```

---

## Sigil → Post-Pilot: API Contract

### Authentication
All Sigil requests include:
```
Authorization: Bearer <POSTPILOT_API_KEY>
X-SRN-App: sigil
Content-Type: application/json
```

### Endpoints used by Sigil

| Command | Endpoint | Purpose |
|---------|----------|---------|
| `/post` | `POST /v1/generate_and_publish` | One-shot generate + publish |
| `/postgenerate` | `POST /v1/generate_post` | Preview caption only |
| `/postgenerate` → Publish Now | `POST /v1/publish_post` | Publish a pre-generated caption |
| `/poststatus` | `GET /v1/health` | Health check |
| `/poststatus` | `GET /v1/get_history` | Last N posts |

### Request: `POST /v1/generate_and_publish`
```json
{
  "topic":     "Taco Tuesday is back!",
  "tone":      "exciting",
  "platforms": ["facebook", "instagram"],
  "image_url": "https://cdn.example.com/taco.jpg",
  "user_id":   "usr_abc123"
}
```

### Response
```json
{
  "success": true,
  "data": {
    "caption":  "🌮 It’s Taco Tuesday and we’re bringing the heat!",
    "hashtags": ["#TacoTuesday", "#FoodTruck", "#NomNom"],
    "post_id":  "post_1234567890",
    "results": {
      "facebook":  { "success": true,  "url": "https://facebook.com/..." },
      "instagram": { "success": true,  "url": "https://instagram.com/..." },
      "tiktok":    { "success": false, "error": "Not connected" }
    }
  }
}
```

---

## ShadowRealm → Post-Pilot: Health Monitoring

ShadowRealm pings `GET /v1/health` every 5 minutes per `SRN_REGISTRY.json`.

Expected response:
```json
{ "status": "ok", "version": "1.0.0", "uptime": 3600 }
```

If health check fails, ShadowRealm sends an alert to the `srn-alerts` Discord channel via Sigil.

---

## Environment Variables

### Post-Pilot (Render)
```bash
FLASK_SECRET_KEY=<random 32+ char string>
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
REDIRECT_URI=https://<your-postpilot-domain>/auth/facebook/callback
GOOGLE_REDIRECT_URI=https://<your-postpilot-domain>/auth/google/callback
TIKTOK_REDIRECT_URI=https://<your-postpilot-domain>/auth/tiktok/callback
DATABASE_PATH=postpilot.db
```

### Sigil (Railway)
```bash
DISCORD_TOKEN=
DISCORD_CLIENT_ID=
POSTPILOT_URL=https://<your-postpilot-domain>
POSTPILOT_API_KEY=pp_live_...
POSTPILOT_USER_ID=usr_...
POSTPILOT_SRN_APP=sigil
POSTPILOT_TIMEOUT_MS=12000
```

---

## Generating a Post-Pilot API Key

After deploying Post-Pilot:

1. Log in at `https://<your-postpilot-domain>`
2. Go to **Settings → API Keys**
3. Click **Create Key** — name it `sigil`
4. Copy the `pp_live_...` key
5. Set it as `POSTPILOT_API_KEY` in Sigil's Railway environment
6. Set your Post-Pilot `user_id` as `POSTPILOT_USER_ID`

---

## Updating Live URLs

After each deploy, update `SRN_REGISTRY.json`:

```json
"postpilot": {
  "live_url": "https://post-pilot.onrender.com"
},
"sigil": {
  "live_url": "https://sigil-production.up.railway.app"
}
```
