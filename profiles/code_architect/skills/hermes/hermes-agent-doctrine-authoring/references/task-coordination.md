# Multi-Profile Task Coordination

Pattern for two Hermes profiles (orchestrator + worker) sharing a filesystem
and Supermemory container tag. Used in the Voltaic Marketing deployment
(default ↔ researcher).

## Filesystem Layout

```
/data/workspace/triage/
├── .task-format.md              # Format spec — canonical reference
├── inbox/                       # Worker writes completed/error task files
├── task_requests/               # Orchestrator writes new task briefs
│   └── consumed/                # Worker archives read briefs
└── resolved/                    # Orchestrator archives processed files
```

All task files are named `task_<uuid>.md` with YAML frontmatter + markdown body.

## Task File Frontmatter

### Universal Fields

| Field | Required | Type |
|-------|----------|------|
| `task_id` | Yes | UUIDv4 |
| `output_type` | Yes | `research_findings` \| `scraped_data` \| `analysis` \| `report` \| `error_state` |
| `status` | Yes | `complete` \| `partial` \| `failed` |
| `severity` | Yes | `info` \| `warning` \| `blocking` |
| `profile` | Yes | `researcher` (which worker wrote it) |
| `created_at` | Yes | ISO 8601 with timezone |
| `target_query` | Optional | Research query being executed |

### Error-Specific Fields (when `output_type: error_state`)

| Field | Required | Description |
|-------|----------|-------------|
| `error_type` | Yes | `auth_gate` \| `rate_limit` \| `parse_fail` \| `connection_error` \| `timeout` \| `ssl_error` \| `model_error` \| `tool_unavailable` |
| `step` | Yes | Which deterministic loop step failed |
| `retry_count` | Yes | Retries attempted before halting |
| `fix_hint` | Yes | Action the orchestrator should take |

### Error Type → Fix Map

| error_type | Fix |
|---|---|
| `auth_gate` | Refresh cookies at `/data/camofox/cookies/<platform>_<account>.json` |
| `rate_limit` | Reduce concurrency, wait 60s, rotate proxy |
| `connection_error` | Restart Camofox service |
| `ssl_error` | Check cert chain, rotate proxy, retry with `skipTlsVerification: true` |
| `parse_fail` | Review x-ref mappings against current page structure |
| `model_error` | Swap model provider or reduce reasoning effort |
| `tool_unavailable` | Check MCP server health, restart if needed |

### Example Error Task File

```markdown
---
task_id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
output_type: error_state
status: failed
severity: blocking
profile: researcher
created_at: '2026-05-22T14:30:00Z'
error_type: auth_gate
step: D
target_query: MobileMD LinkedIn company page profile data
retry_count: 1
fix_hint: Refresh LinkedIn cookies at /data/camofox/cookies/
---

## Error Context
LinkedIn returned login wall. Cookie file exists but appears expired.

## Evidence
- **type:** snapshot
- **summary:** Page shows "Sign in to view this page" with CAPTCHA prompt.

## Attempted Mitigations
1. Retried with same cookie file (1 attempt) — same result.
2. No further retries per Error Triage Protocol.
```

### Example Completed Task File

```markdown
---
task_id: c3d4e5f6-a7b8-9012-cdef-123456789012
output_type: research_findings
status: complete
severity: info
profile: researcher
created_at: '2026-05-22T15:00:00Z'
target_query: MobileMD at-home acute care competitive landscape
---

## Summary
Three competitors identified in the at-home acute care space in NE Ohio.
MobileMD's 70% ER wait reduction claim is their strongest differentiator.

## Steps Executed
1. SearXNG query: "at-home acute care Cleveland Ohio competitors"
2. Firecrawl v2: scraped top 3 results
3. No Camofox failover needed

## Findings
...

## Sources
- https://example.com/competitor-1 → supermemory:abc123
- https://example.com/competitor-2 → supermemory:def456
```

## Resolution Block (Appended by Orchestrator)

```markdown
## Resolution
- **resolved_at:** `<ISO 8601 timestamp>`
- **action_taken:** `<concrete description>`
- **verification:** `<how fix was confirmed>`
- **permanent_fix:** `<if applicable>`
```

## Task Request Format (Orchestrator → Worker)

Written to `/data/workspace/triage/task_requests/task_<uuid>.md`:

```yaml
---
task_id: <uuid>
assignee: researcher
created_at: '<ISO 8601>'
task_type: research | scrape | competitive_analysis | social_media | authenticated
priority: low | normal | high | urgent
deadline: '<ISO 8601>'   # optional
---
```

Body sections:
1. **Research goal** — one sentence
2. **Scope constraints** — what NOT to investigate
3. **Target sites/URLs** — if known
4. **Expected output format** — map to output_type
5. **Special instructions** — proxy, mobile, `maxAge: 0` for live data, etc.

## Coordination Flow

```
1. Orchestrator writes task brief  →  task_requests/task_<uuid>.md
2. Worker polls task_requests/ on session start
3. Worker moves consumed brief     →  task_requests/consumed/
4. Worker executes deterministic loop
5. Worker writes output            →  inbox/task_<uuid>.md
6. Orchestrator processes inbox file:
   - error_state  →  diagnose, apply fix_hint, verify
   - other        →  validate, store to Supermemory, archive
7. Orchestrator appends ## Resolution
8. Orchestrator moves file         →  resolved/
```

Both profiles share Supermemory container tag (`voltaic`) for audit trail.
Worker commits retrievals before writing task output. Orchestrator searches
Supermemory before creating new tasks to avoid redundant research.
