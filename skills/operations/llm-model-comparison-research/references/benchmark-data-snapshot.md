# EQ-Bench Creative Writing v3 Scores (May 2026 Snapshot)

Key models relevant to social media / copywriting evaluation. Full leaderboard: https://eqbench.com/creative_writing.html

| Model | Elo Score | Rubric Score | Slop ↓ | Repetition ↓ | Length (tokens) |
|-------|-----------|-------------|--------|-------------|-----------------|
| claude-opus-4-7 | 2206.1 | 82.85 | 1.5 | 4.0 | 5,692 |
| gpt-5.5 | 2034.9 | 85.05 | 1.8 | 2.5 | 12,945 |
| claude-opus-4-8 | 2031.4 | 83.30 | 1.8 | 3.7 | 5,842 |
| gpt-5.4 | 2002.7 | 84.45 | 1.7 | 2.7 | 10,488 |
| claude-sonnet-4-6 | 1967.9 | 82.50 | 1.4 | 4.1 | 5,876 |
| claude-opus-4-6 | 1932.8 | 82.65 | 1.7 | 4.0 | 6,055 |
| gpt-5.2 | 1782.8 | 83.30 | 2.3 | 3.0 | 12,536 |
| Kimi-K2.6 | 1781.6 | 83.35 | 1.8 | 3.8 | 8,333 |
| claude-sonnet-4.5 | 1766.7 | 80.70 | 2.2 | 3.6 | 5,784 |
| o3 | 1743.6 | 81.40 | 2.4 | 2.7 | 7,864 |
| DeepSeek-V4-Pro | 1569.9 | 82.25 | 2.7 | 3.2 | 7,444 |
| DeepSeek-R1 | 1500.0 | 78.40 | 4.3 | 4.6 | 5,352 |
| claude-3-5-sonnet | 1448.3 | 74.75 | 2.8 | 4.4 | 4,921 |
| GPT-4o (inferred) | ~1443 | N/A | N/A | N/A | N/A |
| gemini-2.5-pro-preview | 1417.3 | 80.80 | 4.0 | 4.9 | 6,974 |
| claude-3-7-sonnet | 1394.9 | 77.35 | 3.3 | 3.7 | 6,327 |

## EVY Aggregated Data (May 18, 2026)

From https://evy.so/compare/best-llms-for-writing/ — combines EQ-Bench Creative, Arena Text, EQ General, Speed, and Prices.

### Task-Specific Recommendations (from EVY)

| Task | Recommended Models | Rationale |
|------|-------------------|-----------|
| Narrative & long-form | Claude Opus 4.7, Claude Sonnet 4.6 | Highest EQ Creative; emotional depth, tonal consistency |
| Structured commercial copy | GPT-5.5, Claude Sonnet 4.6 | Clarity, persuasion structure, format adherence |
| High-volume / fast drafts | Gemini 3 Flash, Grok 4.1, Kimi K2 | Speed and low cost outweigh peak quality |
| Brand voice & consistency | Claude Sonnet 4.6, Gemini 3.1 Pro | Strong instruction-following, tonal control |

## LechMazur Creative Story-Writing Benchmark (May 2026)

From https://github.com/lechmazur/writing — pairwise story comparison, 31 models, ~26.1k judgments.

Top 10:
1. GPT-5.5 (xhigh) — Score 3.5, 92% win probability
2. gpt-5.4-xhigh — Score 3.4, 91%
3. gpt-5.4-medium — Score 3.3, 90%
4. Claude Opus 4.7 (high) — Score 3.0, 87%
5. Claude Sonnet 4.6 Thinking 16K — Score 2.8, 86%
6. claude-opus-4-6-16K — Score 2.2, 80%
7. Claude Opus 4.8 (xhigh) — Score 1.7, 75%
8. gpt-5.2-medium — Score 1.5, 72%
9. Kimi K2.6 — Score 1.2, 68%
10. Claude Opus 4.8 (high) — Score 1.1, 67%

## OpenRouter Pricing Snapshot (June 1, 2026)

All prices per 1M tokens. Standard pricing (may vary by provider on OpenRouter).

| Model | Input $ | Output $ | Context | Max Output |
|-------|---------|----------|---------|------------|
| deepseek/deepseek-v4-pro | 0.44 | 0.87 | 1M | 384K |
| anthropic/claude-sonnet-4 | 3.00 (≤200K) / 6.00 (>200K) | 15.00 (≤200K) / 22.50 (>200K) | 1M | 64K |
| anthropic/claude-opus-4 | 15.00 | 75.00 | 200K | 32K |
| openai/gpt-4.1 | 2.00 | 8.00 | 1M | 16.4K |
| openai/gpt-4o | 2.50 | 10.00 | 128K | 16.4K |
| google/gemini-2.5-pro | 1.25 (≤200K) / 2.50 (>200K) | 10.00 (≤200K) / 15.00 (>200K) | 1M | 65.5K |
| google/gemini-2.5-flash | 0.30 | 2.50 | 1M | 65.5K |
| meta-llama/llama-4-maverick | 0.15 | 0.60 | 1M | 16.4K |
| openrouter/owl-alpha | FREE (currently) | FREE | 1M | 262K |

## Prompt Engineering Impact Data

From https://www.digitalapplied.com/blog/prompt-engineering-marketing-copy-templates:

| Factor | Impact |
|--------|--------|
| Structured prompts vs. ad-hoc | 3.2x conversion lift |
| Chain-of-thought prompting | +28% CTR on ad headlines |
| Brand voice calibration (5 examples) | 90%+ voice accuracy |
| <3 brand examples | Inconsistent tone |
| >7 brand examples | Diminishing returns, wasted context |

Core finding: "A well-structured prompt on Claude Sonnet consistently outperforms a generic prompt on Claude Opus."

## Agency Market Share (Late 2025)

From Vincenthaywood Medium article:

| Tool | Market Share |
|------|-------------|
| ChatGPT (OpenAI) | 67-68% |
| Google Gemini | ~18% |
| Microsoft Copilot | ~14% |
| Perplexity | ~6% |
| Claude (Anthropic) | 3-4% |

## Useful Search Queries for Future Sessions

- `"best LLM for copywriting social media" 2026 comparison benchmark`
- `OpenRouter model pricing comparison per million tokens 2026`
- `AI copywriting tools agencies using model comparison social media`
- `prompt engineering vs model quality social media copywriting`
- `EQ-Bench creative writing leaderboard`
- `LLM creative writing benchmark 2026 scores comparison`