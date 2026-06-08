# Partner Deployment Checklist

What a business partner needs when deploying their own Hermes instance from this
agency's GitHub fork (or their fork of it).

## Deployment Flow

1. Partner forks your populated repo (or you give them direct deploy access to yours)
2. Railway → New Service → **Deploy from GitHub Repo** → paste fork URL
3. Set env vars in Railway Variables tab (below)
4. Deploy — Railway reads `railway.json`, builds from `Dockerfile`
5. On first boot, `entrypoint.sh` syncs `profiles/` into `/data/profiles/`

No "deploy from template first, then switch source" dance needed.

## Required API Keys (3 core)

| Service | Railway Env Var | How to get |
|---------|-----------------|-------------|
| **OpenRouter** | `OPENROUTER_API_KEY` | [openrouter.ai/keys](https://openrouter.ai/keys) |
| **Firecrawl** | `FIRECRAWL_API_KEY` | [firecrawl.dev](https://firecrawl.dev) → API Keys |
| **Supermemory** | `SUPERMEMORY_API_KEY` | [supermemory.ai](https://supermemory.ai) → Dashboard → API Keys |

Set in Railway → service → Variables tab as raw env vars:

```
OPENROUTER_API_KEY=sk-or-v1-...
FIRECRAWL_API_KEY=fc-...
SUPERMEMORY_API_KEY=sm_...
```

The config profiles reference these by name (`api_key_env: FIRECRAWL_API_KEY`,
`supermemory.api_base: https://api.supermemory.ai/v3`), so Hermes auto-wires
them on startup — no dashboard clicking required beyond the first-run provider
wizard (OpenRouter key triggers auto-detection).

**Supermemory trap:** partner must create a free account at supermemory.ai
first, then hit their API dashboard to generate the key. No in-app signup.

## Optional (messaging + browser)

| Service | Env Vars | When needed |
|---------|----------|-------------|
| **Telegram** | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS` | Chat via Telegram |
| **Discord** | `DISCORD_BOT_TOKEN`, `DISCORD_ALLOWED_USERS` | Chat via Discord |
| **Slack** | `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` | Chat via Slack |
| **Camofox** | `CAMOFOX_URL`, `CAMOFOX_API_KEY` | Only if they deploy a separate Camofox browser for authenticated scraping. Without it, Camofox tabs fail gracefully. |

## Prerequisites: Your Fork Must Have

Before a partner can deploy, verify your fork on GitHub has ALL of:

- `Dockerfile` (with `COPY profiles ./profiles`)
- `railway.json`
- `.env.example`
- `.gitignore`
- `.dockerignore`
- `entrypoint.sh` (with profile sync block)
- `admin/`
- `skills/`
- `profiles/` (with `default/config.yaml`, `researcher/config.yaml`, `.gitignore`)

Missing any of these → partner's deploy fails at build time.

## Model: deepseek/deepseek-v4-pro

The default profile uses `deepseek/deepseek-v4-pro` via OpenRouter for both
main model AND delegation. Do NOT switch delegation to anthropic — the prompt
file in the repo may be stale on this point. The live `profiles/default/config.yaml`
in the fork is authoritative.

## Config Version Compatibility

- Default profile config is written in the modern v23+ structure (no `_config_version`
  key — Hermes upgrades it on first run)
- Researcher profile config carries `_config_version: 23` as written
- Both profiles use `__FIRECRAWL_API_KEY__` as placeholder — real key comes from
  Railway env var `FIRECRAWL_API_KEY`
- Partner never commits real API keys to the repo
