# Camofox Railway Deployment Reference

## Repository
- URL: https://github.com/jo-inc/camofox-browser
- Default branch: **`master`** (not `main` — Railway defaults to `main` and will fail)
- License: MIT | Stars: ~5k | Language: Node.js/TypeScript

## What It Is
Self-hosted Node.js server wrapping Camoufox (Firefox fork with C++ fingerprint
spoofing). Bypasses Cloudflare, bot detection, and social media scraping blocks.
Drop-in anti-detection replacement for Puppeteer/Playwright. When `CAMOFOX_URL`
is set in Hermes, all browser tools route through it automatically.

## Railway Deployment Steps

1. **New Service → GitHub Repo → `jo-inc/camofox-browser`**
2. **Change branch from `main` → `master`** (Settings → Source → Branch)
3. Railway auto-detects `railway.toml`, uses `Dockerfile.ci` (downloads Camoufox binary at build time via GitHub releases — no bind mounts, no Makefile needed)
4. Build takes ~3–5 min (downloads Firefox/Camoufox binary)
5. Health check: `/health`, timeout 120s — Railway waits for this before marking live

### `railway.toml` (already in repo, for reference)
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile.ci"

[deploy]
startCommand = "sh -c 'CAMOFOX_PORT=${PORT:-9377} node --max-old-space-size=${MAX_OLD_SPACE_SIZE:-128} server.js'"
healthcheckPath = "/health"
healthcheckTimeout = 120
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

## Environment Variables to Set on Camofox Service

| Variable | Value | Notes |
|---|---|---|
| `PORT` | `9377` | Fix port for predictable private URL |
| `MAX_OLD_SPACE_SIZE` | `512` | Node heap MB; default 128 is too small for multiple sessions |
| `SESSION_TIMEOUT_MS` | `3600000` | 1hr session timeout — good for social media |
| `CAMOFOX_API_KEY` | any secret | Enables cookie import endpoint |
| `CAMOFOX_CRASH_REPORT_ENABLED` | `false` | Optional: disable telemetry |

## Volume for Persistence
Add a Railway Volume mounted at `/root/.camofox` on the Camofox service.
This is where session profiles, cookies, and login state are stored.
Without it, everything is wiped on redeploy.

Key subdirectories:
- `/root/.camofox/profiles/` — persistent Firefox profiles keyed by userId
- `/root/.camofox/cookies/` — cookie files
- `/root/.camofox/traces/` — session trace zips (TTL 24h)

## Hermes-Side Config

```bash
# /data/.env
CAMOFOX_URL=http://camofox-browser.railway.internal:9377
```

```yaml
# /data/config.yaml
browser:
  camofox:
    managed_persistence: true   # stable userId → cookies/logins survive between tasks
```

**Nested path is critical.** `managed_persistence: true` at top level is silently
ignored by Hermes. Must be at `browser.camofox.managed_persistence`.

## API Endpoints (Key ones)

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | Health check — no auth required |
| POST | `/tabs` | Create tab. Body: `{url, userId, sessionKey}` — both required |
| GET | `/tabs/:id/snapshot?userId=` | Accessibility tree. userId required |
| GET | `/tabs/:id/screenshot?userId=` | PNG screenshot. userId required |
| DELETE | `/tabs/:id?userId=` | Close tab |
| DELETE | `/sessions/:userId` | Wipe all session data for a user |
| GET | `/docs` | Swagger UI |

## Confirmed Working (May 2026)
- Private URL: `http://camofox-browser.railway.internal:9377`
- Health response: `{"ok":true,"engine":"camoufox","browserConnected":true,"browserRunning":true}`
- Twitter/X opened cleanly: standard login page, no bot detection, no CAPTCHA
- Screenshot confirmed via vision_analyze

## Optional: Advanced Config Keys

```yaml
browser:
  camofox:
    managed_persistence: true
    user_id: shared-camofox        # Pin to a specific userId (externally managed sessions)
    session_key: visible-tab       # Pin to a specific tab's listItemId
    adopt_existing_tab: true       # Reuse an existing tab before creating a new one
```

Env var equivalents: `CAMOFOX_USER_ID`, `CAMOFOX_SESSION_KEY`, `CAMOFOX_ADOPT_EXISTING_TAB`
