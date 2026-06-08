# Web Research Tool Fallback Strategy

When primary web scraping/research tools fail, do NOT block. Pivot to the built-in
fallback stack. This pattern saved a high-priority Composio MCP research task
that Firecrawl (MCP) refused with 401/auth errors.

## Priority Order

| Priority | Tool | Notes |
|----------|------|-------|
| 1 | `firecrawl_scrape` | Primary. `maxAge:0` for live data. JSON format for structured extraction. |
| 2 | `firecrawl_search` | Primary search. Use without `scrapeOptions` first, then scrape results individually. |
| 3 | `firecrawl_map` | URL discovery on a known domain. Use before falling back to agent. |
| 4 | **FALLBACK**: `web_search` | Built-in. Returns titles + URLs + snippets. No auth needed. |
| 5 | **FALLBACK**: `web_extract` | Built-in. Takes URLs from `web_search`, extracts markdown. Up to 5 URLs per call. |
| 6 | `searxng-local` skill | If SEARXNG_URL is set, use curl to the JSON endpoint as another fallback. |
| 7 | `firecrawl_agent` | Last resort for complex multi-page research when all else fails. Async, needs polling. |

## Failure Modes and Diagnosis

| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| Firecrawl returns 401 | API key expired or misconfigured | Pivot to `web_search` + `web_extract` immediately |
| Firecrawl "unreachable after 3 failures" | MCP server down or network issue | Pivot to built-in tools |
| Firecrawl scrape returns empty/minimal content | JS-rendered page or wrong URL | Try `waitFor`, then `firecrawl_map` to find correct URL, then fall back |
| `web_extract` times out or returns error on a URL | Page too large, JS-heavy, or paywalled | Try the other URLs in the search results; one usually works |

## Effective Fallback Workflow

1. Run 2-4 parallel `web_search` calls with different query phrasings
2. Collect the most promising URLs from all results
3. Call `web_extract` on up to 5 URLs at once
4. Piece together findings from extracted content
5. If a specific page is critical and web_extract fails, try `firecrawl_scrape` on that single URL (the tool may have recovered)

## When This Worked

June 2026: Researched Composio MCP integration for Hermes profiles. Firecrawl search
returned 401 and scrape returned "unreachable" on all 4 initial calls. Pivoted to
`web_search` (4 queries, 40 results total) + `web_extract` (15 pages across 3 calls).
Completed all 6 research scope items with high confidence, 18 URLs sourced.

## Anti-Patterns

- Do NOT retry a failing Firecrawl tool more than 3 times in one turn — it triggers
  the "same_tool_failure_warning" loop limit and wastes time.
- Do NOT switch to text-only replies when tools fail — keep using other tools.
- Do NOT give up on research because one tool family is down. The built-in stack
  (`web_search` + `web_extract`) is robust and has no auth dependencies.
