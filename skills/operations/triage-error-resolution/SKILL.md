---
name: triage-error-resolution
description: "Process task files (error states, research findings, scraped data, analysis, reports, code reviews, architecture decisions, bug analyses) dropped by worker profiles into the multi-profile triage inbox"
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

The triage system handles ALL task types from worker profiles (researcher,
code_architect, future: design, social_media, seo) — not just errors.
Files are markdown (`.md`) with YAML frontmatter, written to a shared inbox on the
`/data` volume. The orchestrator (default profile) processes files directly; an
optional cron job (`triage-inbox-watcher`, currently paused) is available for
background polling.

## Workflow

1. **Scan inbox**: `search_files(target="files", pattern="task_*.md", path="/data/workspace/triage/inbox/")`.
2. **Read + parse** each against `/data/workspace/triage/.task-format.md` — extract
   `output_type`, `status`, `severity`, `approval_gates` from frontmatter.
3. **Move to in_progress**: move file from `inbox/` to `in_progress/`.
4. **Act based on output_type** (from `/data/workspace/triage/.task-format.md`):
   - `error_state` — diagnose from `error_type`, `step`, `fix_hint`. Apply fix per resolution map.
   - `research_findings` — extract insights, determine if follow-up tasks or reports are needed.
   - `scraped_data` — process data, route to downstream systems.
   - `analysis` — review conclusions, validate, determine next steps.
   - `report` — archive relevant parts to Supermemory, flag urgent items.
   - `code_review` — review findings, delegate implementation if needed.
   - `architecture_decision` — record decision, check for cross-profile impact.
   - `bug_analysis` — verify root cause, delegate fix to code_architect if applicable.
5. **Check approval_gates before delegating further**:
   - `none` (default) → auto-delegate to next profile without asking operator.
   - `each_step` → use `clarify` to confirm before passing to next profile.
   - `output_only` → surface output to operator, do NOT delegate further.
6. **Verify** the fix (re-run the failing step or check service health).
7. **Append `## Resolution`** section to the markdown file and move to `resolved/`.
8. **Update memory** if a recurring pattern emerges.
9. **[SILENT]** if inbox is empty.

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

### Worker Profile Consumption Ordering
When a worker profile's AGENTS.md has a "Task Request Polling" section, the **consumption step (move brief to `consumed/`) MUST come BEFORE any domain/routing logic that could skip it**. If Domain Research Mode matching or domain filtering is placed before consumption, tasks with non-matching domains (e.g., `assignee_domain: social` routed to researcher) will be executed but their briefs will never be moved — causing indefinite accumulation in `task_requests/`. **Fix:** step 1 = consume, step 2 = route/filter. This applies to all worker profiles (researcher, code_architect, social_media, design, seo).

### Inbox Is a Transit Folder, Not Storage
The inbox MUST be empty after orchestrator processing. Process files on every turn, append `## Resolution`, and move to `resolved/` immediately. Files should not sit in inbox for more than 24 hours. If you discover stale inbox files (>24h old), flag it as a pipeline failure — either the orchestrator isn't processing or the triage-inbox-watcher cron is disabled.

### Web Research Tool Failures
When primary web research tools (Firecrawl MCP) fail with auth errors or become
unreachable, do NOT block — pivot to built-in `web_search` + `web_extract`.
See `references/web-research-tool-fallback.md` for the full priority order and
fallback workflow.

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

| Directory | Who writes | Who reads | Purpose |
|---|---|---|---|
| `task_requests/` | Orchestrator | Worker profiles | New task briefs with full context |
| `task_requests/consumed/` | Worker profiles | Orchestrator | Archive of consumed briefs |
| `inbox/` | Worker profiles | Orchestrator | Completed task files |
| `in_progress/` | Orchestrator | Orchestrator | Files currently being processed |
| `resolved/` | Orchestrator | Orchestrator | Processed files (30-day retention) |
| `archive/` | Orchestrator | Orchestrator | Files >30 days old |

## Retention

- `inbox/`: clean immediately after pickup
- `in_progress/`: clean after resolution
- `resolved/`: keep 30 days, then move to `archive/`
- `archive/`: long-term record

## File Accumulation Prevention

See `references/triage-accumulation-diagnostic.md` for the full diagnostic checklist,
root cause analysis, and cleanup procedure when files pile up in `task_requests/` or `inbox/`.

Key rules:
- **Consume before route:** Worker profiles MUST move briefs to `consumed/` BEFORE any domain matching logic.
- **Inbox is transit:** Process and move to `resolved/` on every turn. Files >24h old = pipeline failure.
- **Cron health:** The `triage-inbox-watcher` cron should be enabled. If `last_run_at: null`, it never ran.

## Automation

A cron job (`triage-inbox-watcher`, ID `81d45347e648`) is available for background
polling of `/data/workspace/triage/inbox/` every 5 minutes. Currently **paused**
(the operator controls when to enable it). The orchestrator processes files
directly in interactive sessions regardless of cron state. See
`references/triage-cron-watcher.md` for the cron prompt.

## Profile AGENTS.md Template

Add these sections to any worker profile's AGENTS.md:

### Task Request Polling (MANDATORY — Worker Profiles Only)

```
# Task Request Polling (Before Step 1)

On session start, check `/data/workspace/triage/task_requests/` for `task_*.md`
files with `assignee_profile: <this_profile_name>`.
If found:
1. Read the task brief (YAML frontmatter + body).
2. Extract: goal, scope, constraints, target URLs, output format.
3. Move consumed brief to `/data/workspace/triage/task_requests/consumed/`.
4. Proceed to execution.
If no task requests: proceed directly.
```

**Without this section, the profile never picks up work and task briefs pile up
indefinitely in `task_requests/`.** The `code_architect` profile was created without
it — this is a known gap that must be fixed.

### Task Output Protocol

```
# Task Output Protocol

When work completes or an unrecoverable error halts execution:

1. **Generate** a UUIDv4 for task_id.
2. **Write** a markdown task file per `/data/workspace/triage/.task-format.md`
   into `/data/workspace/triage/inbox/task_<uuid>.md`.
   - Include all required frontmatter fields (task_id, profile, timestamp, status, output_type).
   - For error states: also include error_type, severity, step, blocking_url, fix_hint.
   - Body: free-form markdown with findings, sources, evidence, caveats.
3. **Halt.** Do not retry, do not speculate.

The orchestrator (default profile) processes the inbox.
```

## Architecture Decision

One mechanism for everything. The triage folder is the universal task handoff inbox.
Markdown files (not JSON). No separate `tasks/` directory. The old `.schema.json`
(JSON error-state schema) is deprecated and archived at `archive/.schema.json.v1-deprecated`.

See `references/task-dispatch-generalization.md` for the migration rationale
and the full markdown task output format specification.
