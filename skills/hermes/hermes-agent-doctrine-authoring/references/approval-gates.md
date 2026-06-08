# Approval Gates — Per-Task Delegation Control

Pattern for giving the operator per-task control over whether the orchestrator
auto-pipelines or pauses for confirmation between profile handoffs.

## The Pattern

### 1. Task Format Field

Add to `.task-format.md` frontmatter:

```yaml
approval_gates: none | each_step | output_only   # optional, defaults to "none"
```

| Value | Behavior |
|---|---|
| `none` | Auto-pipeline — orchestrator delegates without asking. Operator sees final output. |
| `each_step` | Gate at every handoff — orchestrator asks before delegating to next profile. |
| `output_only` | First profile completes, orchestrator surfaces output. No further delegation. |

### 2. Orchestrator Prompt (in AGENTS.md)

Before writing ANY task brief, the orchestrator uses `clarify`:

```
"Task: <one-sentence summary>. How should I handle this?
 1. Auto-pipeline — delegate and keep going, surface final result
 2. Gate at each step — I'll ask before passing to the next profile
 3. Output only — first profile completes, I surface results, no further delegation"
```

The operator's choice is written as `approval_gates: none|each_step|output_only`
in the task brief frontmatter.

### 3. Inbox Processor Checks the Field

When the orchestrator processes a completed task file from inbox/:
- Read `approval_gates` from the original task brief (or the completed file)
- If `each_step`: `clarify` before delegating to next profile
- If `output_only`: surface to operator, do NOT delegate further
- If `none` (default): auto-delegate to the next profile in the pipeline

### 4. Why Per-Task, Not Global

Different task types have different risk profiles:
- Code/infrastructure changes: low risk (reversible via git), good candidate for `none`
- Business/strategy decisions: high risk, good candidate for `each_step`
- Research-only: no delegation needed, good candidate for `output_only`

Global settings force the same behavior for everything — per-task gives the operator
control without slowing down low-risk work.

### 5. Scope

`approval_gates` only controls the orchestrator's behavior between handoffs.
Individual profiles still run autonomously — it doesn't insert approval prompts
inside their execution loops.
