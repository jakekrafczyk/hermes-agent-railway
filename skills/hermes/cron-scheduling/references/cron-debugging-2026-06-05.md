# Cron Job Debugging — 2026-06-05 Session

## What Happened

Created a test cron job (`cron-file-write-test`) to write a file to `/data/workspace/output/cron_test.md` 5 minutes in the future.

**Mistake 1 — Wrong timezone offset:** Used EST (UTC-5) when it was actually EDT (UTC-4). The scheduled time was off by 1 hour.

**Mistake 2 — Current time, not future time:** Set the schedule to roughly the current time instead of adding 5 minutes.

**Mistake 3 — Job never fired:** After fixing the time and waiting past the scheduled time, the job showed:
- `state: "scheduled"` (not "completed" or "running")
- `last_run_at: null` (never executed)
- `last_status: null`

**Attempted fix — `cronjob run`:** Force-running the job updated `next_run_at` to the current time but did NOT actually execute (last_run_at remained null).

## Ground Truth Commands

```bash
# Get current UTC time + offset
date -u -d "+5 minutes" +"%Y-%m-%dT%H:%M:%SZ"

# Check which daylight savings is active
TZ="America/New_York" date +"%Z"

# Get both local and UTC for comparison
date -u && TZ="America/New_York" date
```

## Root Cause (Resolved)

**The gateway was not running.** The cron scheduler has no standalone process — the gateway calls `scheduler.tick()` every 60 seconds. Without the gateway, jobs are written to `/data/cron/jobs.json` but never executed.

Confirmed via:
```bash
hermes cron status
# → "✗ Gateway is not running — cron jobs will NOT fire"

ps aux | grep -i gateway | grep -v grep
# → no results (START_GATEWAY defaults to "false" in entrypoint.sh)
```

The entrypoint at `/opt/hermes-railway/entrypoint.sh` has:
```bash
if [ "${START_GATEWAY:-false}" = "true" ]; then
```
Default is `false`, so the gateway never starts on a fresh Railway deploy.

## Resolved Questions

1. **Why didn't the `no_agent=true` script job fire?** — No gateway running to call `scheduler.tick()`.
2. **Why did `cronjob run` not execute?** — It updates `next_run_at` in jobs.json but still needs the gateway's next tick to actually process it. With no gateway, no tick ever comes.
3. **Does `deliver: "origin"` require an active chat?** — Not the root cause. The job never reached the delivery stage because it never executed.
4. **Would `deliver: "local"` have worked?** — No, same root cause. The delivery mode is irrelevant when the scheduler itself isn't ticking.

## Key Architecture Insight

The cron execution chain is:
```
cronjob tool → writes to jobs.json → (gateway tick reads jobs.json) → scheduler.tick() → run_job() → deliver
```
If the gateway isn't running, the chain breaks at step 3 and nothing downstream happens. The `cronjob list` and `cronjob run` API calls only touch jobs.json — they don't trigger execution.

## User's Correction

> "currently it 11:47, so 4 hours ahead [of EST]" — user is aware of EDT vs EST distinction and expects correct handling.
