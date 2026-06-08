# Supermemory Container Architecture — Client-Only Design (2026-06-05)

## Architecture

**Containers are client-only, not domain-suffixed.** There are no `{client}_{domain}` containers
(e.g., `mobilemd_research`, `voltaic_code_architect`). All containers are bare client names:

| Container | Purpose |
|---|---|
| `voltaic` | **Default.** Auto-capture target for ALL profiles. Operational/technical context (tool quirks, API endpoints, patterns). Also serves as client business container when Voltaic IS the active client. |
| `mobilemd` | Client business context only — brand voice, audience data, campaigns, objectives |
| `west_shore_chamber` | Client business context only |

**Key principle:** `voltaic` is the only container that receives auto-capture. All profiles
write their operational learnings there. The `memory` store tool is restricted to client
business context only, targeting the active client's container.

## Resolution Priority (as of 2026-06-05)

```
Priority 1: /data/supermemory.json container_tag        → "voltaic" for all profiles
Priority 2: Hardcoded default in governed plugin         → "voltaic"
```

**`SUPERMEMORY_CONTAINER_TAG` env var is NO LONGER USED.** It was removed from all `.env` files
(2026-06-05). The old pattern of per-profile container isolation via env var overrides is dead.
All profiles share the `voltaic` default.

Config.yaml's `supermemory.container_tag` field is set to `voltaic` in all profiles but is
**never read by the plugin** — it's purely informational.

## Store Tool — Client Business Context ONLY

The `memory` tool (built-in, `action='add'`) is reserved for high-signal client business context:

- ✅ Client brand voice/guidelines, audience demographics, campaign history, business objectives
- ❌ Operational facts (tool quirks, API endpoints, file paths) — auto-capture handles these
- ❌ Task progress, session outcomes (use session_search)

**Exception:** When active client IS `voltaic`, skip the store tool entirely. Auto-capture
already writes to `voltaic`, and since Voltaic IS the client, both operational and business
context land in the same container automatically.

## Recall — Two Searches Per Task

Before executing any client task, run TWO supermemory searches:

1. `voltaic` — operational/technical context
2. `{active_client}` — client business context

- Skip search #2 when active client is `voltaic` (same container)
- Search #2 returning empty for a new client is normal — proceed, no error

## Anti-Duplication (Orchestrator→Worker)

The orchestrator runs both searches during triage and includes results in the task brief body.
Worker profiles (researcher, code_architect) read the brief and do NOT re-run the searches.
The task brief IS their context. This prevents the orchestrator AND the worker from both
burning recall calls on the same queries.

Exception: if the task brief explicitly says "memory search returned nothing" — worker may
run its own search.

## Profile Config Checklist

When configuring a new profile or auditing an existing one:

- [ ] `config.yaml`: `supermemory.container_tag: voltaic`
- [ ] `.env`: NO `SUPERMEMORY_CONTAINER_TAG` line
- [ ] `SOUL.md`: Supermemory Protocol section with recall + store rules (see code_architect SOUL.md for template)
- [ ] `AGENTS.md`: Task brief anti-duplication rule, store discipline
- [ ] `CLAUDE.md` §5: loaded by all profiles — the master recall/store discipline

## Migration from Old Pattern (pre-2026-06-05)

If you find stale `{client}_{domain}` containers or `SUPERMEMORY_CONTAINER_TAG` env vars:

1. Remove `SUPERMEMORY_CONTAINER_TAG` from all `.env` files
2. Set all `config.yaml` `supermemory.container_tag` to `voltaic`
3. Simplify `supermemory.json` `custom_containers` to client-only list
4. Update all profile doctrine to reference CLAUDE.md §5
5. Clean up stale memory facts (use `memory(action='replace')` to update container refs)

## Verification

```bash
# Check no env var overrides remain
grep -r "SUPERMEMORY_CONTAINER_TAG" /data/.env /data/profiles/*/.env 2>/dev/null
# Expected: no output

# Check config container_tag
grep "container_tag" /data/config.yaml /data/profiles/*/config.yaml
# Expected: all say "voltaic"

# Check profiles boot
for HOME in /data /data/profiles/researcher /data/profiles/code_architect; do
  HERMES_HOME=$HOME /opt/hermes/.venv/bin/hermes profile 2>&1 | head -3
done
```
