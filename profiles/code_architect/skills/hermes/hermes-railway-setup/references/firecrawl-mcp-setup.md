# Firecrawl MCP Server — Setup Reference

Source: https://github.com/mendableai/firecrawl-mcp-server

## What it provides

16 tools via MCP stdio (npx -y firecrawl-mcp):

| Tool | Description |
|------|-------------|
| `firecrawl_scrape` | Scrape a single URL → clean markdown/HTML/links |
| `firecrawl_search` | Web search + optionally extract content from results |
| `firecrawl_crawl` | Crawl entire site, extract all pages |
| `firecrawl_extract` | LLM-powered structured data extraction from pages |
| `firecrawl_agent` | Autonomous deep research agent (separate AI agent) |
| `firecrawl_map` | Discover all indexed URLs on a site |
| `firecrawl_interact` | Browser interaction: click, navigate, fill forms |
| `firecrawl_check_crawl_status` | Poll status of a crawl job |
| `firecrawl_agent_status` | Poll status of an agent job |
| `firecrawl_search_feedback` | Send feedback on a search result |
| `firecrawl_parse` | Parse local file (self-hosted only) |
| `firecrawl_interact_stop` | End an interact session |
| `firecrawl_browser_*` | (Deprecated) browser session management |

## Required env var

`FIRECRAWL_API_KEY` — get from https://www.firecrawl.dev/app/api-keys

## config.yaml block

```yaml
mcp_servers:
  firecrawl:
    command: npx
    args:
      - -y
      - firecrawl-mcp
    env:
      FIRECRAWL_API_KEY: fc-<your-key>
```

Also add to `/data/.env`:
```
FIRECRAWL_API_KEY=fc-<your-key>
```

## Optional env vars (retry / credit tuning)

```
FIRECRAWL_RETRY_MAX_ATTEMPTS=3        # default 3
FIRECRAWL_RETRY_INITIAL_DELAY=1000    # ms, default 1000
FIRECRAWL_RETRY_MAX_DELAY=10000       # ms, default 10000
FIRECRAWL_RETRY_BACKOFF_FACTOR=2      # default 2
FIRECRAWL_API_URL=https://...         # only for self-hosted
```

## Verification

```bash
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes mcp test firecrawl
# Expected: ✓ Connected (Nms) + ✓ Tools discovered: 16

# Live scrape test:
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes -z \
  "Use firecrawl_scrape to scrape https://example.com and return the title"
# Expected response: "Example Domain"
```

## Known issues / pitfalls

- `hermes mcp add --args -y firecrawl-mcp` fails — argparse interprets `-y` as a CLI flag. Always write directly to `config.yaml`.
- Requires `node` / `npx` to be installed. On this Railway deployment: `node v20.19.2`, `npx 9.2.0` at `/usr/bin/`.
- First connection is slow (~3-4s) because npx downloads the package on first run; subsequent connections are cached.
