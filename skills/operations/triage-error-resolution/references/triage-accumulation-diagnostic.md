# Triage File Accumulation — Diagnostic & Fix Pattern

## Symptoms
- Files piling up in `task_requests/` (unconsumed)
- Files sitting in `inbox/` for days without being resolved
- `task_requests/consumed/` is empty or stale

## Root Cause Checklist

### 1. Worker Profile Missing Task Request Polling Section
**Symptom:** Briefs with `assignee_profile: <profile>` sit in `task_requests/` indefinitely.
**Diagnosis:** Check the profile's AGENTS.md for a "Task Request Polling" section.
**Fix:** Add the polling section (see template in SKILL.md § "Profile AGENTS.md Template").

### 2. Consumption Step Placed After Domain Routing
**Symptom:** Briefs consumed for some domains but not others (e.g., `social` domain briefs left behind).
**Diagnosis:** In the worker's polling section, check if "Move to `consumed/`" comes AFTER domain-specific logic.
**Fix:** Reorder — consumption (step 3) MUST come BEFORE Domain Research Mode matching (step 4).

### 3. Inbox Not Being Processed
**Symptom:** Completed task results sit in `inbox/` with no `## Resolution` appended.
**Diagnosis:** Check if the orchestrator is processing inbox on every turn. Check if `triage-inbox-watcher` cron is enabled.
**Fix:** Process inbox files immediately. Append `## Resolution` and move to `resolved/`. Enable the cron for background polling.

### 4. Cron Job Never Ran
**Symptom:** `last_run_at: null` on the `triage-inbox-watcher` cron.
**Diagnosis:** `cronjob(action='list')` → check `last_run_at` and `enabled` fields.
**Fix:** Enable the cron, or process inbox manually in interactive sessions.

## Cleanup Procedure

When files have already accumulated:

```bash
# 1. Identify stale briefs (check assignee_profile vs assignee_domain)
find /data/workspace/triage/task_requests -maxdepth 1 -name "*.md" ! -path "*/consumed/*"

# 2. For each stale brief: if the task is already complete (result exists in inbox/),
#    move the brief to consumed/ — do NOT re-execute
mv /data/workspace/triage/task_requests/task_<uuid>.md /data/workspace/triage/task_requests/consumed/

# 3. Process inbox backlog: read each file, append ## Resolution, move to resolved/
#    (per output_type handling in the Inbox Processing Protocol)

# 4. Verify clean state
find /data/workspace/triage/inbox -type f        # should be empty
find /data/workspace/triage/task_requests -maxdepth 1 -name "*.md" ! -path "*/consumed/*"  # should be empty
```

## Prevention
- Every new worker profile MUST include the Task Request Polling section (consume-before-route ordering).
- The orchestrator MUST process inbox on every turn — inbox is a transit folder, not storage.
- The `triage-inbox-watcher` cron should be enabled for background polling (every 5m).
