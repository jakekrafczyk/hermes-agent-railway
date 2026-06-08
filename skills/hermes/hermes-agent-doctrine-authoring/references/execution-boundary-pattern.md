# Execution Boundary Pattern — Anti-Execution Gate

When the orchestrator recognizes a task pattern and knows how to implement it,
the natural impulse is "I'll just do it." This is the **#1 failure mode** of
multi-profile architectures — it collapses delegation pipelines into a single
agent, rendering all other profiles useless.

## Failure Mechanism

```
"I recognize this pattern" → load reference docs → "I know how to do this"
  → short-circuit from "investigate and route" to "write the implementation"
```

The more familiar the task, the **greater** the danger. The orchestrator's own
expertise becomes a liability — it skips delegation precisely when it could
write the best task brief.

## The Anti-Execution Gate (installed in SOUL.md § Hard Rules)

Before ANY `write_file`, `patch`, or implementation `terminal` command:

### 3-Question Self-Check

1. **Is this implementation work?** (writing code, editing configs, creating deliverable files)
   → YES: STOP. Delegate.

2. **Does this belong to a specialized profile?** (code → code_architect, research → researcher)
   → YES: STOP. Write a task brief. Do NOT touch it yourself.

3. **Is this purely orchestration?** (task briefs, inbox processing, resolution appending,
   file moves within triage/, config reads for context, memory searches, SearXNG)
   → YES: Proceed. This IS your job.

### Litmus Test

If the action creates or modifies a file outside of `/data/workspace/triage/`
or `/data/workspace/active_client.yaml`, it's almost certainly domain work.
Stop and delegate.

### Danger Zone Language

Explicit language naming the failure mode is critical — vague policy
statements ("you don't execute domain work") get ignored under cognitive load:

> **When the pattern is familiar and the fix is obvious** — that's the DANGER ZONE.
> The easier the implementation looks to you, the more likely you're
> short-circuiting. Pause. Write the task brief. Trust the specialized
> profile to implement it — that's what they're for.

> **When in doubt:** delegate. A task brief that arrives at the wrong profile
> is a minor error. You executing domain work is a structural failure.

## Copy-Paste for New Orchestrator Profiles

```markdown
## Execution Boundary (CATASTROPHIC FAILURE MODE)

The #1 way you fail: recognizing a task pattern ("I've done this before"), knowing
how to implement it, and executing it yourself instead of delegating.

**Pre-Action Self-Check** — before ANY write_file, patch, or implementation
terminal command:

1. **Is this implementation work?** → YES: STOP. Delegate.
2. **Does this belong to a specialized profile?** → YES: STOP. Write a task brief.
3. **Is this purely orchestration?** → YES: Proceed.

**Litmus test:** files outside /data/workspace/triage/ = domain work.

**DANGER ZONE:** the easier the implementation looks, the more likely you're
short-circuiting. Pause. Delegate. Trust the implementer.
```

## Worker Boundary (Researcher, Design, Social, SEO)

Workers have the same vulnerability in a different form: "I found the answer,
I'll just implement it." Their boundary rule:

- **The only files you write:** task files in `/data/workspace/triage/inbox/`
- **The only files you move:** consumed briefs to `task_requests/consumed/`
- **You do NOT:** write code, create assets, draft social posts, edit configs

The output contract is everything. The worker's job ends when the findings
hit `inbox/`. The orchestrator routes them to the implementer.

## Related Pitfalls

- **Profile-specific AGENTS.md rules replace generic SOUL.md identity.**
  When applying this pattern to a new worker profile, the boundary rules
  go in AGENTS.md under a `# Research Boundary` (or equivalent) section —
  NOT in SOUL.md. SOUL.md carries identity and tone; AGENTS.md carries
  operational constraints.

- **The implementer (code_architect) does NOT need this gate.**
  Implementing IS its job. Its guardrails are CLAUDE.md §2 (Simplicity
  First) and §3 (Surgical Changes), not a prohibition on implementation.

- **Test the boundary immediately after installation.**
  Ask the orchestrator to walk through a danger-zone scenario and confirm
  it self-identifies the delegation requirement before touching tools.
  A self-report of "I would delegate" without the self-check walkthrough
  is not sufficient — the check must be demonstrated step by step.
