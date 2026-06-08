# Triage Inbox Watcher — Cron Job

**Job ID:** `81d45347e648`  
**Name:** `triage-inbox-watcher`  
**Schedule:** every 5 minutes  
**Workdir:** `/data/workspace`  
**Profile:** `default` (loads orchestrator AGENTS.md doctrine)  
**Deliver:** local (silent when inbox empty)

## Token-Efficient Prompt (393 chars)

The prompt is deliberately minimal — all processing procedure lives in the
orchestrator's AGENTS.md (Inbox Processing Protocol). The cron prompt only
says WHAT to do, not HOW. Before: 2,060 chars of duplicated procedure.
After: 393 chars (81% smaller). The orchestrator's AGENTS.md already defines
output_type handling, approval_gates routing, resolution format, and
error triage — the cron job inherits all of it.

```
Process the triage inbox per AGENTS.md Inbox Processing Protocol.
1. Check /data/workspace/triage/inbox/ for task_*.md files
2. If empty: respond "[SILENT]" and exit
3. For each file: move to in_progress/, read, process by output_type, append ## Resolution, move to resolved/
4. Follow .task-format.md for output_type handling and approval_gates
5. Summarize actions taken (1-2 lines per file)
```

## Token Efficiency Principle

When a cron job runs as a profile that already has comprehensive AGENTS.md
doctrine, the cron prompt should be a table of contents, not a textbook.
Every procedural detail in the prompt is dead weight — the profile's system
prompt already carries the full procedure. The cron prompt only needs:
1. WHAT to check (inbox path, file pattern)
2. The silence rule (empty = [SILENT])
3. Output contract (summary format)
4. Reference to the authoritative doctrine file (".task-format.md" or "AGENTS.md")

## Setup

Via cronjob tool: `cronjob(action='update', job_id='81d45347e648', profile='default', ...)`  
The `profile` field is critical — it loads the orchestrator's AGENTS.md into
the cron session's system prompt, which carries the full Inbox Processing Protocol.