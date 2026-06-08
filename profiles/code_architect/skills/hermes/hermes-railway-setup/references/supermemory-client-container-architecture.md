# Supermemory Client-Container Architecture (2026-06-05)

Container tags reorganized from `{client}_{domain}` to client-only, with
`voltaic` as the shared default for operational/technical context.

## Container Layout

| Container | Purpose | Write Path |
|---|---|---|
| `voltaic` | Default. Auto-capture target. Operational/technical context for ALL profiles. Also serves as business container when Voltaic IS the active client. | Auto-capture + `memory` tool |
| `mobilemd` | Client business context — brand voice, audience, campaigns, objectives | `memory` tool (intentional, high-signal only) |
| `west_shore_chamber` | Client business context | `memory` tool (intentional, high-signal only) |

## Recall Protocol (Two Searches per Task)

Before executing any client task, run TWO supermemory searches:
1. `voltaic` — operational/technical context (tool quirks, API endpoints, patterns, past decisions)
2. `{active_client}` — client business context (brand voice, audience, campaigns, objectives)

- **Skip search #2 when active client IS `voltaic`** — same container.
- If search #2 returns empty (new client): proceed, no error.

## Store Discipline (CLAUDE.md §5)

The `memory` tool is RESTRICTED to client business context ONLY:
- ✅ Brand voice, audience demographics, campaign history, business objectives, market positioning
- ❌ Operational facts (tool quirks, API endpoints, file paths) — auto-capture handles these
- ❌ Task progress, session outcomes (session_search for those)
- **When active client is `voltaic`:** Skip the store tool entirely. Auto-capture writes both
  operational and business context to `voltaic` automatically.

## Anti-Duplication (Orchestrator → Worker)

When the orchestrator delegates to a worker profile:
- The orchestrator runs the two searches during triage and includes results in the task brief
- Worker profiles do NOT re-run the same searches — the task brief IS their context
- Exception: if the task brief explicitly says "memory search returned nothing" — worker may run its own

## Files Changed

| File | Change |
|---|---|
| `supermemory.json` | Containers: 10→3. `voltaic` (default), `mobilemd`, `west_shore_chamber` |
| `CLAUDE.md` | New §5 — Supermemory Recall/Store Discipline |
| `code_architect/SOUL.md` | Supermemory section rewritten — new protocol, container refs updated |
| `code_architect/config.yaml` | `container_tag: voltaic_code_architect` → `voltaic` |
| `code_architect/.env` | Removed `SUPERMEMORY_CONTAINER_TAG` override |
| `researcher/.env` | Removed `SUPERMEMORY_CONTAINER_TAG` override |
| `researcher/AGENTS.md` | New Supermemory Protocol section — anti-duplication, store discipline |
| `AGENTS.md` (orchestrator) | Step 2 Triage Checklist rewritten — two-search recall, anti-duplication |

## Plugin Installation Across Profiles

Container tags are now uniform (`voltaic` across all profiles), so the
`SUPERMEMORY_CONTAINER_TAG` env var is no longer needed. The `container_tag`
in `supermemory.json` is the single source of truth.

However, the **plugin itself must be installed per-profile**. Each profile
needs a symlink from `$HERMES_HOME/plugins/supermemory_governed/` →
`/data/plugins/supermemory_governed/`. Without this, auto-capture silently
fails for that profile. See `hermes-railway-setup` skill "Sharing Plugins
Across Profiles" section for the setup command.