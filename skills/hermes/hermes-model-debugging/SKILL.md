---
name: hermes-model-debugging
description: "Diagnose and resolve model/provider errors in Hermes — 400 upstream failures, 429 rate limits, 502/503 downtime, streaming failures, and working model suddenly broken. Isolation protocol for determining whether the failure layer is Hermes config, OpenRouter routing, or the upstream provider."
triggers:
  - model error
  - model not working
  - provider error
  - provider returned error
  - HTTP 400 from model
  - HTTP 429 rate limit
  - HTTP 502 bad gateway
  - HTTP 503 no provider
  - model stopped working
  - can't connect to model
  - openrouter error
  - stealth error
  - upstream provider failure
  - working model broke
  - model returns nothing
  - streaming failed
---

# Hermes Model Debugging

When a model that should work returns errors — or a previously-working model
suddenly breaks — the error usually originates from one of three layers:

1. **Hermes config** — wrong model ID, incompatible parameters, streaming mismatch
2. **OpenRouter routing** — provider filtering, parameter requirements blocking all providers
3. **Upstream provider** — cold starts, capacity limits, intermittent downtime

This skill covers the full isolation protocol. For 401/403 auth errors
specifically, also consult `hermes-profile-auth` (key length comparison,
.env stubs, missing env vars).

## The Isolation Protocol

Work top-down from the raw error. Do NOT skip to fallback models before
identifying the failure layer — you'll miss config issues that would also
break the fallback.

### Step 1: Read the Error Metadata

The error shape tells you which layer failed:

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
  }
}
```

**Decode the metadata:**

| Field | What it tells you |
|---|---|
| `provider_name` present | Upstream provider failure — not auth, not Hermes |
| `is_byok: true` | "Bring your own key" provider — your key may be invalid/expired |
| `is_byok: false` | OpenRouter-managed provider — key issue is on their side |
| `raw: "ERROR"` (no details) | Provider gave a generic failure — likely capacity/cold-start |
| `raw` contains specific message | Read the message — may indicate parameter incompatibility |
| No `metadata` at all | Likely Hermes-level issue (bad model ID, request shape, or gateway timeout) |

**Quick lookup by HTTP code:**

| Code | Likely Layer | Common Cause |
|---|---|---|
| 400 | Upstream provider | Cold start, capacity, parameter incompatibility |
| 401 | Hermes auth | Bad/missing API key — see `hermes-profile-auth` |
| 402 | OpenRouter account | Out of credits — add funds |
| 403 | OpenRouter/moderation | Guardrail block, content filter, or permission issue |
| 429 | Upstream or OpenRouter | Rate limiting — check `Retry-After` header |
| 502 | OpenRouter routing | Selected model/provider down |
| 503 | OpenRouter routing | No available provider meeting routing requirements |

### Step 2: Isolate with Direct API Call

The single most valuable diagnostic: test the model directly against
OpenRouter's API with `curl`. This rules out Hermes entirely.

```bash
API_KEY=$(grep OPENROUTER_API_KEY /data/.env | cut -d= -f2)

# Minimal request — no streaming, no extra params
curl -s --max-time 15 https://openrouter.ai/api/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "openrouter/owl-alpha",
    "messages": [{"role": "user", "content": "Hi"}]
  }'
```

**Interpret results:**

- **Same error as Hermes** → problem is between OpenRouter and the upstream
  provider. Hermes config is fine. Proceed to Step 3.
- **Works via curl but not Hermes** → Hermes config issue. Check model ID
  format, streaming settings, provider routing config. Proceed to Step 4.
- **Different error via curl** → may indicate Hermes is adding incompatible
  parameters. Compare the full request body Hermes sends vs your curl call.

### Step 3: Check Community Reports

When the error is from the upstream provider (same via curl), check whether
this is a known intermittent issue:

1. **Reddit** — search `r/hermesagent`, `r/openrouter`, `r/LocalLLaMA` for
   the model name + error message
2. **GitHub** — search issues on `NousResearch/hermes-agent` and the model's
   client apps (OpenClaw, etc.) for the provider name
3. **OpenRouter announcements** — https://openrouter.ai/announcements/all
   for provider incidents or model status changes

If multiple users are reporting the same error with the same provider, it's
a known upstream issue — retry later. No config change will fix it.

### Step 4: Test Parameter Variations

If the error might be parameter-related (400 with specific raw message, or
curl works but Hermes doesn't), test progressively:

```bash
# Variation 1: No parameters at all (baseline)
curl -s --max-time 15 https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openrouter/<model>","messages":[{"role":"user","content":"Hi"}]}'

# Variation 2: With streaming disabled explicitly
curl -s --max-time 15 https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openrouter/<model>","messages":[{"role":"user","content":"Hi"}],"stream":false}'

# Variation 3: With provider routing relaxed
curl -s --max-time 15 https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openrouter/<model>","messages":[{"role":"user","content":"Hi"}],"provider":{"require_parameters":false}}'
```

If #1 fails but #3 works, the issue is `require_parameters` filtering out
the only available provider. Set `provider_routing.require_parameters: false`
in config.yaml.

### Step 5: Deploy Workarounds

When the upstream provider is the problem and retrying doesn't help:

**A. Wait and retry** — free/stealth models on OpenRouter sometimes need
cold-start warmup (seconds to minutes). Retry 2-3 times with 30s gaps.

**B. Fallback models** — add to config.yaml so Hermes auto-switches on failure:

```yaml
fallback_providers:
  - model: openrouter/quasar-alpha
    provider: openrouter
  - model: google/gemini-2.5-flash
    provider: openrouter
