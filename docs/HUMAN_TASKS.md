# ShadowRealm — Human Tasks

Things that cannot be automated by the AI build agent (file too large to patch safely,
requires local testing, or needs a one-time manual decision). Clear each item after it
is done and commit the update.

---

## Pending

### ▢ C06 — Wire `/status` route into `app.py`

Two lines to add manually:

**1. Near the other route imports** (alongside the `setup_auth_routes` import, ~line 90):

```python
from src.status_route import register_status_route
```

**2. Near the bottom where routes are registered** (right after `setup_auth_routes(app, ...)`):

```python
register_status_route(app)
```

Once added, `GET /status` is live and auth-gated identically to every other UI page.
Verify by visiting `http://localhost:7860/status` after restart.

---

## Completed

*(Move items here when done, with the date.)*
