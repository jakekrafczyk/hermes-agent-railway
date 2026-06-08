# Cron & Gateway Debugging — Session Reference

## Architecture

The cron system has three components:
1. **Jobs store** — `/data/cron/jobs.json` (JSON, managed by `cron/jobs.py`)
2. **Scheduler** — `cron/scheduler.py` provides `tick()` which checks for due jobs and runs them
3. **Gateway ticker** — a daemon thread in the gateway process that calls `tick()` every 60 seconds

**Critical dependency:** The gateway MUST be running for cron jobs to execute. There is no standalone cron daemon — the ticker is embedded in `gateway/run.py::_start_cron_ticker()` (line 17719).

## Gotcha #1: `script` = File Path, NOT Inline Content

The `cronjob` tool accepts a `script` parameter. This is treated as a **file path relative to `/data/scripts/`**, NOT as inline bash content.

**What happens with inline content:**
```
script: "#!/bin/bash\necho hello"
```
Scheduler tries to execute: `/data/scripts/#!/bin/bash\necho hello`
Result: `Script not found: /data/scripts/#!/bin/bash`

**Correct pattern:**
1. Create the script file: `write_file("/data/scripts/my_job.sh", "#!/bin/bash\necho hello")`
2. Reference by name: `cronjob create ... script="my_job.sh"`

The scheduler's `_run_job_script()` joins `CRON_DIR.parent / "scripts" / script_path` and checks if the file exists.

## Gotcha #2: `deliver` Mode Matters for Execution

| Mode | Behavior | When to use |
|---|---|---|
| `origin` | Send result back to the chat that created the job | When a messaging platform (Telegram, Discord) is connected |
| `local` | Save output to `/data/cron/output/<job_id>/` only | When no messaging platform is connected |
| `none` | Fire and forget — no output saved | Script-only jobs with no output needed |

**Critical:** `deliver=origin` with no connected platform causes the job to be **wiped from `jobs.json` without executing**. The scheduler logs `no delivery target resolved for deliver=origin` and drops the job entirely — the script never runs.

**Fix:** Use `deliver=local` for all jobs until a messaging platform is configured.

## Gotcha #3: Gateway Won't Start Ticker Without Platform Config

The gateway starts the cron ticker regardless of whether platforms are connected. The log message `Gateway will continue for cron job execution` confirms this. However, the ticker only runs if the gateway process itself starts successfully (past the `runner.should_exit_cleanly` check at line 18157).

## Gotcha #4: Discord Retry Spam

If Discord is configured in `config.yaml` but no `DISCORD_BOT_TOKEN` is set, the gateway retries the Discord adapter every 60 seconds, filling the log with:
```
ERROR hermes_plugins.discord_platform.adapter: [Discord] No bot token configured
```
This is cosmetic — the cron ticker still runs. But it clutters diagnostics. Either add the token or remove the Discord config.

## Gotcha #5: CLI vs WebUI Job Visibility

`hermes cron list` (CLI) may show "No scheduled jobs" while the WebUI shows jobs. This is because:
- The CLI uses its own `HERMES_HOME` (may be `/data` or a profile path)
- The WebUI's `cronjob` tool writes to the active session's `HERMES_HOME`
- Both resolve to `get_hermes_home() / "cron" / "jobs.json"`

Check the actual file to confirm: the jobs.json path is always `$HERMES_HOME/cron/jobs.json`.

## Gotcha #6: Cron Output Location

Job execution output (stdout capture, script results) goes to:
```
/data/cron/output/<job_id>/<timestamp>.md
```
Each job ID gets its own subdirectory. Each run creates a timestamped `.md` file with the job metadata and script output.

The `write_file` side effects of scripts (e.g., creating `/data/workspace/output/cron_test.md`) happen in the normal filesystem — the cron output directory only captures stdout.

## Timezone Pitfall

When scheduling one-shot cron jobs for a specific local time:
1. Get both times: `date -u` (UTC) and `TZ="America/New_York" date` (local)
2. Compute the offset empirically (don't assume EST vs EDT)
3. Schedule in UTC: `schedule="YYYY-MM-DDTHH:MM:SSZ"`
4. Always compute FUTURE time: `date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ"`

**EDT (March-November):** UTC = local + 4 hours
**EST (November-March):** UTC = local + 5 hours

## Enable Gateway for Persistence

The gateway can be started manually (`nohup hermes gateway run --replace &`) but this dies on container restart. For persistent cron execution:

1. Set `START_GATEWAY=true` in Railway service environment variables
2. Redeploy — the entrypoint starts the gateway as a background process

## Quick Diagnostic Sequence

```bash
# 1. Is the gateway running?
ps aux | grep -i gateway | grep -v grep

# 2. Did the ticker start?
grep "Cron ticker started" /data/logs/gateway.log

# 3. Are there jobs?
cat /data/cron/jobs.json | python3 -m json.tool

# 4. Did jobs execute?
ls -la /data/cron/output/

# 5. Check for errors
grep -i "error\|warn\|deliver\|script.*not.*found" /data/logs/gateway.log | tail -20
```
