---
name: triage-error-resolution
description: "Process task files (error states, research findings, scraped data, analysis, reports) dropped by worker profiles into the universal Voltaic triage inbox"
triggers:
  - "check triage"
  - "fix errors"
  - "triage inbox"
  - "task inbox"
  - "check inbox"
  - "worker error"
  - "profile error"
  - "process inbox"
  - "inbox watcher"
---

# Triage Task Processing

The triage system handles ALL task types from worker profiles — not just errors.
Files are markdown (`.md`) with YAML frontmatter, written to a shared inbox on the
`/data` volume. An orchestrator cron job polls every 5 minutes.

## Workflow

1. **Scan inbox**: `ls /data/workspace/triage/inbox/` — look for `task_*.md` files.
2. **Read + parse** each against `/data/workspace/triage/.task-format.md` — extract
   `output_type`, `status`, `severity` from frontmatter.
3. **Move to in_progress**: `mv /data/workspace/triage/inbox/task_<uuid>.md /data/workspace/triage/in_progress/`
4. **Act based on output_type**:
   - `error_state` — diagnose from `error_type`, `step`, `fix_hint`. Apply fix per resolution map.
   - `research_findings` — extract insights, determine if follow-up tasks or reports are needed.
   - `scraped_data` — process data, route to downstream systems.
   - `analysis` — review conclusions, validate, determine next steps.
   - `report` — archive relevant parts to Supermemory, flag urgent items.
5. **Verify** the fix (re-run the failing step or check service health).
6. **Append `## Resolution`** section to the markdown file and move to `resolved/`.
7. **Update memory** if a recurring pattern emerges.
8. **[SILENT]** if inbox is empty.

## File Format

All files follow `/data/workspace/triage/.task-format.md`. Key points:
- **Markdown** (`.md`) with YAML frontmatter — not JSON
- Filename: `task_<uuid>.md` — UUID must match `task_id` in frontmatter
- Required frontmatter: `task_id`, `profile`, `timestamp`, `status`, `output_type`
- Error states additionally need: `error_type`, `severity`, `step`, `blocking_url`, `fix_hint`

## Resolution Map (Error States)

| error_type         | Action |
|--------------------|--------|
| auth_gate          | Refresh cookies: check `/data/camofox/cookies/` for the platform file, re-authenticate via VNC session. If no VNC, instruct user to refresh cookies and re-drop. |
| rate_limit         | Add 60s delay, check for proxy rotation. If persistent, reduce crawl concurrency in config. |
| parse_fail         | Re-check x-ref mappings in AGENTS.md extraction field mapping. Page structure may have changed — update the mapping and retry. |
| connection_error   | **(1) Check profile isolation first:** does the profile have its own `.env` and `config.yaml`? Is `CAMOFOX_URL` set? Profile configs don't inherit from main config. **(2)** Verify service health from the profile's perspective — use the actual service URL, not localhost (profiles may resolve differently). **(3)** Restart service if truly down. |
| timeout            | Reduce page complexity: add `mobile:true` to scrape options, reduce waitFor. If Camofox, check if page is too heavy. |
| ssl_error          | Ensure `skipTlsVerification:true` is set. If still failing, rotate proxy. |
| model_error        | Swap model provider in profile config. Check API key validity. |
| tool_unavailable   | **(1) Check profile isolation first** — profiles have their own `config.yaml` and `.env`. A tool unreachable from a profile may be healthy on the host. Check: `camofox.managed_persistence` is `true`, `user_id`/`session_key` are set, `CAMOFOX_URL` is in the profile's `.env`. **(2)** Verify service health with the correct URL. **(3)** Check MCP server health and config. Restart if needed. |
| unknown            | Full diagnostic: check logs at `/data/logs/errors.log`, check service health, review latest session. |

## Pitfalls

### Profile Isolation
Profiles run with `HERMES_HOME=<profile_dir>` — their own `config.yaml` and `.env` **do not inherit** from the main `/data/config.yaml` and `/data/.env`. A service running fine on the host (Camofox, SearXNG) will appear unreachable from a profile if the profile lacks its own config. Every new profile needs a bootstrap checklist → `references/profile-bootstrap.md`.

## Resolution Append Format (Markdown)

Appended by the orchestrator before moving to `resolved/`:

```markdown
## Resolution

- **Resolved at:** ISO8601
- **Action taken:** what was done
- **Verification:** how we know it worked
- **Permanent fix:** what prevents recurrence (if applicable)
```

## Directory Contract

| Directory      | Who writes          | Who reads          | Purpose                                  |
|----------------|---------------------|--------------------|------------------------------------------|
| `inbox/`       | Worker profiles     | Voltaic agent/cron | New markdown task files to process       |
| `in_progress/` | Voltaic agent/cron  | Voltaic agent/cron | Files currently being processed          |
| `resolved/`    | Voltaic agent/cron  | Voltaic agent/cron | Processed files (30-day retention)       |
| `archive/`     | Voltaic agent/cron  | Voltaic agent/cron | Files >30 days old (moved from resolved/)|

## Retention

- `inbox/`: clean immediately after pickup
- `in_progress/`: clean after resolution
- `resolved/`: keep 30 days, then move to `archive/`
- `archive/`: long-term record

## Automation

A cron job (`triage-inbox-watcher`) polls `/data/workspace/triage/inbox/` every 5 minutes
and executes this workflow automatically. The cron prompt is in `references/triage-cron-watcher.md`.

## Profile AGENTS.md Template

Add this section to any worker profile's AGENTS.md:

```
# Task Output Protocol

When research completes or an unrecoverable error halts execution:

1. **Generate** a UUIDv4 for task_id.
2. **Write** a markdown task file per `/data/workspace/triage/.task-format.md`
   into `/data/workspace/triage/inbox/task_<uuid>.md`.
   - Include all required frontmatter fields (task_id, profile, timestamp, status, output_type).
   - For error states: also include error_type, severity, step, blocking_url, fix_hint.
   - Body: free-form markdown with findings, sources, evidence, caveats.
3. **Halt.** Do not retry, do not speculate.

The Voltaic orchestrator cron job polls the inbox every 5 minutes.
```

## Architecture Decision

One mechanism for everything. The triage folder is the universal task handoff inbox.
Markdown files (not JSON). No separate `tasks/` directory. The old `.schema.json`
(JSON error-state schema) is deprecated and archived at `archive/.schema.json.v1-deprecated`.

See `references/task-dispatch-generalization.md` for the migration rationale
and the full markdown task output format specification.
