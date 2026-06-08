# Hermes + Supermemory Documentation — Compact Index Pattern

## What

Both projects publish compact LLM-optimized doc indexes:
```
https://hermes-agent.nousresearch.com/docs/llms.txt          (~17KB, ~135 lines)
https://supermemory.ai/docs/llms.txt                          (~19KB, ~134 lines)
```

These are NOT full documentation dumps. They are structured indexes — each
line links to a specific docs page. You read the index to find the right
page URL, then `web_extract` or `firecrawl_scrape` that specific page.

## Why (vs the old 59k-line approach)

The old approach cached a 2.6MB / 59k-line full dump at
`/data/hermes-docs-llms-full.txt`. This cost:
- 2.6MB of disk
- ~2,200+ input tokens every session (the entry in Supermemory)
- `search_files` over 59k lines with broad patterns → hundreds of noise matches
- Stale content requiring manual refresh

The compact index approach:
- ~17–19KB each — negligible disk
- 135/134 lines — scan visually, no grep needed
- Always points to live docs (no staleness)
- Read entire index in one `read_file` call (~1k tokens)

## Location

```
/data/system/reference/hermes_llms.txt        # Hermes Agent docs index
/data/system/reference/supermemory_llms.txt   # Supermemory docs index
```

## Setup (one-time)

```bash
mkdir -p /data/system/reference/
curl -s https://hermes-agent.nousresearch.com/docs/llms.txt \
  > /data/system/reference/hermes_llms.txt
curl -s https://supermemory.ai/docs/llms.txt \
  > /data/system/reference/supermemory_llms.txt
```

## Usage

1. `read_file(path="/data/system/reference/hermes_llms.txt")` — scan the index
2. Find the doc page URL that matches your question
3. `web_extract(urls=["<that-url>"])` or `firecrawl_scrape` for structured data

For quick lookups where you know the topic, you can skip the index and go
directly to `web_extract` on the relevant docs page URL.

## Pitfalls

- These are **indexes, not the full docs**. Each entry is a one-line link +
  description. If you need detailed content, you MUST follow the link.
- The compact files at `/data/system/reference/` are NOT auto-updated. Docs
  evolve — if a link 404s or the content seems outdated, re-curl.