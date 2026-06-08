---
name: llm-model-comparison-research
description: Multi-source LLM model evaluation for domain-specific use cases — benchmark aggregation, pricing collection, and recommendation synthesis.
version: 1.0.0
---

# LLM Model Comparison Research

Systematic workflow for evaluating and comparing LLM models for a specific domain (social media, coding, analysis, writing, etc.) using live data from OpenRouter, benchmark leaderboards, and industry sources. Produces structured comparison tables, cost analysis, impact analysis, and a recommendation matrix.

## Triggers

Use this skill when asked to:
- Compare LLM models for a specific use case or domain
- Evaluate which model is "best" for a task (copywriting, coding, content, etc.)
- Research model pricing, benchmarks, or capabilities across providers
- Build a model recommendation matrix for a profile or workflow
- Any variation of "which LLM should I use for X"

## Workflow

### Phase 1: Gather Candidate Models

1. Identify the candidate model list (user-specified or discover through search).
2. Note each model's OpenRouter ID format (e.g., `deepseek/deepseek-v4-pro`, `anthropic/claude-sonnet-4`).

### Phase 2: Collect Pricing & Specs from OpenRouter

For EACH candidate model, scrape its OpenRouter model page:
- URL pattern: `https://openrouter.ai/{provider}/{model-id}`
- Extract: input/output pricing (per 1M tokens), context window, max output tokens, throughput, latency, structured output error rate, and provider-specific pricing tiers (cached vs uncached, ≤200K vs >200K tiers).
- Use `web_extract` for these pages — they are static enough and return good markdown.

**Pitfall:** Firecrawl MCP's `firecrawl_scrape` may fail with auth errors. `web_extract` is a reliable fallback for OpenRouter pages.

### Phase 3: Collect Benchmark Data

Scrape these benchmark leaderboards for creative/writing quality:

| Source | URL | What It Measures | Use For |
|--------|-----|-----------------|---------|
| **EQ-Bench Creative Writing v3** | `https://eqbench.com/creative_writing.html` | Elo scores + slop/repetition metrics for creative writing | Brand voice quality, copywriting, tonal control |
| **EVY Aggregated Benchmarks** | `https://evy.so/compare/best-llms-for-writing/` | Aggregated EQ Creative + Arena Text + EQ General + Speed + Pricing | Cross-reference, especially for models not yet on EQ-Bench |
| **LechMazur Creative Writing** | `https://github.com/lechmazur/writing` | Pairwise story comparison benchmark | Creative narrative quality |
| **Price Per Token IFEval** | `https://pricepertoken.com/leaderboards/writing` | IFEval (instruction-following) scores + community votes | Platform formatting compliance, instruction adherence |
| **EQ-Bench Longform** | `https://eqbench.com/creative_writing_longform.html` | Long-form creative writing quality | Long-form content (LinkedIn articles, reports) |

Key metrics to extract per model:
- **EQ-Bench Elo** — primary creative writing quality metric (range ~200–2,200, higher = better)
- **Slop score** — frequency of GPT-isms/clichés (lower = more original/human-like)
- **Repetition score** — word/phrase repetition (lower = more varied)
- **IFEval score** — instruction-following precision (higher = better at formatting constraints)
- **IFBench score** — alternative instruction-following benchmark (different methodology)

### Phase 4: Collect Industry Analysis

Search for and scrape articles on:
- "best LLM for [domain] 2026"
- "LLM model comparison [domain] benchmark"
- "AI [domain] tools agency model comparison"
- "prompt engineering vs model quality [domain]"

Key sources that consistently produce useful data:
- `marketingagent.blog` — detailed marketing use-case breakdowns with cost calculations
- `digitalapplied.com` — prompt engineering templates with quantitative impact data
- `pecollective.com` / `cloudzero.com` — comprehensive pricing comparison tables
- `medium.com` agency workflow articles
- Reddit threads in `r/ai_x_marketing`, `r/artificial`, `r/PromptEngineering`

### Phase 5: Synthesize

Produce these sections in order:

1. **Model Comparison Table** — all candidate models with columns: pricing (input/output), context window, max output, EQ-Bench Elo, IFEval/IFBench score, speed (tok/s), qualitative notes. Star-ratings for copywriting sub-dimensions (hooks, brand voice, short-form, long-form, platform formatting).

2. **Cost Analysis** — cost per typical workload unit (e.g., cost per 100 social posts, per LinkedIn article). Include prompt caching savings estimates and tiered routing strategies.

3. **Model Choice vs. Prompt Engineering Impact** — quantitative evidence on which matters more, with specific multiplier claims (e.g., "structured prompts = 3.2x conversion lift"). Include platform-specific model sweet spots.

4. **What Industry/Agencies Are Using** — market share data, real-world case studies with before/after cost metrics, dedicated tool landscape.

5. **Recommendation Matrix** — at minimum: Primary (quality/cost balance), Budget (cheapest viable), Premium (quality over cost), Multi-Client (brand voice isolation). Include a summary decision table mapping use cases to models with costs.

### Phase 6: Write Output File

Format per the task-format.md spec:
- YAML frontmatter with `output_type: research_findings`, `profile: researcher`, `status: complete`
- `sources` array listing all URLs consulted
- `confidence: high|medium|low`
- Free-form markdown body with all five synthesis sections

## Key Data Points to Always Include

- **Pricing caveat:** OpenRouter effective pricing varies by provider routing and cache hit rate. Report both list prices and weighted effective prices where available.
- **Benchmark caveat:** No benchmark directly measures social media post quality. EQ-Bench measures creative fiction, IFEval measures instruction following. Neither is a perfect proxy — state this limitation.
- **Context window:** Models with >200K context often have tiered pricing (higher cost for prompts exceeding 200K). Always note this.
- **Prompt caching:** Anthropic offers 90% discount on cached system prompts. OpenAI and Google also offer caching. Include potential savings when recommending models for repeated-use patterns.
- **Date sensitivity:** Model versions iterate monthly. Benchmark scores and pricing are snapshots. Include the date of data collection in the output.

## Common Pitfalls

- **Firecrawl MCP failure:** `firecrawl_scrape` on OpenRouter model pages frequently fails with auth errors. Use `web_extract` as primary tool for OpenRouter pages — it handles them reliably.
- **Reddit scraping failure:** `web_extract` on Reddit URLs often returns "Website Not Supported." Search for the thread content via `web_search` snippets instead, or find syndicated versions on other sites.
- **Benchmark staleness:** EQ-Bench updates weekly; models released after the last refresh won't appear. Check the benchmark page's "Updated" date and note gaps in the output.
- **Model version confusion:** OpenRouter sometimes lists older model versions alongside newer ones (e.g., `claude-opus-4` base vs `claude-opus-4-6`). Check release dates to ensure you're comparing apples to apples.

## References

- `references/benchmark-data-snapshot.md` — Concrete benchmark scores, pricing, and agency data from the June 2026 session. Use as a starting point for data that may still be current.
