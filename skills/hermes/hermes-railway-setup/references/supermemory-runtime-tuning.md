# Supermemory Runtime Tuning (`$HERMES_HOME/supermemory.json`)

Companion to the "Tuning a Governed Memory Plugin at Runtime" section of
`SKILL.md`. This file documents every runtime knob, the token impact of each,
and the diagnostic path used to isolate the 40k-token-per-turn issue on the
Voltaic Marketing deployment.

## Where the file is read

`supermemory_governed` (and the bundled `supermemory`) call
`_load_supermemory_config(hermes_home)` inside `initialize()`. It reads
`$HERMES_HOME/supermemory.json` once at session start. Schema is enforced by
`_default_config()` — unknown keys are ignored, malformed JSON falls back to
defaults silently. **Edits take effect on the next new session**, not the
current one.

## Full schema with defaults

```json
{
  "container_tag": "voltaic",
  "auto_recall": true,
  "auto_capture": true,
  "max_recall_results": 3,
  "profile_frequency": 50,
  "capture_mode": "all",
  "search_mode": "hybrid",
  "entity_context": "<see plugin __init__.py for full default>",
  "api_timeout": 5.0,
  "enable_custom_container_tags": false,
  "custom_containers": [],
  "custom_container_instructions": ""
}
```

## Per-flag token impact

| Flag | Token cost when `true` | Notes |
|---|---|---|
| `auto_recall` | **High — primary suspect for runaway burn.** Every turn: profile fetch + search results → `<supermemory-context>` block injected into system prompt. Grows turn-over-turn because each turn's stored memory becomes next turn's retrieved memory. | Disable first when diagnosing token bloat |
| `auto_capture` | Low input-token cost. Sends conversation turns to Supermemory in a background thread — doesn't grow the prompt. But it's what *feeds* the loop `auto_recall` retrieves from. | Safe to keep `true` even when `auto_recall: false` |
| `max_recall_results` | Linear with value. Hard-capped at 3 by the governed plugin's module-level `_MAX_TOOL_RESULT_LIMIT`. Setting higher is silently clamped. | Already minimal at default |
| `profile_frequency` | Inverse: lower = more frequent profile dumps. Default `50` is sane; setting `1` means profile dump every turn. | Only matters when `auto_recall: true` |
| `search_mode` | None directly. `hybrid` returns memories AND documents; `memories` only returns micro-facts (smaller blobs). | Marginal in practice |
| `entity_context` | One-time per write, not per turn. Capped at 1500 chars by `_clamp_entity_context`. | Negligible |
| `api_timeout` | None. Operational only. | — |

## Diagnostic path used on the Voltaic Marketing deployment

Symptom: input tokens jumped from baseline (~2k system prompt) to 40k+ per
user message immediately after `supermemory_governed` was wired up. The
SOUL.md and `system_prompt_block()` text were small and unchanged.

Steps that isolated the cause:

1. **Confirmed the static system prompt was small.** `SOUL.md` was 1792 bytes,
   `system_prompt_block()` output was ~6 lines. Static surface was not the
   problem.
2. **Read the plugin source.** Two methods get called every turn from the
   agent loop: `prefetch(user_message)` and `sync_turn(user, assistant)`.
3. **Traced `prefetch()`** (line 565 of `__init__.py`): calls
   `client.get_profile(query=...)`, formats `static + dynamic + search_results`
   into the `_format_prefetch_context()` XML block, returns it for injection
   into the system prompt.
4. **Traced `sync_turn()`** (line 582): stores cleaned user+assistant content
   as a memory document with category `conversation_turn` — runs in a
   background thread, doesn't touch prompt size.
5. **Conclusion:** the burn is `auto_recall: true` → `prefetch()` → growing
   retrieved-memory list every turn (because each `sync_turn` adds to what
   `prefetch` later finds).
6. **Fix:** wrote `auto_recall: false` to `/data/supermemory.json`. Verified
   the file change with `read_file`. Documented that the change takes effect
   on the next session.

## Recommended defaults for token-conscious / agency setups

```json
{
  "auto_capture": true,
  "auto_recall": false,
  "container_tag": "<client_or_agency>",
  "max_recall_results": 3,
  "search_mode": "hybrid"
}
```

**Note:** There is no `recall_limit` config key. The result cap is enforced
entirely by the plugin's module-level constant `_MAX_TOOL_RESULT_LIMIT = 3` in
`__init__.py` and by `max_recall_results` in this JSON file (clamped 1–3). Do
not attempt to set `memory.recall_limit` in `config.yaml` — the key does not
exist and will be silently ignored.

Rationale:
- `auto_capture: true` — writes are cheap, and you want the long-term store
  populated so the model has something to deliberately search later.
- `auto_recall: false` — kill the injection loop entirely. The model has
  `supermemory_search` / `supermemory_profile` tools and will use them when
  the system block tells it to.
- `max_recall_results: 3` — matches the hard cap in `_MAX_TOOL_RESULT_LIMIT`,
  so explicit tool calls also stay bounded.

## When to re-enable `auto_recall`

Only when both of these are true:
- Single-tenant deployment (no client isolation worry).
- You've measured that the passive profile injection is genuinely useful —
  e.g. the model needs persistent biographical facts that it wouldn't think
  to search for.

For multi-tenant or token-budgeted setups, leave it off and rely on the
explicit tool route.

## Profile-scoped behavior (both profiles share one file)

`initialize()` reads `$HERMES_HOME/supermemory.json` once per session — there is
no per-profile variant. Both `default` (orchestrator) and `researcher` profiles
read the same `/data/supermemory.json`. If the researcher needs more aggressive
recall than the orchestrator, you have two options:

1. **Global `auto_recall: false` + orchestrator manually calls `supermemory_profile`.**
   Keeps token burn deterministic — only the orchestrator pays for recall when
   it explicitly decides to.

2. **Code-level profile differentiation.** `initialize()` receives `agent_identity`
   in `kwargs` (e.g. `"default"`, `"researcher"`). You can branch `self._auto_recall`
   on identity in `initialize()` to let the researcher prefetch passively while
   the orchestrator stays dark. This requires editing the plugin source.

Do NOT create a second `supermemory.json` under the researcher profile directory
— the plugin doesn't look there, and `$HERMES_HOME` is shared.

## How this interacts with the governed plugin's other caps

The module-level caps (`_MAX_TOOL_RESULT_LIMIT = 3`,
`_MAX_TOOL_ITERATIONS_PER_TURN = 3`) only protect against runaway *tool calls*.
They do **not** protect against `auto_recall`'s passive injection — that path
bypasses the tool router entirely and writes directly into the prompt via
`prefetch()`. The supermemory.json `auto_recall` flag is the only control.

This is the asymmetry that made the bug confusing: a "governed" plugin with
hard caps still leaked 40k tokens per turn because the leak was on a code path
the caps don't cover.
