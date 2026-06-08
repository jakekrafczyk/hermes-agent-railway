# Supermemory Setup on Hermes Railway

## Source
Docs: https://supermemory.ai/docs/integrations/hermes
Plugin README: /opt/hermes/plugins/memory/supermemory/README.md

## Setup Steps (verified May 2026)

```bash
# 1. Install the supermemory Python SDK
pip install supermemory
# → installs to ~/.local/lib/python3.13/site-packages/

# 2. Copy into PYTHONPATH-accessible location (venv is read-only)
cp -r ~/.local/lib/python3.13/site-packages/supermemory /opt/hermes-railway/
cp -r ~/.local/lib/python3.13/site-packages/supermemory-*.dist-info /opt/hermes-railway/

# 3. Verify importable
/opt/hermes/.venv/bin/python -c "import supermemory; print('ok')"

# 4. Set the provider
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes config set memory.provider supermemory
# → ✓ Set memory.provider = supermemory in /data/config.yaml

# 5. Add API key
echo 'SUPERMEMORY_API_KEY=<your_key>' >> /data/.env

# 6. Verify
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes memory status
```

## SDK Dependencies Already in Hermes Venv
These are bundled and don't need copying: `httpx`, `pydantic`, `anyio`, `h11`, `httpcore`, `certifi`.
Only the `supermemory` package itself needed to be copied.

## ⚠️ Critical Pitfall: auto_recall on Pay-Per-Token Providers

**Setting `auto_recall: true` on OpenRouter (or any metered provider) will burn 40k+ input tokens per turn.** Here's why:

1. `sync_turn()` stores every user+assistant turn as a new Supermemory document
2. `prefetch()` fires every turn, calling `get_profile()` which semantically searches all stored memories
3. As the conversation grows, more memories match the query → the `<supermemory-context>` injection block balloons
4. Next turn: even more memories stored → even more retrieved → compound growth loop

**Fix:** Set `auto_recall: false` in `$HERMES_HOME/supermemory.json`. This kills the prefetch pipeline entirely. Memory tools (`supermemory_search`, `supermemory_store`, etc.) still work when explicitly called — they just don't auto-inject context every turn.

`auto_capture: true` is fine to leave on (it writes memories but doesn't inject them). The problem is exclusively the retrieval+injection side.

The governed plugin's per-turn tool budget and result-count caps do NOT protect against this — those limits control explicit tool calls. `prefetch()` is an automatic lifecycle hook (`on_turn_start` → `prefetch()`) that runs before any tool call and is not subject to the tool budget.

## Config File (optional tuning)
`$HERMES_HOME/supermemory.json` — create/edit for custom settings:

| Key | Default | Description |
|-----|---------|-------------|
| `container_tag` | `hermes` | Use `{identity}` for profile-scoped tags |
| `auto_recall` | `true` | ⚠️ **DANGER on OpenRouter: injects growing memory-context block every turn (40k+ tokens). Set to `false` unless on flat-rate provider.** |
| `auto_capture` | `true` | Store turns after responses |
| `max_recall_results` | `10` | Max items in context |
| `profile_frequency` | `50` | Profile recall interval (turns) |
| `capture_mode` | `all` | Capture aggressiveness |
| `search_mode` | `hybrid` | `hybrid` / `memories` / `documents` |
| `api_timeout` | `5.0` | SDK timeout (seconds) |

## Tools Unlocked
- `supermemory_store` — store an explicit memory
- `supermemory_search` — semantic similarity search
- `supermemory_forget` — forget by ID or query
- `supermemory_profile` — retrieve persistent profile

## Multi-Container Tags
For multiple namespaces, add to `supermemory.json`:
```json
{
  "container_tag": "hermes",
  "enable_custom_container_tags": true,
  "custom_containers": ["work", "personal"],
  "custom_container_instructions": "Use work for job tasks, personal for life context."
}
```

## When you need hard token caps (chained searches, runaway tool calls)

Configurable knobs in `supermemory.json` are advisory — the model can still
pass `limit: 20` to `supermemory_search` and chain many calls per turn. For a
provider-token budget that the model **cannot** override, ship a renamed copy
of the plugin with caps enforced in code. Full recipe with copy-paste patches:
`references/governed-memory-plugin.md`.

On this deployment, `memory.provider` is `supermemory_governed` (container
`voltaic`, max 3 results per search, max 3 memory tool calls per user turn).
The bundled `supermemory` plugin remains on disk but is not selected.
