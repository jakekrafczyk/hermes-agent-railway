---
name: hermes-system-check
description: "Repeatable system health check for a Hermes Railway deployment — identity, memory, search, scraping, file I/O, and config review."
triggers:
  - system check
  - health check
  - is everything working
  - verify setup
  - check all tools
  - diagnostic
  - confirm setup
  - what model are you using
  - is supermemory connected
  - check my config
---

# Hermes System Health Check

A 6-check procedure for verifying a Hermes Railway deployment end-to-end.
Run this after initial setup, after config changes, or whenever something feels
off. Each check is independent — report pass/fail/needs-attention per check.

## Check Order & What to Test

### 1. Identity
```bash
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes profile
cat /data/config.yaml
```
Report: agent name, active profile, model + provider, Hermes version.

### 2. Memory (Supermemory)
```bash
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes memory status
```
Then: call `supermemory_store` with a timestamped test entry, call
`supermemory_search` to retrieve it back and confirm round-trip.

Expected: `Plugin: installed ✓`, `Status: available ✓`

### 3. Web Search (SearXNG)
Use `terminal` (not `execute_code`) with `--max-time 10` or `timeout=15`:
```bash
curl -s --max-time 10 "${SEARXNG_URL}/search?q=test&format=json"
```
If SearXNG times out, check for public URL: `printenv | grep -i searxng`
and look for `RAILWAY_SERVICE_SEARXNG_RAILWAY_URL`. Fall back to
`mcp_firecrawl_firecrawl_search` if needed — still report SearXNG as
⚠️ needs attention.

### 4. Browser / Scrape

**If `CAMOFOX_URL` is set**, health-check Camofox first:
```bash
timeout 10 curl -s "$CAMOFOX_URL/health"
# Expected: {"ok":true,"engine":"camoufox","browserConnected":true,"browserRunning":true,...}
```
Then open a test page via the API:
```bash
# Create tab
curl -X POST "$CAMOFOX_URL/tabs" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","userId":"hermes-default","sessionKey":"diag"}'
# Snapshot (use returned tabId)
curl "$CAMOFOX_URL/tabs/<tabId>/snapshot?userId=hermes-default"
# Clean up
curl -X DELETE "$CAMOFOX_URL/tabs/<tabId>?userId=hermes-default"
```

**Always also test Firecrawl scrape** (used for public web scraping regardless of browser backend):
```python
mcp_firecrawl_firecrawl_scrape(url="https://example.com", formats=["markdown"])
```
Confirm: title = "Example Domain", status 200.

Report both: Camofox (anti-detection browser) + Firecrawl (cloud scraper) as separate sub-checks.

### 5. File Creation
```python
write_file("/data/home/workspace/test_output.txt", "Hermes is working.")
```
Read it back and confirm content + size.

### 6. Settings Review
Check:
- `cat /data/config.yaml` → default model
- `cat /data/SOUL.md` → persona defined or blank template?
- Any obvious gaps for the user's stated use case

## SOUL.md Location & Default State
- Path: `/data/SOUL.md`
- Default state: **blank template** (comment block only, no persona defined)
- For marketing/automation use cases, recommend filling it in with a persona

## Reporting Format

Use a table per check with status emoji: ✅ PASS / ⚠️ NEEDS ATTENTION / ❌ FAIL.
End with a 3-item "recommended next steps" list tuned to what's broken or missing.

## Summary Report Template

| Check | Status | Notes |
|---|---|---|
| 1. Identity | ✅/⚠️/❌ | ... |
| 2. Memory | ✅/⚠️/❌ | ... |
| 3. Web Search | ✅/⚠️/❌ | ... |
| 4. Browser/Scrape | ✅/⚠️/❌ | ... |
| 5. File I/O | ✅/⚠️/❌ | ... |
| 6. Config | ✅/⚠️/❌ | ... |

## Common Issues & Fixes

| Symptom | Fix |
|---|---|
| SearXNG internal URL timeout | Use public URL from `RAILWAY_SERVICE_SEARXNG_RAILWAY_URL` |
| `execute_code` + curl hangs 300s | Always use `terminal(timeout=15)` for network probes |
| SOUL.md blank | Edit `/data/SOUL.md` with persona — no restart needed |
| Memory status "not configured" | Run `hermes config set memory.provider supermemory` + add key to `/data/.env` |
| MCP tools missing | Run `hermes mcp list` and `hermes mcp test firecrawl` |
| Camofox health returns connection error | Check service is deployed; verify `$CAMOFOX_URL` is set and reachable (typically `http://camofox-browser.railway.internal:9377`) |
| Camofox tab creation returns `{"error":"userId and sessionKey required"}` | Both `userId` and `sessionKey` fields are required in the POST body |
| Camofox snapshot returns 400 `userId required` | Pass `?userId=hermes-default` as query param on GET endpoints |
| Camofox browser tools fall through to local Chrome (not found error) | `CAMOFOX_URL` not loaded in current session env — verify it's in `/data/.env` and session was restarted after adding it |
| **auto_recall: true burns 40k+ tokens/turn on OpenRouter** | Check `/data/supermemory.json` — if `auto_recall: true`, every turn prefetches and injects growing `<supermemory-context>` block. Set to `false`. See `hermes-railway-setup` references/supermemory-setup.md for full diagnosis. |

## Reference Runs

- `references/diagnostic-run-2025-05-17.md` — first full check after Supermemory + Firecrawl setup; SearXNG was unreachable (private URL not yet wired), all other checks passed.
- Second run (same session, after fixes): SearXNG fixed via private URL `searxng-railway.railway.internal:8080`; Camofox deployed and added; all 6 checks passed.

## Pitfalls

- **Do NOT use `execute_code` for network timeout probes.** If the host is
  unreachable, `execute_code` will hang the full 300-second script timeout.
  Always use `terminal(command="curl --max-time 10 ...", timeout=15)`.
- **Firecrawl Python SDK (execute_code) returns Pydantic models, not dicts.**
  `app.scrape(...)` returns a `Document` object — access fields as attributes
  (`.markdown`, `.metadata.title`), not dict keys (`["markdown"]`). See
  `hermes-railway-setup` references/firecrawl-sdk-v4-usage.md for full API.
- **Firecrawl screenshot URLs** from `firecrawl_scrape` are signed GCS URLs —
  they expire and may have partial signatures when copy-pasted. Use them
  immediately via `vision_analyze` or include the full URL verbatim.
