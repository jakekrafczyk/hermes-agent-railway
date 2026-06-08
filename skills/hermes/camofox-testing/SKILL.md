---
name: camofox-testing
description: Test Camofox browser end-to-end — public pages and authenticated (cookie-injected) platforms. Covers the full API pipeline, quirk discoveries, and auth-gate handling.
version: 1.0.0
---

# Camofox Testing Runbook

End-to-end verification of the Camofox browser service on Railway. Tests the full
researcher profile runbook: create tab, accessibility snapshot, schema extraction,
screenshot, cookie injection, auth gate detection, cleanup.

## Prerequisites Check

```bash
# Health
timeout 5 curl -s http://camofox-browser.railway.internal:9377/health
# Config
grep -A 3 'camofox:' /data/config.yaml
# Env
grep CAMOFOX_URL /data/.env
# Cookies dir
ls -la /data/camofox/cookies/
```

---

## Test #1: Public Page Pipeline

Exercises 4 of 6 runbook steps. No cookies needed.

### Commands

```bash
# A. Create tab + navigate
curl -s -X POST http://camofox-browser.railway.internal:9377/tabs \
  -H "Content-Type: application/json" \
  -d '{"userId":"test","sessionKey":"test","url":"https://en.wikipedia.org/wiki/Browser_automation"}'
# → tabId

# B. Snapshot (wait 3s)
sleep 3
curl -s "http://camofox-browser.railway.internal:9377/tabs/$TAB_ID/snapshot?userId=test"

# C. Extract (REQUIRES x-ref selectors from snapshot)
curl -s "http://camofox-browser.railway.internal:9377/tabs/$TAB_ID/extract" \
  -H "Content-Type: application/json" \
  -d '{"userId":"test","schema":{"type":"object","properties":{"title":{"type":"string","x-ref":"e3"},"section":{"type":"string","x-ref":"e11"}}}}'

# D. Screenshot
curl -s "http://camofox-browser.railway.internal:9377/tabs/$TAB_ID/screenshot?userId=test" \
  -o /tmp/camofox-shot.png

# E. Cleanup
curl -s -X DELETE "http://camofox-browser.railway.internal:9377/tabs/$TAB_ID?userId=test"
```

### Verified Results (2026-05-22)

| Step | Status | Detail |
|------|--------|--------|
| Tab create | ✅ | Wikipedia article loaded, redirect followed |
| Snapshot | ✅ | Full accessibility tree, `@e1`–`@e27` refs |
| Extract | ✅ | `x-ref` selectors work, values returned |
| Screenshot | ✅ | 1280×720 PNG, 192KB |
| Delete | ✅ | `ok: true` |

### Quirks Discovered

| # | Quirk | Detail |
|---|-------|--------|
| 1 | **Extract needs x-ref** | Without `x-ref` pointing to a snapshot ref ID, all values return `null` |
| 2 | **Arrays unsupported** | Extract schemas only support `"type": "string"`. Arrays and nested objects rejected |
| 3 | **userId placement varies** | Tab create: body. Snapshot/screenshot: query param. Extract: MUST be in POST body |
| 4 | **Redirect handling** | Camofox follows HTTP redirects gracefully (Wikipedia → canonical URL) |

---

## Test #2: Authenticated Platform (LinkedIn)

Exercises the full cookie → injection → navigate → auth-gate detection flow.

### Cookie Format

Cookies must be an object with a `"cookies"` array:
```json
{
  "cookies": [
    {"name":"li_at","value":"AQEDAS...","domain":".www.linkedin.com","path":"/","secure":true,"httpOnly":true,"sameSite":"Lax",...}
  ]
}
```

**Convert Netscape format:**
```python
import json
cookies = []
with open("cookies.txt") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"): continue
        parts = line.split("\t")
        if len(parts) < 7: continue
        domain, flag, path, secure_str, exp_str, name, value = parts
        value = value.strip('"')
        expiration = int(exp_str) if exp_str != "0" else None
        c = {"name":name,"value":value,"domain":domain,"path":path,"secure":secure_str=="TRUE","httpOnly":False,"sameSite":"Lax"}
        if expiration: c["expirationDate"] = expiration
        cookies.append(c)
with open("output.json","w") as f: json.dump({"cookies":cookies}, f, indent=2)
```

### Cookie Injection

```bash
source /data/profiles/researcher/.env  # provides CAMOFOX_API_KEY
curl -s -X POST "http://camofox-browser.railway.internal:9377/sessions/<USER_ID>/cookies" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CAMOFOX_API_KEY" \
  -d @/data/camofox/cookies/<platform>_<account>.json
```

**⚠️ Critical:** Auth header must be `Authorization: Bearer <key>`. 
`x-api-key`, `api-key`, query param `apiKey`, and other variations all return `Forbidden`.

### Setting up CAMOFOX_API_KEY

The key can be set on EITHER:
1. **The Camofox Railway service** as an env var (global for all clients) — recommended
2. **A profile's `.env` file** (`/data/profiles/<profile>/.env`) — per-profile isolation

The curl or script sourcing that `.env` provides the key at call time via the `Authorization: Bearer` header.

### Auth-Gate Detection

After navigating via the Hermes browser tool (which routes through Camofox when CAMOFOX_URL is set), inspect the snapshot:

- **"Welcome back" + account name** → ✅ Partially authenticated (cookies recognized, may need password re-auth for headless browsers)
- **"Sign in" heading** → ❌ Full auth gate (cookies not recognized or expired)
- **"Choose an account"** + multiple account buttons → ✅ Cookies recognized, account selection page
- **Feed/Navigation elements visible** → ✅ Fully authenticated

### Verified Results (2026-05-22)

| Step | Status | Detail |
|------|--------|--------|
| Cookie conversion | ✅ | 30 cookies from Netscape → JSON |
| Cookie placement | ✅ | `/data/camofox/cookies/linkedin_default.json` |
| Cookie injection | ✅ | `POST /sessions/researcher/cookies` → `ok: true, count: 30` |
| Auth gate | ⚠️ Partial | Account recognized ("Welcome back, Jake Krafczyk"), password re-auth required |
| Key insight | 🔑 | Cookies ARE injected and LinkedIn recognizes them. Headless-browser security triggers password verification |

### Key Auth Cookies Required for LinkedIn

| Cookie | Domain | Purpose |
|--------|--------|---------|
| `li_at` | `.www.linkedin.com` | Primary auth session token |
| `JSESSIONID` | `.www.linkedin.com` | Session identifier |
| `lidc` | `.linkedin.com` | Login state cookie |
| `liap` | `.linkedin.com` | Auth persistence flag |
| `bcookie` | `.linkedin.com` | Browser cookie |
| `bscookie` | `.www.linkedin.com` | Secure browser cookie |

---

## Troubleshooting

### Cookie injection returns "Forbidden"
- Wrong auth header — use `Authorization: Bearer <key>`, not `x-api-key`
- API key not set — check `CAMOFOX_API_KEY` in env

### Cookies injected but LinkedIn shows login page
- Cookies may be in wrong format — needs `{"cookies": [...]}` wrapper, not bare array
- UserId mismatch — tab must use same userId as cookie injection
- LinkedIn's headless-browser detection triggers password re-auth (expected)

### Extract returns null for all fields
- Missing `x-ref` in schema properties — must point to snapshot ref IDs like `"x-ref": "e3"`
