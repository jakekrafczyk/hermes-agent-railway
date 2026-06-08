# Camofox Authenticated Path (Researcher Profile)

When operating under the `researcher` Hermes profile (HERMES_HOME=/data/profiles/researcher),
the AGENTS.md mandates this path for authenticated platforms including Reddit.

## Model Switching

Switch to **DeepSeek Pro** before starting any authenticated social media phase:

```
/hermes model deepseek/deepseek-v4-pro
```

Return to the default model after the authenticated phase completes.

## Prerequisites Check

Before starting, verify Camofox is reachable:

```bash
# 1. Check env var (preferred URL — uses Railway private DNS)
echo "CAMOFOX_URL=$CAMOFOX_URL"

# 2. Health check (use CAMOFOX_URL, not localhost — services are on separate hosts)
timeout 5 curl -s "$CAMOFOX_URL/health"

# 3. Cookie directory
ls /data/camofox/cookies/
```

## Runbook

### A. Locate Session Cookies

```bash
ls /data/camofox/cookies/
```

Naming convention: `<platform>_<account_id>.json` (e.g., `reddit_default.json`).

Cookies must be in plain JSON array format — each object with `name`, `value`, `domain`,
`path`, `httpOnly`, `secure`, `sameSite` fields. If the cookie file is in hotcleaner.com
Cookie Editor's vcrv1 binary format, see `references/cookie-formats.md` for decoding.

### B. Inject Cookies

```bash
curl -s -X POST "$CAMOFOX_URL/sessions/<USER_ID>/cookies" \
  -H "Content-Type: application/json" \
  -d '{"cookies": [{"name":"reddit_session","value":"...","domain":".reddit.com","path":"/","httpOnly":true,"secure":true}]}'
```

### C. Create Tab and Navigate

```bash
curl -s -X POST "$CAMOFOX_URL/tabs" \
  -H "Content-Type: application/json" \
  -d '{"userId": "<USER_ID>", "sessionKey": "<SESSION_KEY>", "url": "https://old.reddit.com/r/SUBREDDIT/"}'
```

Capture returned `tabId`.

### D. Accessibility Snapshot

```bash
curl -s "$CAMOFOX_URL/tabs/${TAB_ID}/snapshot?userId=${USER_ID}"
```

Parse the accessibility tree for post titles, authors, scores, and permalinks.
Ref IDs (e.g., `@e5`, `@e12`) map to interactive elements.

### E. Schema Extraction (per post)

```bash
curl -s -X POST "$CAMOFOX_URL/tabs/${TAB_ID}/extract" \
  -H "Content-Type: application/json" \
  -d '{"userId": "<USER_ID>", "schema": {"type":"object","properties":{"title":{"type":"string","x-ref":"<TITLE_REF>"},"author":{"type":"string","x-ref":"<AUTHOR_REF>"},"score":{"type":"string","x-ref":"<SCORE_REF>"}}}}'
```

**Extract API quirks (verified 2026-05-22):**

- **`x-ref` selectors are required.** Each property MUST have an `"x-ref"` field
  pointing to a ref ID from the snapshot (e.g., `"e3"`, `"e11"`). Without `x-ref`,
  all values come back `null`.
- **Only `"type": "string"` is supported.** Arrays (`"type": "array"`) and nested
  objects are rejected with `"property has unsupported type"`.
- **`userId` must be in the POST body**, not just in the query string. Passing it
  only as a query param returns `"userId is required"`.
- **Tab create accepts `url` directly.** You can skip a separate navigate call by
  including `"url": "https://..."` in the tab creation payload.
- **Railway private URL:** The Camofox service URL is
  `http://camofox-browser.railway.internal:9377` (not `localhost`). Check
  `$CAMOFOX_URL` for the current value.

### F. Auth-Gate Detection

After snapshot, inspect the output for:
- Login prompts
- CAPTCHA / verification pages
- 2FA requirements
- Paywalls
- Access-denied messages

**If any gate is detected, halt.** Write a triage error state and stop.
Do not retry, do not attempt bypass.

## Triage on Camofox Unavailability

When Camofox is unreachable (CAMOFOX_URL unset, health check fails, cookie directory
missing), the task cannot proceed through the authenticated path. Write an error state
to the Voltaic triage system:

1. Read the schema: `/data/workspace/triage/.schema.json`
2. Generate a UUIDv4 for error_id
3. Write to: `/data/workspace/triage/inbox/error_state_<uuid>.json`

Required fields: `profile` ("researcher"), `error_id` (UUID), `timestamp` (ISO8601),
`error_type` ("tool_unavailable"), `severity` ("blocking"), `step` ("C").

See `references/triage-format.md` for the full schema and example.