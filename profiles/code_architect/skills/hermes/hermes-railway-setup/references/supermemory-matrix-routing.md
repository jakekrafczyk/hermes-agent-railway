# Supermemory Matrix Routing — Multi-Tenant Container Tag Composition

## What it solves

When multiple agency clients share one Supermemory instance and one `voltaic`
container, client data bleeds across research sessions. The matrix routing pattern
composes a unique `container_tag` per client×domain pair, isolating memory at the
Supermemory container level.

## Architecture

```
active_client.yaml          ← single source of truth for active client
    ↓ read by both profiles before every memory tool call
    ↓
container_tag = "{active_client}_{active_domain}"
    ↓
Supermemory API call scoped to that container
```

## Files involved

| File | Role | Updated by |
|---|---|---|
| `/data/workspace/active_client.yaml` | Holds `active_client` string (e.g. `mobilemd`) | Operator or orchestrator at session start |
| Profile `AGENTS.md` (both default and researcher) | Embeds the routing rules the model must follow | Doctrine edit (one-time) |
| `supermemory.json` | Sets primary `container_tag` to `voltaic` as fallback | Config (already done) |

## Active client file format

```yaml
# /data/workspace/active_client.yaml
active_client: voltaic
```

Switch clients before starting work:

```bash
echo "active_client: mobilemd" > /data/workspace/active_client.yaml
echo "active_client: westshore" > /data/workspace/active_client.yaml
```

## Container tag composition rules

| Profile | Domain | Example `container_tag` |
|---|---|---|
| orchestrator (default) | `none` — keeps `voltaic` | `voltaic` |
| researcher | `research` | `mobilemd_research` |
| future: architect | `architecture` | `mobilemd_architecture` |
| future: designer | `ui-ux` | `mobilemd_ui-ux` |
| future: seo | `seo` | `mobilemd_seo` |

The orchestrator keeps `voltaic` (unchanged — it's the cross-client management
layer). All worker profiles compose `{active_client}_{domain}`.

## AGENTS.md routing rules (verbatim snippet for paste)

Append this block to every profile's `AGENTS.md` (customize domain per profile):

```markdown
## SUPERMEMORY AGENCY MATRIX ROUTING

1. You operate in a multi-tenant agency environment. To protect token boundaries
   and prevent data bleeding, you must ALWAYS isolate your memory queries.
2. Before invoking any Supermemory tool (`supermemory_search`, `supermemory_store`,
   `supermemory_forget`, `supermemory_profile`), you **MUST** read
   `/data/workspace/active_client.yaml` to extract the `active_client` string.
3. Identify your current profile domain (e.g., 'research', 'architecture',
   'ui-ux', 'seo').
4. Formulate `container_tag` as: "{active_client}_{active_domain}"
   (Example: `container_tag: "mobilemd_research"`).
5. **NEVER** execute a memory tool query with a blank or global `container_tag`.
   If `active_client` is not set or the file is missing, halt and escalate.
6. Apply this to **all four** Supermemory tool calls — search, store, forget,
   and profile.
```

## Adding this to a new profile

1. Create or edit `/data/profiles/<name>/AGENTS.md`
2. Paste the routing rules block (customize domain in rule 3)
3. That's it — `active_client.yaml` and the plugin are already shared infrastructure
4. No plugin changes, no config changes, no `supermemory.json` changes needed

## Why not use multi-container mode (`enable_custom_container_tags`)?

The governed plugin supports a multi-container mode that whitelists discrete
container names in `supermemory.json`. But that approach requires pre-declaring
every client container. The matrix routing pattern is more flexible:
- Adding a client = writing one line to `active_client.yaml`
- Adding a domain = just using a new suffix in the profile's AGENTS.md
- No plugin or config changes for new client×domain combinations

## Pitfalls

- **`active_client.yaml` must exist before any memory tool call.** If the file is
  missing or `active_client` is blank, the researcher must halt and escalate — not
  guess or fall back to `voltaic`.
- **Both profiles share one active_client.yaml.** If the orchestrator switches
  the active client mid-session, the researcher picks up the new client on its
  next tool call. This is desired behavior for task-switching.
- **No per-profile `supermemory.json`.** The runtime tuning file is global.
  Matrix routing is enforced at the AGENTS.md/runtime level, not the config level.
- **Container tags are composed, not validated against a list.** Supermemory
  creates containers implicitly on first write. If the model misspells the tag,
  a new separate container silently gets created. Profiles must read the exact
  string from `active_client.yaml`.
- **The orchestrator keeps `voltaic`.** Do NOT compose `voltaic_orchestrator`.
  The orchestrator needs cross-client visibility for triage. `voltaic` stays.