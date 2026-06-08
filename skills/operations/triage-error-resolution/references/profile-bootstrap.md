# Profile Bootstrap Checklist

Every new Hermes worker profile must pass this checklist before it can operate. Profiles are isolated — their `config.yaml` and `.env` do **not** inherit from `/data/config.yaml` and `/data/.env`.

## 1. Environment file

Create `<profile>/.env` with:

```bash
CAMOFOX_URL=http://camofox-browser.railway.internal:9377
CAMOFOX_API_KEY=<key>
```

## 2. Camofox config

In `<profile>/config.yaml`, the `browser.camofox` block must include:

```yaml
browser:
  camofox:
    managed_persistence: true
    user_id: <profile_name>
    session_key: <profile_name>-session
    port: 9377
    cookies_path: /data/camofox/cookies
```

The `user_id` and `session_key` are required by the Camofox API on every tab creation and snapshot call.

## 3. Integration wiring

Copy these blocks from `/data/config.yaml` into the profile's `config.yaml`:

```yaml
memory:
  provider: supermemory

searxng:
  url: http://localhost:8888

supermemory:
  api_base: https://api.supermemory.ai/v3
  container_tag: voltaic

firecrawl:
  api_base: https://api.firecrawl.dev/v2
  api_key_env: FIRECRAWL_API_KEY

tools:
  defer_loading: true
  pre_selection: true

mcp_servers:
  firecrawl:
    command: npx
    args:
    - -y
    - firecrawl-mcp
    env:
      FIRECRAWL_API_KEY: <redacted>

auxiliary:
  vision:
    provider: openrouter
    model: openrouter/auto
  web_extract:
    provider: openrouter
    model: openrouter/auto
  compression:
    provider: openrouter
    model: deepseek/deepseek-v4-pro

compression:
  enabled: true
  threshold: 0.4
  target_ratio: 0.15
  protect_last_n: 15

terminal:
  cwd: /data/workspace

delegation:
  provider: openrouter
  model: deepseek/deepseek-v4-pro
```

## 4. AGENTS.md + SOUL.md

- Copy or customize `AGENTS.md` from `/data/profiles/researcher/AGENTS.md` as a starting template.
- `SOUL.md` is the behavioral layer (tone, rules). Researcher uses a generic one; the orchestrator profile injects its own via system prompt.

## 5. Shared directories

Ensure the profile can reach:

- `/data/camofox/cookies/` — must exist (created by main profile setup)
- `/data/workspace/triage/` — error state drop target
- `/data/workspace/tasks/` — task coordination folder (future)

## 6. Config version

Profiles use `_config_version: 23` (auto-expanded with all defaults). The main profile uses `_config_version: 5` (compact, hand-crafted). When syncing, do NOT copy v23 noise into the main config or vice versa — do targeted delta sync of operational settings only.

## 7. Verification

After bootstrap, run:

```bash
# Check Camofox health from the profile's perspective
curl -s --max-time 5 $CAMOFOX_URL/health | python3 -c "import sys,json; d=json.load(sys.stdin); assert d['ok']==True; print('Camofox OK')"

# Check SearXNG
curl -s --max-time 5 http://localhost:8888 | head -c 100

# Verify config parses
python3 -c "import yaml; yaml.safe_load(open('$HERMES_HOME/config.yaml')); print('Config OK')"
```

## Real-world failure case

**2026-05-22 — Researcher profile Camofox unreachable**

- **Symptom:** `tool_unavailable`, Camofox "connection refused" from researcher profile
- **Root cause:** Researcher had no `.env` file, `camofox.managed_persistence: false`, empty `user_id`/`session_key`. The Camofox service was running fine on the host — the profile just couldn't see it.
- **Fix:** Created `.env` with `CAMOFOX_URL`, set `managed_persistence: true`, added `user_id`/`session_key`, created `/data/camofox/cookies/`, synced missing integration blocks.
- **Lesson:** Always check profile-level config before assuming a service is down.
