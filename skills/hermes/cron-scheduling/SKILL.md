---
name: cron-scheduling
description: Schedule and manage Hermes cron jobs correctly — timezone handling, time computation, delivery verification, and debugging failed executions.
tags: [cron, scheduling, timezone, automation]
triggers:
  - User asks to schedule, create, or set up a cron job
  - User asks about timezones, scheduled tasks, or recurring automation
  - Anything involving `cronjob` action=create or action=edit with a schedule
---

# Cron Scheduling

Schedule Hermes cron jobs with correct time computation, timezone awareness, and delivery verification.

## Critical Rules

### 1. NEVER Guess Timezones — Always Use `date`

**Before setting any schedule, run a terminal command to get the current UTC time:**

```bash
date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ"
```

This single command:
- Gets the actual server time (ground truth, not guesswork)
- Computes the offset (e.g., +5 minutes)
- Formats it as ISO 8601 UTC (what `cronjob` expects)

**Never hand-compute UTC from a local time.** The server runs in UTC; local timezone offsets vary with daylight savings and are easy to get wrong.

### 2. EDT vs EST — Check the Season

The user is in the US Eastern timezone. The offset from UTC changes with daylight savings:

| Period | Abbreviation | UTC Offset |
|--------|-------------|------------|
| Nov – Mar | EST (Eastern Standard) | UTC-5 |
| Mar – Nov | EDT (Eastern Daylight) | UTC+4 hours ahead of EDT |

**To verify which is active:**
```bash
TZ="America/New_York" date +"%Z"
# Returns "EDT" or "EST"
```

**Pitfall:** Assuming EST (UTC-5) year-round. During March–November it's EDT (UTC-4). Getting this wrong means the job runs 1 hour late or early.

### 3. Set Future Times, Not Current Times

When the user says "5 minutes from now":
1. `date -u` to get current UTC
2. Add the delta
3. Set the schedule to the **future** time

**Pitfall:** Setting the schedule to the current time instead of current + delta. Double-check the computed time is actually in the future.

### 4. Verify Execution — Don't Trust `last_run_at: null`

After a cron job should have fired:

1. **Check `cronjob list`** — look at `last_run_at` and `last_status`
2. **If `last_run_at` is still null** after the scheduled time has passed, the job didn't fire
3. **Force-run with `cronjob run`** — but verify the force-run actually executed (check `last_run_at` updates)
4. **Check the expected output** — e.g., if the job creates a file, verify the file exists

### 5. Gateway Must Be Running — The #1 Reason Jobs Don't Fire

The cron scheduler does NOT run as a standalone process. The gateway calls `scheduler.tick()` every 60 seconds from a background thread. **No gateway = no job execution**, regardless of what `cronjob list` shows.

**Diagnose immediately when jobs don't fire:**
```bash
# Check gateway status
hermes cron status
# Output if gateway is down: "✗ Gateway is not running — cron jobs will NOT fire"

# Verify no gateway process exists
ps aux | grep -i gateway | grep -v grep
```

**Fix options (pick one):**
1. **Enable the gateway** — set `START_GATEWAY=true` in Railway env vars, redeploy. The entrypoint starts the gateway which then calls `tick()` every 60s.
2. **System crontab** — add `* * * * * /opt/hermes/.venv/bin/hermes cron tick` to run ticks without the full gateway.
3. **Background loop** — a long-running process that calls `hermes cron tick` every 60 seconds.

**Architecture note:** Neither the web UI (`server.py`) nor the admin API (`admin.app` on port 8080) trigger scheduler ticks. The `cronjob` tool only writes to `/data/cron/jobs.json` — it does not execute anything. The `cronjob run` action updates `next_run_at` but also depends on the gateway to actually process it on the next tick.

**Also check:** `hermes cron list` (CLI) may show "No scheduled jobs" even when jobs exist in `/data/cron/jobs.json`. This is a profile path mismatch — the CLI's `HERMES_HOME` may differ from the web UI's. Always check the actual file when debugging.

### 6. Script Parameter = File Path, NOT Inline Code

The `script` field in `cronjob action=create` expects a **filename relative to `/data/scripts/`**, not inline bash content.

**Wrong:** `script: "#!/bin/bash\necho hello"` → gateway interprets the whole string as a path: `Script not found: /data/scripts/#!/bin/bash...`

**Correct:**
1. Create the script file: `write_file(path="/data/scripts/my_job.sh", content="#!/bin/bash\necho hello")`
2. Reference by name: `cronjob action=create, script="my_job.sh"`

The gateway's `_run_job_script()` prepends `/data/scripts/` to the script value and executes it.

### 7. `deliver=origin` Fails Silently Without a Connected Platform

When no messaging platform (Telegram, Discord, Slack, etc.) is connected, `deliver=origin` produces:
```
WARNING cron.scheduler: Job '<id>': no delivery target resolved for deliver=origin
```
The job is removed from jobs.json without executing. **Use `deliver=local` until a messaging platform is configured.**

### 8. Removing Platform Config Stops Gateway Retry Spam

If the gateway retries an unconfigured platform (e.g., Discord with no bot token), it logs errors every 60 seconds and eventually pauses after 10 failures. To stop this:

```bash
# Remove the platform section from all config files
/opt/hermes/.venv/bin/python3 -c "
import yaml
for path in ['/data/config.yaml', '/data/profiles/researcher/config.yaml', '/data/profiles/code_architect/config.yaml']:
    with open(path) as f:
        cfg = yaml.safe_load(f)
    if 'discord' in cfg:
        del cfg['discord']
    with open(path, 'w') as f:
        yaml.dump(cfg, f, sort_keys=False, default_flow_style=False)
"
```

**Gateway config changes require a restart** to take effect:
```bash
hermes gateway restart
```

### 9. Set Timezone for All Profiles

The `timezone` key in config.yaml controls how Hermes displays times. Set it to the user's timezone across all profiles:

```bash
hermes config set timezone America/New_York  # default profile
HERMES_HOME=/data/profiles/researcher hermes config set timezone America/New_York
HERMES_HOME=/data/profiles/code_architect hermes config set timezone America/New_York
```

**Pitfall:** `patch` tool is blocked on protected config files (`/data/config.yaml`). Use `hermes config set` instead. For profile configs, `patch` may also be blocked by security guards — fall back to `hermes config set` with `HERMES_HOME` override.

## Patterns

### One-Shot Test Job (Recommended Template)
```bash
# Step 1: Get the correct future time
date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ"
# Output: 2026-06-05T23:52:00Z

# Step 2: Create the job with the computed time
# cronjob action=create, schedule=<output from step 1>, repeat=1, no_agent=true
```

### Recurring Job
```bash
# schedule="every 5m", repeat="forever"
```

### Delivery Options
- `deliver: "origin"` — sends result back to the chat where it was created
- `deliver: "local"` — stores locally (useful for debugging)
- `no_agent: true` — runs script directly, no LLM invocation (cheaper, faster for bash-only jobs)

## Quick Reference

| Field | Notes |
|---|---|
| `schedule` | ISO 8601 UTC for once, `"every Nm"` for recurring |
| `repeat` | `1` for once, `"forever"` for recurring |
| `no_agent` | `true` = script-only, no LLM |
| `deliver` | `"origin"` or `"local"` |
| `workdir` | Defaults to session working dir |
| `profile` | Which Hermes profile to run as |
