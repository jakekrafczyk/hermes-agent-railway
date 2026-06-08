# Multi-Profile Task Coordination

Pattern for coordinating multiple Hermes profiles sharing a filesystem and
Supermemory. Generalized from the Voltaic Marketing deployment:
orchestrator → researcher + code_architect + future profiles.

## Core Design: Manifest-Driven Discovery

The orchestrator does NOT hardcode which profiles exist. It reads two YAML
manifest files at session start:

| File | Owns |
|---|---|
| `/data/workspace/profiles.yaml` | Profile names, domains, task_types, config paths, routing priorities |
| `/data/workspace/clients.yaml` | Agency client registry (ID, name, container_prefix) |

The orchestrator reads both, presents a client selection prompt, then knows
both WHO the client is and WHAT workers are available.

## Session Startup Protocol (Orchestrator)

Every new session, before responding:

1. `read_file("/data/workspace/clients.yaml")` → know available clients
2. `clarify` → present client selection prompt, let user pick
3. `write_file("/data/workspace/active_client.yaml", "active_client: <chosen_id>")`
4. `read_file("/data/workspace/profiles.yaml")` → know available workers
5. `search_files(target="files", pattern="task_*.md", path="/data/workspace/triage/inbox/")`

After ANY client switch, repeat steps 1-3. Client isolation is cryptographic —
no Client A data touches a Client B task.

## Profiles Manifest Format

```yaml
# /data/workspace/profiles.yaml
profiles:
  orchestrator:
    name: "default"
    domain: "orchestration"
    description: "Central router — investigates context, delegates, resolves."
    config_path: "/data/config.yaml"
    task_types: []  # Creates tasks, doesn't receive them
  researcher:
    name: "researcher"
    domain: "research"
    description: "Web scraping, competitive analysis, data gathering."
    config_path: "/data/profiles/researcher/config.yaml"
    task_types: [research, scrape, competitive_analysis, social_media, authenticated]
  code_architect:
    name: "code_architect"
    domain: "architecture"
    description: "System design, code review, refactoring, infrastructure."
    config_path: "/data/profiles/code_architect/config.yaml"
    task_types: [code_review, architecture, bug_hunt, dependency_audit, documentation, infrastructure]

routing_priority:
  research_tasks: ["researcher"]
  code_tasks: ["code_architect"]
  # Future:
  # design_tasks: ["design"]
  # social_tasks: ["social_media"]
  # seo_tasks: ["seo"]
```

Future profiles (design, social_media, seo) have commented templates in the
manifest. Uncomment to activate — the orchestrator picks them up on next session.

## Clients Manifest Format

```yaml
# /data/workspace/clients.yaml
clients:
  voltaic:
    name: "Voltaic Marketing (Agency)"
    domain: "voltaicmarketing.com"
    container_prefix: "voltaic"
    active: true
  mobilemd:
    name: "MobileMD"
    domain: "mobilemd.com"
    container_prefix: "mobilemd"
    active: true
  west_shore_chamber:
    name: "West Shore Chamber of Commerce"
    domain: "westshorechamber.org"
    container_prefix: "west_shore_chamber"
    active: true
```

`container_prefix` feeds into Supermemory routing: `{prefix}_{domain}`.

## Triage Checklist (Mandatory Before Delegation)

The orchestrator MUST work through these steps before writing any task brief:

1. **Client Context** — read `active_client.yaml`, confirm scope
2. **Memory Search** — search `{active_client}_{domain}` for past related work
3. **Competitive Landscape** — SearXNG search for market context (skip for code/infra tasks)
4. **Profile Selection** — match task_type to profile manifest, use routing_priority for tiebreaks
5. **Delegation** — write task brief with full context from steps 1-4

## Delegation Routing Matrix (in AGENTS.md)

The orchestrator's AGENTS.md contains a routing matrix mapping task domains to
profiles. Example:

| Task Domain | Profile | task_type Value |
|---|---|---|
| Web research, scraping | researcher | research, scrape |
| Competitive analysis | researcher | competitive_analysis |
| Code review, refactoring | code_architect | code_review, architecture |
| Bug investigation | code_architect | bug_hunt |
| Dependency audits | code_architect | dependency_audit |

## Generalized Task Format

### Task Request (orchestrator → worker)

Written to `/data/workspace/triage/task_requests/task_<uuid>.md`:

