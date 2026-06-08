---
name: kanban
description: Multi-agent work queue and collaboration board for Hermes — the orchestrator playbook (decomposition, routing, anti-temptation rules) and the worker lifecycle (heartbeats, retries, handoff shapes, workspace handling).
version: 3.1.0
platforms: [linux, macos, windows]
environments: [kanban]
---

# Kanban — Orchestrator & Worker Guide

Hermes Kanban is a durable SQLite board for multi-profile / multi-worker collaboration. Two roles:

- **Orchestrator** — decomposes work, creates tasks, assigns to profiles, routes, does NOT execute
- **Worker** — spawned by the dispatcher, does the actual work, heartbeats, completes or blocks

The **core worker lifecycle** (6 steps: orient → work → heartbeat → block/complete) and the **"don't do the work yourself" rule** are auto-injected into every Kanban process via the `KANBAN_GUIDANCE` system-prompt block. This skill covers the deeper detail.

---

## Section 1: Orchestrator Playbook

### Profiles are user-configured — not a fixed roster

There is **no default specialist roster**. Before fanning out, discover what profiles exist:

```bash
hermes profile list
```

Or ask the user. Cache the result for the rest of the conversation.

### When to use the board (vs. just doing the work)

Create Kanban tasks when:
1. Multiple specialists are needed
2. Work should survive a crash or restart
3. User might want to interject (human-in-the-loop)
4. Multiple subtasks can run in parallel
5. Review / iteration is expected
6. The audit trail matters

If *none* of those apply → use `delegate_task` or answer directly.

### The Anti-Temptation Rules

- **Do not execute the work yourself.** Route, don't execute.
- **For any concrete task, create a Kanban task and assign it.** Every single time.
- **Split multi-lane requests before creating cards.** Extract independent workstreams.
- **Run independent lanes in parallel.** Link only true data dependencies.
- **Never create dependent work as independent ready cards.** Use `parents=[...]` on `kanban_create`.
- **If no specialist fits available profiles, ask the user.** Do not invent profile names.
- **Decompose, route, and summarize — that's the whole job.**

### Decomposition Process

**Step 1** — Understand the goal. Ask clarifying questions if ambiguous.

**Step 2** — Sketch the task graph. Extract lanes, map to profiles, decide parallel vs sequential.

**Step 3** — Create tasks with links:

```python
t1 = kanban_create(title="research: cost analysis", assignee="<profile-A>", body="...")["task_id"]
t2 = kanban_create(title="research: performance", assignee="<profile-A>")["task_id"]
t3 = kanban_create(title="synthesize recommendation", assignee="<profile-B>", parents=[t1, t2])["task_id"]
```

**Step 4** — Complete your own orchestrator task with summary.

**Step 5** — Report back to the user in plain prose.

### Common Patterns

| Pattern | Description |
|---------|-------------|
| **Fan-out + fan-in** | N research cards (no parents), one synthesis card (all as parents) |
| **Parallel + validation** | Implementer + explorer in parallel, reviewer depends on both |
| **Pipeline with gates** | Planner → Implementer → Reviewer (each `parents=[previous]`) |
| **Same-profile queue** | N tasks, same profile, no dependencies → dispatcher serializes |
| **Human-in-the-loop** | Task blocks. Operator unblocks with answer; worker respawns |

### Goal-Mode Cards (Persistent Workers)

For open-ended cards where one turn rarely finishes the job:

```python
kanban_create(title="Translate docs site to French", body="Acceptance: every page translated", assignee="<profile>", goal_mode=True, goal_max_turns=15)
```

### Recovering Stuck Workers

When a worker profile keeps crashing: Reclaim, Reassign, or change the profile's model.

See `references/known-profiles-and-patterns.md` for common orchestration task-graph examples.

---

## Section 2: Worker Lifecycle

### Workspace Handling

| Kind | What it is | How to work |
|------|------------|-------------|
| `scratch` | Fresh tmp dir, yours alone | Read/write freely; GC'd when task archived |
| `dir:<path>` | Shared persistent directory | Treat like long-lived state |
| `worktree` | Git worktree at resolved path | `git worktree add <path>` from main repo first |

### Tenant Isolation

If `$HERMES_TENANT` is set, prefix memory entries with the tenant.

### Good Handoff Shapes

**Coding task:**
```python
kanban_complete(summary="shipped rate limiter — 14 tests pass", metadata={
    "changed_files": ["rate_limiter.py"], "tests_passed": 14
})
```

**Review-required (block instead of complete):**
```python
kanban_comment(body="review-required handoff: ...")
kanban_block(reason="review-required: rate limiter needs eyes before merging")
```

**Research task:**
```python
kanban_complete(summary="3 libraries reviewed; vLLM wins", metadata={"recommendation": "vLLM"})
```

### Claiming Cards You Created

Pass `created_cards=[ids]` on `kanban_complete`. Only list ids from a successful `kanban_create` return value.

### Block Reasons That Get Answered Fast

Bad: `"stuck"` — no context.
Good: `"Rate limit key choice: IP or user_id?"` — specific decision needed.

Leave longer context as a `kanban_comment()` first.

### Heartbeats Worth Sending

Good: `"epoch 12/50, loss 0.31"`, `"scanned 1.2M/2.4M rows"`.
Bad: `"still working"`, empty notes. Every few minutes max.

### Retry Scenarios

Check `kanban_show` for prior `runs`. Don't repeat failed paths:

- `timed_out` — chunk or shorten work
- `crashed` — reduce memory footprint
- `spawn_failed` — profile config issue, block for human input
- `blocked` — unblock comment should be in thread

### Do NOT

- Call `delegate_task` as substitute for `kanban_create`
- Call `clarify` (runs headless — use `kanban_block` instead)
- Modify files outside `$HERMES_KANBAN_WORKSPACE`
- Complete a task you didn't actually finish

### Pitfalls

- Task state can change between dispatch and startup — always `kanban_show` first
- Workspace may have stale artifacts from previous runs
- Don't rely on `hermes kanban <verb>` CLI in containerized backends — use the tools

### CLI Fallback (for scripting)

- `kanban_show` ↔ `hermes kanban show <id> --json`
- `kanban_complete` ↔ `hermes kanban complete <id> --summary "..." --metadata '{}'`
- `kanban_block` ↔ `hermes kanban block <id> "reason"`
- `kanban_create` ↔ `hermes kanban create "title" --assignee <profile>`

### Notification Routing

Add to `~/.hermes/config.yaml`:
```yaml
notification_sources: ['*']  # accept subscriptions from all profiles
```
