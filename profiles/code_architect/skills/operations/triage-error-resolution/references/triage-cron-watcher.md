# Triage Inbox Watcher — Cron Job

**Job ID:** `81d45347e648`
**Name:** `triage-inbox-watcher`
**Schedule:** every 5 minutes
**Workdir:** `/data/workspace`
**Deliver:** local (no delivery on silent runs)

## Cron Prompt

```
TASK: Process the file-based task inbox.

CONTEXT:
- Worker profiles write markdown task files to /data/workspace/triage/inbox/
- Files are named task_<uuid>.md with YAML frontmatter
- Your job: process each file, take action based on output_type, append resolution, move to resolved/
- The task format is documented at /data/workspace/triage/.task-format.md

PROCEDURE:
1. List files in /data/workspace/triage/inbox/*.md
2. If none, respond with "[SILENT]" and exit.
3. For each file:
   a. Move it from inbox/ to in_progress/ (rename/mv)
   b. Read the file — parse frontmatter for output_type, status, severity
   c. Act based on output_type:
      - research_findings: read the findings, extract actionable insights,
        determine if a response, follow-up task, or report is needed
      - error_state: diagnose the error using context + fix_hint,
        take corrective action (cookie refresh, config patch, service restart, etc.)
      - scraped_data: process the data, feed into appropriate downstream system
      - analysis: review conclusions, validate, determine next steps
      - report: read, archive relevant parts to supermemory, flag anything urgent
   d. Append a "## Resolution" section to the file documenting what you did
   e. Move the file from in_progress/ to resolved/
4. If any blocking errors were resolved, consider whether the researcher profile
   can resume and notify the operator via final response summary.
```

## Setup Command

```bash
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes cronjob create \
  --name triage-inbox-watcher \
  --schedule "every 5m" \
  --workdir /data/workspace \
  --prompt-file /data/workspace/triage/cron-prompt.txt
```

Or via the cronjob tool with the prompt inline.

## Verification

```bash
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes cronjob list
# Expected: triage-inbox-watcher, state=scheduled, enabled=true, schedule=every 5m
```

## Retention Logic (future enhancement)

Move files from `resolved/` to `archive/` after 30 days. Not yet automated —
the current cron only processes `inbox/`. Add to a future version.