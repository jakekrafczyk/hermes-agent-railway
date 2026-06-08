# Token Compression Patterns

Concrete techniques for shrinking doctrine files without losing behavioral
information. Every byte in SOUL.md and AGENTS.md costs tokens every turn —
these patterns claw back 10-20% with zero behavioral change.

## 1. Table-ify Sub-agent / Worker Lists

**Before:** 5 workers × 7 lines each = 35 lines of bullet-point definitions.
```markdown
### code-reviewer
- **Role:** leaf
- **Toolsets:** [terminal, file, search, web]
- **Trigger:** PR review, diff analysis, pre-merge gate
- **Context contract:** Full file paths, unified diff, PR description, target branch
- **Output:** Structured review with severity-tagged findings
```

**After:** 5 workers in one 6-line table (header + data rows).
```markdown
| Agent | Trigger | Toolsets | Context Contract | Output |
|---|---|---|---|---|
| **code-reviewer** | PR review, diff analysis, pre-merge | terminal, file, search, web | File paths, unified diff, PR desc, target branch | Severity-tagged findings |
```

**Savings:** ~25 lines per 5-aggregate. Drop the "Role: leaf" column if all workers
are leaf-only — that's architectural context, not per-agent data.

## 2. ASCII Art → Compact Text Flow

**Before:** 24 lines of box-drawing characters for a pipeline diagram.
```text
┌─────────────────┐     task_requests/     ┌──────────────────┐
│  DEFAULT        │ ──────────────────────▶│  RESEARCHER      │
│  (orchestrator) │                        │  (worker)        │
...
```

**After:** 2 lines of directional text.
```text
default (orchestrator) → task_requests/ → researcher (worker) → inbox/ → orchestrator
  → resolves errors OR delegates → code_architect → implements → resolved/
```

Follow the flow with a single prose paragraph for details that need precision.

**Savings:** ~22 lines per diagram. ASCII boxes cost 10x their information content.

## 3. Enforce Bright-Line Rule on "Current State"

SOUL.md §6 says: memory for environmental facts, profile files for behavioral
rules. The heuristic is "if the sentence contains 'should' or 'must,' it goes
in a profile file, not memory."

The reverse trap: profile files accumulate transient facts masquerading as
state. Watch for:

- **Historical play-by-play:** "CRITICAL DISCOVERY (2026-05-29): ...", "FIXED: ...", "Takes effect on next session." These are session logs, not doctrine. They age into dead weight.
- **Stale counts:** "0 memories stored — confirmed 2026-05-29." This will be wrong in 24 hours.
- **Migration notes:** "Copied /data/supermemory.json → ..." Already done. Never needs repeating.

**Fix:** Replace a 12-line verbose Current State block with 5 dense single-line
facts. Move the historical detail to the memory tool where it's queryable but
doesn't burn tokens every turn.

**Before (12 lines, ~700 chars):**
```markdown
## Current State
- container is **empty** (0 memories stored) — confirmed 2026-05-29
- Multi-container mode **enabled** — `voltaic_code_architect` is now an allowed tag...
- **CRITICAL DISCOVERY (2026-05-29):** ... (multi-paragraph debug narrative)
- **FIXED:** Copied ... Also switched ...
- **Takes effect on next session.** ...
```

**After (5 lines, ~250 chars):**
```markdown
## Current State
- Primary container: `voltaic_code_architect` (env override over supermemory.json)
- Multi-container ON: custom_containers=[voltaic_code_architect], caps: 3 results, 3 calls/turn
- auto_recall=false (intentional — 40k token burn prevention)
- Built-in `memory` tool → primary container only; explicit supermemory_store for secondary
- Zero-token index: AGENTS.md Codebase Map — 48 verified paths, sub-profile execution verified (2026-05-29)
```

## 4. Inline Comments in Code Blocks

