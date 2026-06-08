# Case: Owl Alpha → Stealth Provider 400 Error

**Date:** June 5, 2026
**Model:** `openrouter/owl-alpha`
**Provider:** Stealth (sole provider for this model)
**Error:** HTTP 400 — `Provider returned error`

## The Error

```json
{
  "error": {
    "message": "Provider returned error",
    "code": 400,
    "metadata": {
      "raw": "ERROR",
      "provider_name": "Stealth",
      "is_byok": false
    }
  },
  "user_id": "org_3DmGJsLt1HHRqYzYsdhcCjHp2bg"
}
```

## The Confusion

The user was running `deepseek/deepseek-v4-pro` on OpenRouter successfully.
Their API key was valid. `owl-alpha` showed as eligible in the OpenRouter
dashboard. The error message said "Verify your API key is valid" — making
it look like an auth problem.

**It was not.**

## Isolation Protocol Applied

### Step 1 — Metadata Analysis
- `provider_name: "Stealth"` → upstream provider failure, not auth
- `is_byok: false` → not a bring-your-own-key issue
- `raw: "ERROR"` (no details) → generic provider failure, likely capacity
- HTTP 400 (not 401/402/403) → not credentials, credits, or permissions

**Conclusion at this layer:** Upstream provider failure. Don't touch API keys.

### Step 2 — Direct curl Test

```bash
curl -s --max-time 15 https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openrouter/owl-alpha","messages":[{"role":"user","content":"Hi"}]}'
```

**Result:** Identical error. Rules out Hermes entirely.

### Step 3 — Parameter Variations

Tested each variation — all failed identically:
- No parameters at all → same error
- `stream: false` explicit → same error
- `provider: {require_parameters: false}` → same error
- `max_tokens: 10` → same error

**Conclusion:** Not a parameter issue. Stealth is simply not serving the model.

### Step 4 — Community Check

Found multiple Reddit threads (r/hermesagent, r/openrouter) and GitHub issues
(OpenClaw) reporting the exact same error with owl-alpha over the preceding
weeks. This is a known intermittent issue with the Stealth provider.

**Conclusion:** Known upstream issue. No config change will fix it.

## Resolution

Recommended fallback models in config.yaml so Hermes auto-switches when
Stealth is down:

```yaml
fallback_providers:
  - model: openrouter/quasar-alpha
    provider: openrouter
  - model: google/gemini-2.5-flash
    provider: openrouter
```

## Key Takeaways

1. **"Provider returned error" with `provider_name` in metadata is NEVER auth.**
   The error message's "Verify your API key" is a generic catch-all — ignore it.
2. **The curl test takes 10 seconds** and rules out Hermes config entirely.
   Always do it before touching config.yaml.
3. **Single-provider models have no fallback within the model.** Owl Alpha only
   has Stealth. When Stealth is down, the only fix is switching models.
4. **Free models have fewer providers and more capacity issues.** DeepSeek v4
   Pro works because it has multiple providers with paid capacity.
