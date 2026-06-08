# Reference: Educational Post Discovery — Voltaic Marketing Test Run (2026-06-04)

This is the raw research output from a live Phase 1 test of the `educational-post-idea-discovery` skill.
Shows the expected shape, depth, and structure of researcher findings. Use as a quality benchmark.

## What Worked

- **30+ web_search calls** across 5 subreddits + local SEO + Cleveland business publications
- **Reddit blocked direct extraction** on all methods (Firecrawl, web_extract, old.reddit.com) — but search snippets provided sufficient signal
- **Cleveland-specific data** was rich: county business survey (614 businesses), local marketing blogs, JPMorgan 2026 Ohio optimism survey
- **10+ long-form sources extracted** — local marketing guides, survey data, industry reports

## Data Points That Drove the Best Ideas

| Signal | Source | Strength |
|--------|--------|----------|
| "Ripped Off by Marketing Agencies" thread | r/smallbusiness | Massive trust deficit — multiple threads, high upvotes |
| "Has AI Actually Made You More Money?" | r/smallbusiness | #1 AI question, deep skepticism |
| "Traffic vs. Conversion vs. Follow-up" poll | r/smallbusiness | Conversion blindness — owners can't self-diagnose |
| 62% more likely to purchase from local-knowledge businesses | MyShyft Cleveland | Hyper-local authenticity = measurable advantage |
| Marketing/social media = #1 short-term need | Cuyahoga County survey | Direct demand signal |
| 70%+ say cost prevents tech expansion | Cuyahoga County survey | Budget anxiety is structural, not just perception |
| Cleveland = 19th largest media market | Hello Mammoth | Traditional ads expensive, reach fragmented |
| 74% of Ohio SMBs optimistic for 2026 | JPMorgan / Signal Cleveland | Growth mindset — they want to invest, need guidance |
| Only 4% of brands have full data integration | Guac Digital | "The 96% Problem" — most are flying blind |

## What Didn't Work

- Reddit full-thread extraction (blocked on all methods)
- Firecrawl MCP tools (invalid authentication token)
- City-data.com forums (no recent Cleveland business discussions)
- LinkedIn public post scraping (login walls)
- Nextdoor (regional account authentication required)

## Successful Fallback Pattern

When Reddit blocks extraction:
1. `web_search` with `site:reddit.com/r/smallbusiness` + keyword filters
2. Analyze search result titles and descriptions for sentiment, pain points, engagement
3. Note thread URLs for manual verification of high-signal threads
4. Supplement with extracted local blogs, surveys, SEO data
5. This is sufficient for idea generation — the pipeline should not stall on extraction failures

## Output Structure

The raw research file (`task_voltaic_idea_research.md`) used these sections:
1. Reddit Findings (per subreddit — r/smallbusiness, r/marketing, r/Entrepreneur, r/Cleveland, r/Ohio)
2. Local Forum Findings (Cleveland marketing blogs, county surveys, FB groups)
3. Local SEO & Search Intent (competitor landscape, PAA questions, market stats)
4. Pain Points & FAQ Themes (top questions, core pain points, misconceptions, what businesses struggle with now)
5. Key Content Angles (raw thematic opportunity areas — NOT post ideas)
6. Research Limitations (transparency about gaps)