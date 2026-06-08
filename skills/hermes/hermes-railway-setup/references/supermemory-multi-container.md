# Supermemory Multi-Container Setup (Option B)

## When to use this

You need profile-scoped container isolation but don't want to change the
primary `container_tag` in `supermemory.json` (which would redirect ALL
auto-capture and `memory` tool writes to the new container).

**Option A** (change primary): switch `container_tag` from `voltaic` to
`voltaic_code_architect` — simple, but floods the architecture namespace
with every conversation turn.

**Option B** (multi-container allowlist): keep `voltaic` as primary, add
`voltaic_code_architect` to an allowlist — only deliberate writes target
the architecture namespace. This is what we use.

## Setup (one-time)

Edit `/data/supermemory.json` to add three keys:

```json
{
  "auto_capture": true,
  "auto_recall": false,
  "container_tag": "voltaic",
  "enable_custom_container_tags": true,
  "custom_containers": ["voltaic_code_architect"],
  "custom_container_instructions": "Use voltaic_code_architect for architecture decisions, code reviews, system design, dependency audits, and cross-profile infrastructure facts. Default voltaic for everything else.",
  "max_recall_results": 3,
  "search_mode": "hybrid"
}
```

### What each key does

| Key | Effect |
|---|---|
| `enable_custom_container_tags` | Tells the governed plugin to accept per-call `container_tag` args on tool calls |
| `custom_containers` | Allowlisted tags beyond the primary. The plugin validates every incoming tag against this list before hitting the API (line 678 in `__init__.py`) |
| `custom_container_instructions` | Injected into the system prompt via `system_prompt_block()` — tells the model when to use which namespace |

Takes effect on the **next new session** (plugin reads this file once at `initialize()`).

## How it works after setup

| What | Primary (`voltaic`) | Secondary (`voltaic_code_architect`) |
|---|---|---|
| `auto_capture` (turn sync) | ✅ always writes here | ❌ never — auto-capture always uses primary |
| `memory` tool mirror (`on_memory_write`) | ✅ always writes here | ❌ never — no per-call tag override |
| `supermemory_store` with no tag | ✅ writes here | ❌ |
| `supermemory_store(container_tag="voltaic_code_architect")` | ❌ | ✅ writes here |
| `supermemory_search` with no tag | ✅ searches here | ❌ |
| `supermemory_search(container_tag="voltaic_code_architect")` | ❌ | ✅ searches here |
| Session-end ingest (`on_session_end`) | ✅ always ingests here | ❌ never |

## The fundamental limitation

**Auto-capture and the built-in `memory` tool can NEVER target secondary
containers.** This is by Supermemory's design, stated in the integration
docs: *"Automatic behavior (turn sync, prefetch, session-end ingest)
always uses primary container only."*

The governed plugin mirrors `memory` tool writes via `on_memory_write()`
(line 636-655 of `__init__.py`), and that method calls `add_memory()`
without a `container_tag` override — it falls back to `self._container_tag`
(always the primary).

### Workaround

For architecture facts that must land in `voltaic_code_architect`, call
`supermemory_store` explicitly with the container_tag:

```
supermemory_store(
  content="[Arch] [Decision]: Switched from X to Y because Z.",
  container_tag="voltaic_code_architect"
)
```

The model sees the `custom_container_instructions` in the system prompt
and knows to do this for architecture-relevant content.

## Verification

```bash
# After storing, confirm the write landed in the right container
API_KEY=$(grep SUPERMEMORY_API_KEY /data/.env | cut -d= -f2-)
curl -s -H "Authorization: Bearer $API_KEY" \
  "https://api.supermemory.ai/v3/documents?container_tag=voltaic_code_architect&limit=3"
```

Also verify the SOUL.md / AGENTS.md container tag references match
what's in the allowlist — the plugin validates tags case-sensitively.

## Pitfalls

- **`container_tag` in `config.yaml` is ignored.** The governed plugin reads
  from supermemory.json + env vars only (line 504-507 of `__init__.py`).
  Setting `supermemory.container_tag: voltaic_code_architect` in config.yaml
  has zero effect.

- **Custom tags must match the allowlist exactly.** The `_sanitize_tag()`
  function strips special chars but a case mismatch still fails validation
  (line 678: `if sanitized not in self._allowed_containers`).

- **The built-in `memory` tool silently writes to the wrong container.**
  There is no warning, no error — the write succeeds but lands in the
  primary container. Users asking "why aren't my architecture facts
  showing up?" likely hit this. The fix is explicit `supermemory_store`.

- **`auto_recall` being false means no prefetch for ANY container.**
  Prefetch is global — there is no per-container prefetch toggle. If you
  need passive memory injection for one namespace, you accept the token
  burn for all namespaces.

- **Each profile needs its own `$HERMES_HOME/supermemory.json`.** The plugin
  reads from `$HERMES_HOME/supermemory.json` at `initialize()` — it does NOT
  fall back to `/data/supermemory.json`. If a named profile (e.g.,
  `code_architect`, `researcher`) has no `supermemory.json`, the plugin loads
  with defaults: `enable_custom_container_tags` = `false`, `custom_containers`
  = `[]`. This silently disables multi-container mode — the `container_tag`
  parameter disappears from `supermemory_*` tool schemas, and the model cannot
  target secondary containers on tool calls. **Fix:** copy the file into the
  profile dir: `cp /data/supermemory.json /data/profiles/<name>/`.
  Verification: `supermemory_search` should appear in the tool list with a
  `container_tag` parameter on the next session.
