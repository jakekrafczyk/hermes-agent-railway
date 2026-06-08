# Nous Portal Model Catalog

**Source:** `hermes model` interactive picker → Nous Portal provider (verified 2026-06-05)
**Inference API:** `https://inference-api.nousresearch.com/v1`
**Subscription management:** https://portal.nousresearch.com/manage-subscription

## Free Tier Models

Available on any Nous Portal account (no paid subscription required):

| Model | In $/Mtok | Out $/Mtok | Cache $/Mtok | Notes |
|---|---|---|---|---|
| `stepfun/step-3.7-flash:free` | free | free | free | StepFun's flash model |
| `nvidia/nemotron-3-ultra:free` | free | — | — | NVIDIA's open model |

The `:free` suffix is part of the model identifier — omitting it routes to the
paid version (which requires a subscription).

## Paid Tier Models

Requires subscription upgrade at https://portal.nousresearch.com. Listed in
order as shown by `hermes model`:

### Premium (Frontier)

| Model | In $/Mtok | Out $/Mtok | Cache $/Mtok |
|---|---|---|---|
| `anthropic/claude-opus-4.8` | 5.00 | 25.00 | 0.50 |
| `openai/gpt-5.5-pro` | 30.00 | 180.00 | — |

### High-End

| Model | In $/Mtok | Out $/Mtok | Cache $/Mtok |
|---|---|---|---|
| `anthropic/claude-sonnet-4.6` | 3.00 | 15.00 | 0.30 |
| `openai/gpt-5.5` | 5.00 | 30.00 | 0.50 |
| `google/gemini-3.1-pro-preview` | 2.00 | 12.00 | 0.20 |
| `x-ai/grok-4.3` | 1.25 | 2.50 | 0.20 |
| `deepseek/deepseek-v4-pro` | 1.60 | 3.20 | 0.14 |
| `qwen/qwen3.7-max` | 1.25 | 3.75 | 0.25 |
| `z-ai/glm-5.1` | 1.26 | 3.96 | 0.23 |

### Mid-Range

| Model | In $/Mtok | Out $/Mtok | Cache $/Mtok |
|---|---|---|---|
| `anthropic/claude-haiku-4.5` | 1.00 | 5.00 | 0.10 |
| `openai/gpt-5.4-mini` | 0.75 | 4.50 | 0.07 |
| `google/gemini-3.5-flash` | 1.50 | 9.00 | 0.15 |
| `qwen/qwen3.7-plus` | 0.40 | 1.60 | 0.08 |
| `moonshotai/kimi-k2.6` | 0.68 | 3.42 | 0.14 |
| `xiaomi/mimo-v2.5-pro` | 0.43 | 0.87 | 0.00 |

### Budget

| Model | In $/Mtok | Out $/Mtok | Cache $/Mtok |
|---|---|---|---|
| `minimax/minimax-m3` | 0.30 | 1.20 | 0.06 |
| `stepfun/step-3.7-flash` | 0.20 | 1.15 | 0.04 |
| `qwen/qwen3.6-35b-a3b` | 0.14 | 1.00 | — |
| `deepseek/deepseek-v4-flash` | 0.10 | 0.20 | 0.02 |
| `nvidia/nemotron-3-super-120b-a12b` | 0.09 | 0.45 | — |
| `tencent/hy3-preview` | 0.06 | 0.21 | 0.02 |

### Also Listed (no pricing shown)

| Model | Notes |
|---|---|
| `google/gemini-3-pro-preview` | Likely free preview (pricing blank) |

## Model Picker Navigation

`hermes model` is interactive (requires PTY). Two screens:

1. **Provider selection** — numbered list, Enter to confirm
2. **Model selection** — shows models with pricing, options:
   - Numbered models (1-2 for free, full list for paid)
   - `Enter custom model name` (for models not in the curated list)
   - `Skip (keep current)` (exit without changes)

**To inspect without changing:** pick any provider, then pick "Skip" on the model
screen. Or kill the process — but "Skip" is cleaner.

## Tool Gateway

Inspect with `hermes portal tools`. Partners:

| Tool | Partner | Status |
|---|---|---|
| Web search & extract | Firecrawl | not configured (unless API key set) |
| Image generation | FAL | FAL (default) |
| Text-to-speech | OpenAI TTS | Edge TTS (free default) |
| Browser automation | Browser Use | Camofox (if deployed) |
| Cloud terminal | Modal | local (default) |

Tool Gateway availability depends on subscription tier.
