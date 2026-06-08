# Firecrawl Python SDK v4.x Usage Notes

The Firecrawl Python SDK v4.x (tested with v4.27.1) returns **Pydantic model
objects**, not plain dicts. This is an easy trap for anyone coming from v1.x
`scrape_url()` → dict patterns.

## Key API Methods

| Method | Returns | Key Fields |
|---|---|---|
| `scrape(url, formats=["markdown"])` | `Document` | `.markdown`, `.metadata`, `.html`, `.links`, `.json` |
| `crawl(url, limit=N, scrape_options=..., timeout=T)` | `CrawlJob` | `.status`, `.data` (list of `Document`), `.total` |
| `start_crawl(url, limit=N, ...)` | `CrawlResponse` | `.id` (job ID for `get_crawl_status`) |
| `get_crawl_status(job_id)` | `CrawlJob` | same as crawl() |
| `map(url, limit=N)` | `MapData` | `.links` (list of `MapLink` objects with `.url`, `.title`, `.description`) |
| `search(query, limit=N)` | `SearchData` | `.data` (list of search result objects) |
| `extract(urls, prompt=..., schema=...)` | async | returns extract result objects |
| `agent(prompt=..., urls=...)` | async | autonomous research agent |
| `get_credit_usage()` | `CreditUsage` | `.remaining_credits`, `.plan_credits`, `.billing_period_start`, `.billing_period_end` |

## The Dict Trap (Pydantic Models)

**Wrong (v1.x style):**
```python
result = app.scrape("https://example.com", formats=["markdown"])
md = result["markdown"]           # ❌ AttributeError: 'Document' object has no attribute '__getitem__'
meta = result.get("metadata")     # ❌ same
```

**Right (v4.x style):**
```python
doc = app.scrape("https://example.com", formats=["markdown"])
md = doc.markdown                 # ✅ attribute access
title = doc.metadata.title        # ✅ nested attribute access
url = doc.metadata.source_url     # ✅
```

**Safe fallback (works with both):**
```python
md = getattr(doc, 'markdown', None)
meta = getattr(doc, 'metadata', None)
if meta:
    title = getattr(meta, 'title', 'N/A')
    url = getattr(meta, 'source_url', None)
```

## CrawlJob Fields

```python
job = app.crawl("https://example.com", limit=3, scrape_options={"formats": ["markdown"]})
job.status          # "completed" | "failed" | etc.
job.data            # list of Document objects
job.total           # total pages discovered
job.credits_used    # credits consumed
job.completed       # timestamp
job.expires_at      # when results expire from cache
```

## Document Fields (most useful)

| Field | Type | Notes |
|---|---|---|
| `.markdown` | `str` | Clean markdown content |
| `.html` | `str` | Raw HTML |
| `.raw_html` | `str` | Unprocessed HTML |
| `.metadata` | `DocumentMetadata` | `.title`, `.source_url`, `.description`, `.language`, `.status_code`, `.scrape_id` |
| `.links` | `list` | Extracted links |
| `.summary` | `str` | Auto-generated summary (if requested) |
| `.json` | `dict` | Structured extraction (if JSON format requested) |
| `.screenshot` | `str` | Screenshot URL (if requested) |
| `.actions` | `list` | Browser actions for `.scrape_execute()` / interact |

## When to Use Python SDK vs MCP Tools

- **MCP tools** (`mcp_firecrawl_firecrawl_scrape`, etc.): Normal agent operation.
  These are the go-to tools for scraping from within a conversation.
- **Python SDK in `execute_code`**: When you need programmatic logic across
  multiple pages, loops, conditional scraping, or bulk operations.