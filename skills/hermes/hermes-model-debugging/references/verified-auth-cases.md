# Verified Cases: Profile Auth Failures

## Case 1: social_media profile — 401 Missing Authentication header

**Date:** 2026-06-01
**Profile:** `/data/profiles/social_media/`
**Error:** `Provider mismatch: Error code: 401 - {'error': {'message': 'Missing Authentication header', 'code': 401}}`

### Diagnosis

1. `config.yaml` was correct: `model.default: deepseek/deepseek-v4-pro`, `provider: openrouter`
2. `.env` comparison:
   - Default: 7 env keys, `OPENROUTER_API_KEY` = 73 chars
   - social_media: 3 env keys, `OPENROUTER_API_KEY` = 13 chars (stub `sk-or-...7b1e`)
3. Also missing: `FIRECRAWL_API_KEY`, `SEARXNG_URL`, `CAMOFOX_URL`, `CAMOFOX_API_KEY`, `XAI_API_KEY`
4. Missing `plugins/` directory — `supermemory_governed` not discoverable

### Fix Applied

1. Copied real `OPENROUTER_API_KEY` (73 chars) from `/data/.env` to `/data/profiles/social_media/.env` via Python in-memory replace
2. Symlinked plugins: `ln -s /data/plugins /data/profiles/social_media/plugins`
3. Verified: `hermes profile` showed correct model, `hermes -z "say hello"` succeeded

### Lessons

- **When creating a new profile, never seed `.env` with placeholder keys** — the 13-char stub looked plausible (started with `sk-or-`) but was too short to be real
- **Key length comparison is the fastest diagnostic** for 401 errors — a real OpenRouter key is 70+ chars
- **Always symlink plugins when adding a new profile** — profiles don't inherit from default