# Diagnostic Run — 2025-05-17

First full system check after initial setup (Supermemory + Firecrawl MCP).

## Results

| Check | Status | Detail |
|---|---|---|
| Identity | ✅ | Profile: default, Model: claude-sonnet-4.6 / openrouter, hermes-agent 0.14.0 |
| Memory | ✅ | Supermemory active, write+recall round-trip confirmed (ID: aUHrAVQKax6y4a6k9kWQxu) |
| SearXNG | ⚠️ | Internal URL `SearXNG.railway.internal:8080` timed out. `SEARXNG_URL` env var was not set. Public URL found via `RAILWAY_SERVICE_SEARXNG_RAILWAY_URL`. Used Firecrawl news search as fallback. |
| Browser/Scrape | ✅ | Firecrawl scrape of example.com: title "Example Domain", status 200 |
| File I/O | ✅ | `/data/home/workspace/test_output.txt` created, 18 bytes |
| Config | ✅ reviewed | SOUL.md exists at `/data/SOUL.md` but is blank template only |

## SearXNG env state at time of check
```
SEARXNG_URL=          (empty / not wired)
RAILWAY_SERVICE_SEARXNG_RAILWAY_URL=searxng-railway-production-e024.up.railway.app
```

## Key finding: execute_code timeout
Using `execute_code` with a `curl` call to the unreachable internal SearXNG URL
caused a full 300-second script timeout. Always use `terminal(timeout=15)` for
network probes so you get a fast BLOCKED instead of hanging.

## Config at time of check (`/data/config.yaml`)
```yaml
model:
  provider: openrouter
  default: anthropic/claude-sonnet-4.6
memory:
  provider: supermemory
mcp_servers:
  firecrawl:
    command: npx
    args: [-y, firecrawl-mcp]
    env:
      FIRECRAWL_API_KEY: fc-f6b...9a3e
```
