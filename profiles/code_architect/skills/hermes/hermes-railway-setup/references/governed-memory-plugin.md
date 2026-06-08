# Governed Memory Plugin Pattern

When the bundled `supermemory` plugin (or any bundled memory provider) burns
too many provider tokens — chained searches, unbounded result counts, global
queries — you can replace it without touching root-owned `/opt/hermes/` by
shipping a **renamed copy** with hard caps baked into code.

This is durable for any class of "tighten an out-of-the-box plugin's behavior
for a paying-client workload."

## Why renaming works

`/opt/hermes/plugins/memory/__init__.py` discovery rule:

- Bundled providers under `/opt/hermes/plugins/memory/<name>/` are scanned first.
- User-installed providers under `$HERMES_HOME/plugins/<name>/` are scanned next.
- On **name collision**, bundled wins (`seen` set in `_iter_provider_dirs`).
- `find_provider_dir(name)` resolves by **exact name** — bundled checked first,
  then user-installed.

So you can't override `"supermemory"`, but you can register `"supermemory_governed"`
in `$HERMES_HOME/plugins/supermemory_governed/` and point `memory.provider` at
the new name. The bundled plugin stays on disk and never gets selected.

## Recipe (concrete, applied for Voltaic Marketing)

```bash
# 1. Copy the bundled plugin to a new name under $HERMES_HOME/plugins/
mkdir -p /data/plugins/supermemory_governed
cp /opt/hermes/plugins/memory/supermemory/__init__.py \
   /data/plugins/supermemory_governed/__init__.py
cp /opt/hermes/plugins/memory/supermemory/plugin.yaml \
   /data/plugins/supermemory_governed/plugin.yaml
```

Edit `/data/plugins/supermemory_governed/__init__.py`:

1. Change the provider name so it's a distinct registration:
   ```python
   @property
   def name(self) -> str:
       return "supermemory_governed"
   ```

2. Add module-level hard caps near the top:
   ```python
   _DEFAULT_CONTAINER_TAG = "voltaic"          # or whatever the client tag is
   _DEFAULT_MAX_RECALL_RESULTS = 3             # was 10
   _MAX_TOOL_RESULT_LIMIT = 3                  # absolute clamp on search limit
   _MAX_TOOL_ITERATIONS_PER_TURN = 3           # per-user-prompt budget
   ```

3. Clamp `max_recall_results` to the same ceiling in `_load_supermemory_config`:
   ```python
   config["max_recall_results"] = max(1, min(_MAX_TOOL_RESULT_LIMIT, int(...)))
   ```

4. Add a per-turn budget counter — initialize, reset, enforce:
   ```python
   # in __init__:
   self._tool_iterations_this_turn = 0

   # in on_turn_start:
   self._tool_iterations_this_turn = 0

   # at the top of handle_tool_call, before dispatch:
   self._tool_iterations_this_turn += 1
   if self._tool_iterations_this_turn > _MAX_TOOL_ITERATIONS_PER_TURN:
       return tool_error(
           f"Supermemory tool-call budget exhausted for this turn "
           f"(limit: {_MAX_TOOL_ITERATIONS_PER_TURN} calls). "
           "Stop calling memory tools and answer with what you already have."
       )
   ```

5. Clamp the per-call `limit` in `_tool_search`:
   ```python
   limit = max(1, min(_MAX_TOOL_RESULT_LIMIT,
                      int(args.get("limit", _MAX_TOOL_RESULT_LIMIT)
                          or _MAX_TOOL_RESULT_LIMIT)))
   ```

6. Update `SEARCH_SCHEMA` description so the model sees the caps in its tool list:
   ```python
   "description": (
       "Search long-term memory by semantic similarity within the active container. "
       "Results are HARD-CAPPED at 3. Total calls per user turn are HARD-CAPPED at 3 — "
       "do not retry or chain searches; one targeted query is the norm."
   ),
   ```

7. Update `system_prompt_block` to declare the caps and the container-only policy
   so they appear in the agent's system prompt every session:
   ```python
   "# Supermemory (governed)",
   f"Active. Container: {self._container_tag}. ALL queries are scoped to this container — never global.",
   f"HARD CAPS (enforced server-side): max {_MAX_TOOL_RESULT_LIMIT} results per search, "
   f"max {_MAX_TOOL_ITERATIONS_PER_TURN} memory tool calls per user turn.",
   "Do not call memory tools speculatively. If the answer is already in the current thread, do NOT search.",
   ```

8. Update `plugin.yaml`:
   ```yaml
   name: supermemory_governed
   version: 1.0.0
   description: "Supermemory with token-governance hard caps..."
   pip_dependencies:
     - supermemory
   ```

Finally:

```bash
# Point Hermes at the new provider
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes config set memory.provider supermemory_governed

# (Optional) explicit defaults file
# ⚠️ auto_recall: true is a token bomb on OpenRouter — see supermemory-setup.md pitfall.
# Set to false unless you're on a flat-rate provider and actively want context injection.
cat > /data/supermemory.json <<'JSON'
{
  "auto_capture": true,
  "auto_recall": false,
  "container_tag": "voltaic",
  "max_recall_results": 3,
  "search_mode": "hybrid"
}
JSON
```

## Why caps belong in code, not just config

