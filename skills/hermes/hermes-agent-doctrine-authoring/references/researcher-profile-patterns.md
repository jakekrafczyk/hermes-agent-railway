# Researcher Profile — Domain-Specific Research Patterns

Pattern for a researcher profile that finds domain-specific context for other
profiles in a multi-profile agency deployment, rather than generic web scraping.

## Research-for-Quality Mission

The researcher's job is to find raw material that specialists need:
- **Code Architect** — documentation, implementation guides, GitHub repos,
  API references, changelogs, dependency upgrade notes
- **Design profile** — CRO blog posts (scan hundreds, synthesize relevance),
  industry-leading design examples, customer psychology trends, social listening data
- **Social Media profile** — platform analytics, competitor content, trending
  formats, engagement benchmarks, audience sentiment
- **Orchestrator** — competitive landscape, market research, industry trends

## Domain Research Modes (in AGENTS.md)

Each `assignee_domain` triggers a different research mode with specific:
- Search strategy (which sites/sources to prioritize)
- Freshness rules (cache vs live)
- Age cutoff rules

### Code/Architecture Mode
- `maxAge: 0` ALWAYS — live pages, no cache
- Discard tech docs/repos older than 6 months
- If the ONLY result is >6 months old: confirm with operator before using
- Prioritize: official docs, GitHub READMEs, npm/pip pages, Stack Overflow <1yr

### Design Mode
- Cached OK for examples/style inspiration
- `maxAge: 0` for psychology trends, social listening, competitive audits
- Sources: CRO/UX blogs, Dribbble/Behance, consumer psychology journals

### Social Media Mode
- `maxAge: 0` always — social data is time-sensitive
- Sources: platform-specific searches, competitor analysis, trend reports

## Context Freshness Table (in SOUL.md)

| Rule | When |
|---|---|
| `maxAge: 0` (no cache) | Code docs, implementation guides, technology research |
| Discard >6 months | Technology research — unless ONLY result |
| Cached OK | General market research, competitive analysis, design examples |
| As recent as possible | Social media data, news, prices |

## Firecrawl MCP Integration

Replace raw curl commands with `mcp_firecrawl_firecrawl_scrape` tool calls.
The tool handles auth, retries, and proxy rotation natively.

Cache control via the `maxAge` parameter:
```json
{ "maxAge": 0 }     // live — no cache
{ "maxAge": unset } // cached OK
```

Orchestrator can override via optional `freshness: live|cached` in task brief.

## Camofox Curl Retention (Hybrid Approach)

Keep raw curl commands for Camofox browser API (reliability over tool abstraction).
Browser tools route through Camofox automatically when `CAMOFOX_URL` is set,
but curl gives direct control for authenticated scraping, cookie injection, and
snapshot extraction.

## Anti-Ban Rules for Authenticated Platforms

When scraping OWN social media accounts:
- Always use Camofox (never Firecrawl) — browser traffic looks real
- Rate limit: max 1 request per 5 seconds
- Never rapid-scroll or rapid-click
- Cookie org: `/data/camofox/cookies/<platform>_<account>.json`
- Light scraping only — extract what's needed, don't crawl profiles
- If CAPTCHA/2FA: HALT immediately, write error_state to inbox

## Model: owl-alpha

`openrouter/owl-alpha` — 1M context window. Handles large scraped pages
and extended multi-source research without context eviction. Free tier,
no per-token cost, suitable for high-volume research.
