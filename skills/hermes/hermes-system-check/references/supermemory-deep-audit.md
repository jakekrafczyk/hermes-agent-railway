# Supermemory Deep Audit Checklist

Run when: memory seems broken, container tag changed, plugin upgraded, or
after any supermemory config mutation.

## Step 1: Plugin Code Review

```bash
# Is the plugin loaded?
ls /data/plugins/supermemory*/plugin.yaml

# Read the plugin implementation to understand caps and routing
read_file(path="/data/plugins/supermemory_governed/__init__.py")
```

Key things to extract from `__init__.py`:
- **Hard caps**: `_MAX_TOOL_RESULT_LIMIT` and `_MAX_TOOL_ITERATIONS_PER_TURN`
- **Default container_tag**: `_DEFAULT_CONTAINER_TAG`
- **Tool schemas**: `STORE_SCHEMA`, `SEARCH_SCHEMA`, `FORGET_SCHEMA`, `PROFILE_SCHEMA`
- **Write mirroring**: `on_memory_write()` mirrors built-in `memory` tool writes to supermemory
- **Turn capture**: `sync_turn()` captures conversations, `on_session_end()` ingests full sessions
- **Prefetch gate**: `prefetch()` returns empty if `auto_recall` is false

## Step 2: Config Cross-Check

Compare FOUR config sources — **env var takes highest priority**:

| Source | File | Keys to check |
|---|---|---|
| **Env var (highest priority)** | Profile `.env` at `$HERMES_HOME/.env` | `SUPERMEMORY_CONTAINER_TAG` — **silently overrides** `container_tag` in config.yaml |
| Hermes config | `/data/config.yaml` | `memory.provider`, `supermemory.container_tag`, `supermemory.api_base` |
| Runtime tuning | `/data/supermemory.json` | `container_tag`, `auto_recall`, `auto_capture`, `max_recall_results`, `search_mode`, `enable_custom_container_tags` |
| Integration docs | `https://supermemory.ai/docs/integrations/hermes` | Expected defaults, available options |

**Resolution chain** (per plugin `__init__.py` line 502-507):
```
SUPERMEMORY_CONTAINER_TAG env var  →  config.yaml container_tag  →  _DEFAULT_CONTAINER_TAG
         (wins if set)                    (fallback)                   (last resort)
```
The `{identity}` template in the config value is replaced with the agent's identity
(profile name or "default"). A `.env` override bypasses this template entirely.

Verify:
- `config.yaml` has `memory.provider: supermemory` (or governed variant)
- `supermemory.json` container_tag matches what profiles expect
- **Check EVERY profile's `.env`** for `SUPERMEMORY_CONTAINER_TAG` — if set, it overrides config.yaml
- API key exists in `/data/.env` as `SUPERMEMORY_API_KEY=sm_...`
- `auto_recall` is intentionally set (false = no context injection, saves tokens; true = prefetch active)
- `enable_custom_container_tags` + `custom_containers` if multi-container needed

**Multi-profile audit** (critical for multi-profile setups):
```bash
for d in /data /data/profiles/*/; do
  echo "=== $(basename $d) ==="
  grep "SUPERMEMORY_CONTAINER_TAG" "$d/.env" 2>/dev/null || echo "(not set)"
done
```
Any profile with the env var set will silently ignore its config.yaml container_tag.

## Step 3: Direct API Probe

The SDK endpoints may redirect or 404. Use the v4 search endpoint for verification:

```bash
# Get API key
API_KEY=$(grep SUPERMEMORY_API_KEY /data/.env | cut -d= -f2-)

# CORRECT: v4 search endpoint (working as of May 2026)
curl -s -X POST "https://api.supermemory.ai/v4/search" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q":"test query","containerTag":"voltaic","limit":3,"searchMode":"hybrid"}'
```

**Key:** `containerTag` is singular (not `containerTags`). `searchMode` supports `memories`, `documents`, `hybrid`.

### Deprecated / Broken Endpoints (May 2026)

| Endpoint | Status | Notes |
|---|---|---|
| `/v3/memories` | 308 → `/v3/documents` | Redirect, then 404 |
| `/v3/documents` | 404 | Returns "404 Not Found" |
| `/v3/memory-entries/search` | 404 | Listed in doc index, not functional |
| `/v4/documents?containerTag=...` | Empty | Returns no content, not a search endpoint |

**The only working search path is `POST /v4/search`.**

### Async Indexing Pitfall

The built-in `memory` tool stores to local MEMORY.md immediately AND mirrors to
Supermemory via `on_memory_write()`, but Supermemory indexing is ASYNC. A fact
stored seconds ago will NOT appear in `/v4/search` results — the RAG pipeline
needs time to embed and index the new content.

**Verification workflow:**
1. Store with `memory(action='add')` → confirm in local MEMORY.md immediately
2. Wait 30-60s for Supermemory async indexing
3. Then probe with `POST /v4/search`

Do NOT conclude "store failed" if a search right after storage returns empty.

## Step 4: Container Tag Alignment

Check that the tag used in SOUL.md / AGENTS.md routing MATCHES what supermemory.json
actually writes to. The full alignment matrix includes ALL config sources:

| Check | Source |
|---|---|
| What SOUL.md mandates | `read_file` → Supermemory section |
| What config.yaml declares | `supermemory.container_tag` |
| **What .env overrides** | `grep SUPERMEMORY_CONTAINER_TAG $HERMES_HOME/.env` per profile |
| What supermemory.json uses | `container_tag` key |
| What's actually stored | API probe (Step 3) |

Common mismatches:
- SOUL.md says `voltaic_code_architect` but supermemory.json has `voltaic`
- Profile `.env` has `SUPERMEMORY_CONTAINER_TAG=voltaic_social` which silently overrides config.yaml's `container_tag: voltaic` — memories land in a different container than expected
- Fix: either remove the env var (let config.yaml win) or change it to match the intended tag

## Step 5: Tool Availability

The governed plugin registers these tools via `get_tool_schemas()`:
- `supermemory_store`
- `supermemory_search`
- `supermemory_forget`
- `supermemory_profile`

If they don't appear in the model's tool list, check:
- `auto_recall: false` does NOT disable tool registration (only suppresses prefetch)
- Provider must be `_active = True` (requires API key + SDK import success)
- `agent_context` must NOT be `cron`, `flush`, or `subagent` (disables writes)

## Step 6: Storage Gap Check

Even when the plugin is active and tools are available, memories may not land in the
expected container. Common failure modes:

| Symptom | Cause | Fix |
|---|---|---|
| `memory` tool writes go to wrong container | `on_memory_write` uses primary tag only, no per-call container override | Enable multi-container or change primary tag |
| Conversation turns not captured | `auto_capture: false` or `agent_context` in deny-list | Set `auto_capture: true` |
| Session ingest fails silently | HTTPError caught, only logged at WARNING | Check API connectivity, key validity |
| Prefetch always empty | `auto_recall: false` (intentional token-saving measure) | Leave as-is if token budget is tight |
| **Memories stored to unexpected container (e.g. `voltaic_social` instead of `voltaic`)** | Profile `.env` has `SUPERMEMORY_CONTAINER_TAG` set, overriding config.yaml | Check `.env` across ALL profiles; remove or correct the env var |

## Audit Record Template

After audit, store compressed findings:

```
[Arch] [CrossProfile]: Supermemory audit YYYY-MM-DD — plugin=<name>, container=<tag>,
  auto_recall=<bool>, memories_stored=<count>, gaps=<list>
```