The bundled plugin already exposes `max_recall_results` and `container_tag` via
`supermemory.json` — but `_tool_search` still accepts `limit` up to 20, and
nothing stops the model from chaining 8 searches in one turn. Defaults the model
can override aren't defenses; only module-level constants enforced in
`handle_tool_call` / `_tool_search` are.

## Verification

```python
# Run from $HERMES_HOME workspace with /opt/hermes/.venv/bin/python:
import os, json, sys
os.environ.setdefault('HERMES_HOME', '/data')
from plugins.memory import discover_memory_providers, load_memory_provider

# 1. Both providers discoverable, governed one available
for name, _, avail in discover_memory_providers():
    if 'supermemory' in name:
        print(f'{name:30s} available={avail}')

# 2. Caps active
p = load_memory_provider('supermemory_governed')
p.initialize(session_id='t', hermes_home='/data')
mod = sys.modules['_hermes_user_memory.supermemory_governed']
assert p._container_tag == 'voltaic'
assert mod._MAX_TOOL_RESULT_LIMIT == 3
assert mod._MAX_TOOL_ITERATIONS_PER_TURN == 3

# 3. Per-turn cap fires
p._tool_search = lambda args: json.dumps({'results': [], 'count': 0})
p.on_turn_start(1, '')
for i in range(4):
    out = p.handle_tool_call('supermemory_search', {'query': 'x'})
    print(f'  call #{i+1}: {out[:100]}')
# Expect: calls 1-3 return {"results": []...}; call 4 returns budget-exhausted error.
```

## Pitfalls

- **Per-turn tool budgets don't protect against prefetch() token bloat.** The
  caps in `handle_tool_call` only limit explicit `supermemory_search` calls from
  the model. `prefetch()` is a lifecycle hook that fires automatically every turn
  and is NOT subject to the tool budget. On pay-per-token providers like
  OpenRouter, the resulting `<supermemory-context>` injection block can reach
  40k+ tokens/turn. **Fix:** set `auto_recall: false` in `$HERMES_HOME/supermemory.json`.
  See `references/supermemory-runtime-tuning.md` for the full diagnosis.
- **Don't try to overwrite `/opt/hermes/plugins/memory/supermemory/__init__.py`** —
  the file is root-owned and not writable by `hermes`. The entrypoint runs as root
  briefly but a patch step there resets on every Railway redeploy. Renaming is
  cleaner.
- **Supermemory tools are already exposed as active Hermes tools.** The plugin's
  `get_tool_schemas()` registers 4 tools (`supermemory_store`, `supermemory_search`,
  `supermemory_forget`, `supermemory_profile`) directly with Hermes' tool registry.
  `handle_tool_call()` dispatches them. This is NOT gated by `tools.pre_selection`,
  `tools.defer_loading`, or any `config.yaml` `tools.*` key — those control Hermes'
  built-in tool loader, not plugin-registered tools. The tools are available to
  both default and researcher profiles automatically at session start. No
  `explicit_tool_routing` toggle is needed or exists for this.
- **Both profiles share a single `supermemory.json`.** The plugin reads from
  `$HERMES_HOME/supermemory.json` once per session in `initialize()`. There is no
  per-profile override path (no `$HERMES_HOME/profiles/<name>/supermemory.json`).
  Both the `default`/`orchestrator` and `researcher` profiles load the same file.
  If you need different `auto_recall` behavior per profile, you must either
  (a) set `auto_recall: false` globally and let the orchestrator manually call
  `supermemory_profile` when needed, or (b) modify the plugin to read
  `agent_identity` from kwargs and switch behavior in `prefetch()`.
- **`tools.pre_selection: true` does NOT control plugin-registered tools.** This
  config key tells Hermes to advertise a reduced subset of *built-in* tools to
  the model based on the task context. Plugin tools (Supermemory's 4, Firecrawl's
  16, etc.) are always in the tool list regardless. Setting `pre_selection:
  false` won't make Supermemory tools "more available" — they already are.
- **The SDK still needs to be importable.** Apply the supermemory-setup steps
  (copy `supermemory` package to `/opt/hermes-railway/`) BEFORE the renamed
  plugin will be `available=True`.
- **Discovery uses exact name.** If you rename the plugin directory but forget
  to change `provider.name`, `find_provider_dir("supermemory_governed")` works
  but the loader logs a warning and `cfg_get(memory, provider)` mismatch may
  confuse memory status. Keep dir name, file name, and `name` property aligned.
- **The bundled plugin still appears in `hermes memory status` listings.** That's
  fine — it just isn't selected. Don't delete it (you can't anyway, root-owned).

## When NOT to use this

- If the user just wants a different default container tag, edit `supermemory.json`
  and stop. No code copy needed.
- If the user wants to log/observe memory traffic without changing caps, write a
  wrapper plugin that delegates to the bundled one rather than copying its source.
- If Hermes ships first-class budget controls in a future version, prefer those
  over the renamed-copy pattern (they'll be maintained upstream).

## Multi-client extension

If the agency adds clients beyond Voltaic, switch the governed plugin to
multi-container mode by updating `/data/supermemory.json`:

```json
{
  "container_tag": "voltaic",
  "enable_custom_container_tags": true,
  "custom_containers": ["mobilemd", "west_shore_chamber"],
  "custom_container_instructions": "Use mobilemd for the medical client, west_shore_chamber for chamber-of-commerce work. Never mix vectors across containers."
}
```

The governed plugin's `_resolve_tool_container_tag` already whitelists tags —
no extra code change needed.
