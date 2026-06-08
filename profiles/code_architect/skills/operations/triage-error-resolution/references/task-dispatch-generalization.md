# Task Dispatch Generalization — Architecture Decision

**Decision:** One mechanism for everything. Collapse the proposed `tasks/` directory
into the existing `triage/` folder. Use markdown files with YAML frontmatter, not JSON.

## Why

The triage error-state pattern was a special case of a general task inbox. Rather
than maintain two parallel inboxes (one for errors, one for everything else), the
single `triage/` folder now handles all output types:

| `output_type`      | Handled by |
|--------------------|-----------|
| `error_state`      | Resolution map (auth, rate limit, parse, connection, timeout, SSL, model, tool) |
| `research_findings`| Extract insights → determine follow-up tasks or reports |
| `scraped_data`     | Process → route to downstream systems |
| `analysis`         | Review conclusions → validate → determine next steps |
| `report`           | Archive to Supermemory → flag urgent items |

## Format Migration

| Aspect | Old (JSON) | New (Markdown) |
|--------|-----------|----------------|
| File extension | `.json` | `.md` |
| Schema | `.schema.json` (JSON Schema) | `.task-format.md` (spec document) |
| Filename | `error_state_<uuid>.json` | `task_<uuid>.md` |
| Resolution | `_resolution` JSON block | `## Resolution` markdown section |
| Validation | Machine-enforced schema | Human-readable format spec |

## Directory Layout

```
/data/workspace/triage/
├── inbox/                  ← Worker profiles write task_<uuid>.md here
├── in_progress/            ← Orchestrator moves files here while processing
├── resolved/               ← Processed files (30-day retention)
├── archive/                ← Files >30 days old
├── .task-format.md         ← Markdown format specification
├── README.md               ← System overview and profile author instructions
└── archive/.schema.json.v1-deprecated  ← Legacy JSON schema (archived)
```

## Task File Format (`.task-format.md`)

YAML frontmatter + markdown body. See the live file at `/data/workspace/triage/.task-format.md`
for the authoritative spec.

### Required Frontmatter

```yaml
task_id: "uuidv4"
profile: "researcher"
timestamp: "ISO8601"
status: complete|partial|failed
output_type: research_findings|error_state|scraped_data|analysis|report
```

### Error State Additions

```yaml
error_type: auth_gate|rate_limit|parse_fail|connection_error|timeout|ssl_error|model_error|tool_unavailable|unknown
severity: blocking|degraded|warning|info
step: "1|2|3a|3b|C|D"
blocking_url: "url or null"
fix_hint: "what might fix it"
```

### Resolution Section (Appended by Orchestrator)

```markdown
## Resolution

- **Resolved at:** ISO8601
- **Action taken:** what was done
- **Verification:** how we know it worked
- **Permanent fix:** what prevents recurrence (if applicable)
```

## Orchestrator Cron

A cron job (`triage-inbox-watcher`, every 5m) polls the inbox automatically.
See `references/triage-cron-watcher.md` for the full cron prompt and setup.