```

Hermes will silently try each model in order when the primary fails.

**C. Provider routing tweaks** — if the model has multiple providers:

```yaml
provider_routing:
  sort: "throughput"      # prefer warm instances
  require_parameters: false
```

**D. Switch to a different free model** — OpenRouter offers several free models
with different providers (and thus different reliability profiles):

| Model | Provider | Notes |
|---|---|---|
| `openrouter/owl-alpha` | Stealth | 1M ctx, agentic, intermittent |
| `openrouter/quasar-alpha` | Stealth | 1M ctx, coding-focused |
| `google/gemini-2.5-flash` | Google | Free tier, rate-limited but reliable |
| `meta-llama/llama-4-maverick` | Various | Free, multiple providers = better uptime |

## Streaming Failures

If the model works non-streaming but fails with streaming:

1. Check `display.streaming` in config.yaml — try setting to `false`
2. Some providers (especially Stealth) have intermittent streaming issues
3. Streaming failures mid-response show as SSE error events with HTTP 200

## Pitfalls

- **Don't assume auth.** A 400 with `provider_name` in metadata is NOT an
  API key issue — it's the upstream provider. Don't rotate keys or check .env.
- **Don't skip the curl test.** Config changes based on incorrect assumptions
  create new problems. Always isolate the failure layer first.
- **"Provider returned error" with `raw: "ERROR"`** is almost always upstream
  capacity/cold-start. No config change will fix it. Retry or wait.
- **Free models have fewer providers.** Owl Alpha has only Stealth. If Stealth
  is down, there's no fallback within that model — you must switch models.
- **Streaming works differently per provider.** If a model works in the
  OpenRouter playground but not in Hermes, check `display.streaming`.

## Auth Errors (401/403)

When the error is a 401 or 403, the root cause is almost always a **truncated, placeholder, or missing API key** in the profile's `.env` file. This is especially common when profiles are created from templates and the `.env` was seeded with a stub.

### Diagnostic Procedure

**Symptom:** `Provider mismatch: Error code: 401 - {'error': {'message': 'Missing Authentication header', 'code': 401}}`

**Step 1 — Verify config:** `HERMES_HOME=/data/profiles/<name> /opt/hermes/.venv/bin/hermes profile` — should show correct model + provider.

**Step 2 — Compare env vars between broken and working profiles:**
```bash
grep -oP '^[A-Z_]+(?==)' /data/profiles/<name>/.env   # broken
grep -oP '^[A-Z_]+(?==)' /data/.env                    # working
```

**Step 3 — Check key lengths.** A real OpenRouter API key is ~70+ chars (starts with `sk-or-v1-`). A stub is <20 chars.

**Step 4 — Fix truncated keys.** Do NOT use `patch` (redacts secrets). Use Python:
```bash
python3 -c "
with open('/data/.env') as f:
    for line in f:
        if line.startswith('OPENROUTER_API_KEY='):
            real_key = line.strip().split('=',1)[1]
            break
with open('/data/profiles/<name>/.env') as f:
    content = f.read()
for line in content.split('\n'):
    if line.startswith('OPENROUTER_API_KEY='):
        old_key = line.strip().split('=',1)[1]
        break
new_content = content.replace(f'OPENROUTER_API_KEY={old_key}', f'OPENROUTER_API_KEY={real_key}')
with open('/data/profiles/<name>/.env', 'w') as f:
    f.write(new_content)
"
```

**Step 5 — Verify:**
```bash
HERMES_HOME=/data/profiles/<name> /opt/hermes/.venv/bin/hermes -z 'Say hello — just confirm you can respond.'
```

### Common Auth Root Causes

| Cause | Symptom | Fix |
|-------|---------|-----|
| `.env` key is a stub | `OPENROUTER_API_KEY` < 20 chars | Copy real key from `/data/.env` |
| Missing env var | `grep` returns 0 matches for expected key | Add key to profile's `.env` |
| Wrong provider in config | `hermes profile` shows unexpected provider | Edit config.yaml model.provider |
| Missing plugins symlink | `memory status` shows NOT installed | `ln -s /data/plugins /data/profiles/<name>/plugins` |

### Plugin Auth Issues

Profiles look for plugins at `$HERMES_HOME/plugins/` — they do NOT inherit from the default profile. A missing plugins directory causes `hermes memory status` to show "NOT installed."

```bash
ls /data/profiles/<name>/plugins/ 2>/dev/null || echo "Missing"
ln -s /data/plugins /data/profiles/<name>/plugins
```

## Reference Cases

- `references/owl-alpha-stealth-400.md` — full diagnosis of "Provider returned error" 400 from the Stealth provider on OpenRouter
- `references/verified-auth-cases.md` — real-world auth diagnoses and fixes (archived from `hermes-profile-auth`)