**Before:** Multi-line comments above each command in a code fence.
```bash
# Read a specific config key to confirm it parsed
HERMES_HOME=/data/profiles/researcher /opt/hermes/.venv/bin/hermes config get model.default

# Check required env vars exist (can't read_file .env directly)
grep -c "..." /data/profiles/researcher/.env
# Expected: 3 (all required keys present)

# Check memory provider status
HERMES_HOME=/data/profiles/researcher /opt/hermes/.venv/bin/hermes memory status
```

**After:** One group comment + inline `# expect 3` on the relevant line.
```bash
# Verify config + env + memory health
HERMES_HOME=/data/profiles/researcher /opt/hermes/.venv/bin/hermes config get model.default
grep -c "..." /data/profiles/researcher/.env  # expect 3
HERMES_HOME=/data/profiles/researcher /opt/hermes/.venv/bin/hermes memory status
```

**Savings:** ~6 lines and ~150 chars per code block. Group related verification
steps under one comment rather than one-per-step.

## 5. Routing Rules in One Line

Long "MATRIX ROUTING" sections with 7 numbered rules can compress to a single
sentence when the logic is mechanical (not judgment-based):

**Before (10 lines):**
```markdown
1. You operate in a multi-tenant agency environment...
2. Before invoking any Supermemory tool, you MUST read /data/workspace/active_client.yaml...
3. Identify your current profile domain...
4. Compose the container_tag parameter as: container_tag: "{active_client}_{active_domain}"
5. NEVER execute a memory tool query with a blank or global container_tag...
6. Apply this to all four Supermemory tool calls...
7. Before storing research findings...
```

**After (2 lines):**
```markdown
Before ANY supermemory tool: read /data/workspace/active_client.yaml → compose
container_tag as {client}_{domain}. NEVER use blank/global tag. Applies to all
four ops: search, store, forget, profile.
```

## 6. Template Templates — Remove Scaffolding

Review output formats, task templates, and other "fill in the blank" sections
often include scaffold comments and empty sections that add lines without information.

**Before (11 lines):**
```markdown
## Review: <module/path>
**Severity breakdown:** 🔴0 🟠0 🟡0 🟢0 ⚪0

### 🔴 CRITICAL
- **<file>:<line>** — <finding>
  Fix: <concrete suggestion>

### 🟠 HIGH
...

## Summary
<1-2 sentence verdict + recommended action>
```

**After (4 lines):**
```markdown
## Review: <module> | 🔴0 🟠0 🟡0 🟢0 ⚪0
- **<file>:<line>** — <finding> (🔴/🟠/🟡/🟢/⚪) → Fix: <suggestion>
## Summary: <1-2 sentence verdict>
```

The agent knows what a severity level is — the `### 🔴 CRITICAL` headers and
empty `### 🟠 HIGH` sections are documentation, not instructions. Drop them.

## Measurement: Always Show the Scorecard

Every compression pass should end with a before/after table. It gives the user
visibility into the trade-off and builds trust that the compression was surgical:

```markdown
| File | Before | After | Δ Lines | Δ Bytes |
|---|---|---|---|---|
| SOUL.md | 264 lines / 14,391 B | 253 lines / 12,865 B | -11 | -1,526 |
| AGENTS.md | 194 lines / 10,983 B | 119 lines / 7,680 B | -75 | -3,303 |
| MEMORY.md | 10 lines / 1,939 B | 10 lines / 1,605 B | 0 | -334 |
| **TOTAL** | **468 lines / 27,313 B** | **382 lines / 22,150 B** | **-86 (-18.4%)** | **-5,163 (-18.9%)** |
```

## Priority Order for Compression

When time or scope is limited, attack in this order (highest ROI first):

1. **ASCII art → text** — always >10 lines saved per diagram, zero info loss
2. **Sub-agent/worker lists → tables** — 5+ lines per entity
3. **Current State historical cruft** — transient facts masquerading as doctrine
4. **Verbose routing rules → one-liners** — mechanical logic doesn't need prose
5. **Code comment compression** — small wins, but zero-risk
6. **Template scaffolding** — small wins, very context-dependent