```yaml
---
task_id: <uuid>
assignee_profile: researcher | code_architect | design | social_media | seo
assignee_domain: research | architecture | design | social | seo
created_at: '<ISO 8601>'
task_type: <from profile's task_types list>
priority: low | normal | high | urgent
deadline: '<ISO 8601>'   # optional
freshness: live | cached  # optional — overrides researcher's domain default
---

# Task: <one-sentence goal>

## Context (from triage investigation)
- Memory search findings: <summary or "none found">
- SearXNG landscape: <summary or "N/A">
- Prior related work: <summary or "none">

## Scope
- What to investigate: <specific scope>
- What NOT to investigate: <constraints>

## Target
- URLs/sites: <if known, else "use your tools to find">

## Output Format
- Expected output_type: <from .task-format.md>
- Special instructions: <proxy, mobile, maxAge:0, etc.>
```

### Task Output (worker → inbox)

Written to `/data/workspace/triage/inbox/task_<uuid>.md`:

```yaml
---
task_id: "uuidv4"           # matches filename
profile: "<profile_name>"   # researcher, code_architect, etc.
timestamp: "ISO8601"
status: complete|partial|failed
output_type: <see .task-format.md for full list>

# Error fields (only when status=failed)
error_type: auth_gate|rate_limit|parse_fail|connection_error|timeout|ssl_error|model_error|tool_unavailable|unknown
severity: blocking|degraded|warning|info
step: "string"
blocking_url: "url or null"
fix_hint: "what might fix it"
---
```

### Freshness Override

The optional `freshness` field in task request frontmatter lets the orchestrator
override the researcher's domain-default cache behavior per task:

| Value | Effect |
|---|---|
| `live` | Force `maxAge: 0` — fetch fresh, bypass cache |
| `cached` | Use Firecrawl cache (faster, cheaper) |
| Absent | Follow researcher's Domain Research Mode defaults |

Use `freshness: live` for code docs, implementation guides, tech research, social
data — anything where staleness matters. Default (absent) for general market
research and competitive analysis.

## Filesystem Layout

```
/data/workspace/
├── profiles.yaml              # Profile manifest
├── clients.yaml               # Client registry
├── active_client.yaml         # Set by orchestrator: {active_client: <id>}
├── triage/
│   ├── .task-format.md        # Format spec — canonical reference
│   ├── inbox/                 # Workers write completed task files
│   ├── task_requests/          # Orchestrator writes new task briefs
│   │   └── consumed/          # Workers archive read briefs
│   ├── in_progress/           # Orchestrator claims tasks during processing
│   └── resolved/              # Processed with ## Resolution appended
```

## Coordination Flow (Multi-Profile)

```
1. User request → orchestrator
2. Orchestrator runs Triage Checklist (client→memory→SearXNG→profile→delegate)
3. Orchestrator writes task brief → task_requests/task_<uuid>.md
4. Worker polls task_requests/, consumes brief → consumed/
5. Worker executes, writes output → inbox/task_<uuid>.md
6. Orchestrator processes inbox:
   - error_state → diagnose, apply fix_hint, verify
   - other → validate, store to Supermemory, archive
7. Orchestrator appends ## Resolution
8. Orchestrator moves file → resolved/
```

## Supermemory Routing (Multi-Client + Multi-Profile)

Container tag format: `{active_client}_{domain}`

- `{active_client}` from `/data/workspace/active_client.yaml`
- `{domain}` from `/data/workspace/profiles.yaml` for the target profile

Examples: `mobilemd_research`, `west_shore_chamber_architecture`, `voltaic_orchestration`

The `supermemory.json` `custom_containers` must list ALL client×domain combos
for the governed plugin to allow them. Generate programmatically:

```python
clients = ['voltaic', 'mobilemd', 'west_shore_chamber']
domains = ['orchestration', 'research', 'architecture']
containers = [f'{c}_{d}' for c in clients for d in domains]
```

When adding a new client or profile, update: profiles.yaml + clients.yaml +
supermemory.json custom_containers.

## Resolution Block

Appended by orchestrator before moving to resolved/:

```markdown
## Resolution
- **resolved_at:** `<ISO 8601 timestamp>`
- **action_taken:** `<concrete description>`
- **verification:** `<how fix was confirmed>`
- **permanent_fix:** `<if applicable>`
```

## Backward Compatibility

Older task files using `assignee: researcher` with `task_type: research|scrape|competitive_analysis|social_media|authenticated` remain valid. The orchestrator maps legacy fields to the new `assignee_profile` + `assignee_domain` format using the routing matrix.

## Error Type → Fix Map

| error_type | Fix |
|---|---|
| `auth_gate` | Refresh cookies at `/data/camofox/cookies/<platform>_<account>.json` |
| `rate_limit` | Reduce concurrency, wait 60s, rotate proxy |
| `connection_error` | Restart Camofox service |
| `ssl_error` | Check cert chain, rotate proxy, retry with `skipTlsVerification: true` |
| `parse_fail` | Review x-ref mappings against current page structure |
| `model_error` | Swap model provider or reduce reasoning effort |
| `tool_unavailable` | Check MCP server health, restart if needed |
