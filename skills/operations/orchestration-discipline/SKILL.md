---
name: orchestration-discipline
description: "Enforces the orchestrator's correct role boundary — investigate and route, never implement. Triage checklist sequence, pipeline control gating, and delegation hygiene."
triggers:
  - orchestrator protocol violation
  - delegation without research first
  - skipped triage checklist
  - implementation in orchestrator context
  - forgot pipeline control clarifier
  - wrote implementation commands in task brief
---

# Orchestration Discipline — Anti-Pattern Prevention

## The Core Rule

> The orchestrator says **WHAT**, not **HOW**. Investigate context, split work into phases, route to correct profiles, and confirm at each gate. Never write implementation commands.

## The Failure Mode

**"I know how" → "I'll just do it."** The orchestrator recognizes a pattern (e.g., git repo bootstrap), loads the reference docs, and short-circuits from investigation to implementation — skipping triage, pipeline control, and profile selection. The task brief becomes an implementation script instead of a routing directive.

## Mandatory Sequence (Every Delegation)

### 1. Client Context Check
- Read `active_client.yaml`. Is this client-scoped or infrastructure?
- If infrastructure: explicitly state so. If client: confirm scope alignment.

### 2. Memory Search
- `session_search` for past sessions on this topic.
- Surface prior decisions, even stale ones, before creating new plans.

### 3. Pipeline Control Gate
- BEFORE any delegation call, present the 3-option clarifier:
  > "Task: `<summary>`. How should I handle this?
  > (A) Auto-pipeline — delegate and keep going, surface final result
  > (B) Gate at each step — I'll stop for your review between phases
  > (C) Output only — first profile completes, I surface results, no further delegation"

### 4. Phase Decomposition
- Split task into phases by profile domain (research → implementation → verification).
- Multiple profiles? The downstream profile always starts AFTER the upstream finishes.
- State the phase plan and confirm before any delegation.

### 5. Research First (When Applicable)
- Any task involving external docs, APIs, tool capabilities, or mechanisms: delegate to researcher FIRST.
- Researcher gathers the latest — docs change, APIs change, the code_architect should work from current information.
- **Researcher scope is EXTERNAL ONLY.** The code_architect already owns the local filesystem. Do NOT ask the researcher to catalog local files, enumerate configs, inspect `profiles/` directories, or answer questions the code_architect can answer by reading its own disk.
- Skip researcher for pure code/config tasks where all context is in the local filesystem — OR for questions the code_architect intrinsically knows (its own architecture, file layout, tool inventory).
- **Litmus test:** "Could the code_architect answer this by looking at its own files?" → DON'T ask the researcher. "Does this require web search, external docs, or knowledge beyond the local filesystem?" → DO delegate to researcher.
- **After research returns:** before delegating to code_architect, check whether the service has a Hermes-specific integration page (e.g., `service.com/hermes`). General docs often describe a more complex SDK path; the Hermes page may have a simpler endpoint. See `references/composio-mcp-gotcha.md`.

### 6. Delegate — Not Implement
- Task brief format: scope, constraints, output format, reference files. NOT shell commands.
- The worker profile decides HOW. The orchestrator defines WHAT must be delivered.
- If you find yourself writing `git init`, `curl -sL`, or `COPY profiles ./profiles` in a task brief, you've crossed the line.

### 7. Verify Before Handoff
- When researcher returns findings: review. Are they current? Complete? Relevant?
- When code_architect returns implementation: verify with the checks the worker was asked to run.
- Surface results to user; ask "Proceed?" before chaining to the next phase.

## Anti-Patterns (DO NOT DO)

| Anti-Pattern | Example | Correct Behavior |
|---|---|---|
| Writing shell commands in task brief | `"Run: git init && git checkout -b main..."` | `"Goal: Bootstrap git repo in /opt/hermes-railway/ and push to shared GitHub repo"` |
| Delegating directly to code_architect without research | Skipping researcher for a task involving external docs | Delegate to researcher first: "Gather current Hermes docs on profile export mechanisms" |
| Asking researcher about local filesystem facts | "Catalog every distributable file across all profiles" or "what's the code_architect's config look like?" | Researcher = external discovery only. Code_architect reads its own disk. Litmus: "could code_architect answer this by looking at its own files?" → don't delegate to researcher. |
| Skipping pipeline control clarifier | Assuming auto-pipeline and spawning subagents | Always ask (A)/(B)/(C) before first delegation |
| Conflating "I know the recipe" with "I should execute it" | Loading a reference doc and writing an implementation plan | Load the reference doc, cite it in the task brief as context for the worker |
| One massive delegation spanning multiple phases | Single delegate_task covering research + build + push | Phase 1: researcher. Phase 2: code_architect. Sequential, not bundled. |
| Trusting general API docs over platform-specific integration pages | Researching a service's general MCP/SDK docs, then implementing from those findings without checking for a Hermes-specific setup page | After researcher returns findings on any external service: check whether the service has a Hermes-specific integration page (e.g., `service.com/hermes`, `service.com/integrations/hermes`). General docs describe the lowest-common-denominator SDK path; the Hermes-specific page often has a simpler, zero-config endpoint. See `references/composio-mcp-gotcha.md` for the case study. |
| **Not auditing worker profiles for task request polling** | Files pile up in `task_requests/` with no profile consuming them | When task briefs accumulate in `task_requests/`, the root cause is almost always a missing Task Request Polling section in the target profile's AGENTS.md. The `code_architect` profile was created without one. Every worker profile MUST have a polling section that checks `task_requests/`, reads the brief, and moves it to `consumed/`. See `hermes-agent-doctrine-authoring` skill → `references/agents-md-structure.md` §1 for the mandatory template. |
| **Diagnostic investigation bleeds into execution** | Running `python -c "import supermemory"` to confirm the SDK is missing, then immediately running `pip install supermemory` to fix it | The boundary is crossed when the orchestrator reaches for a package manager, editor, or config-mutation tool. Investigation = read-only commands (import checks, grep, cat, `hermes memory status`). Execution = any write/side-effect command (`pip install`, `sed`, `write_file` outside triage/). When the fix is one command away, the DANGER ZONE is strongest — delegate even (especially) when the solution is obvious. |
| **Delegation repeatedly fails** | `delegate_task` returns budget limit, timeout, or max_iterations — orchestrator completes the work directly | Write the task brief to `task_requests/` FIRST (as normal). Then attempt delegation. If it fails: (a) RE-TRY ONCE with tighter scope and reduced toolsets. If still fails: (b) document the infrastructure constraint in the resolution file, complete the work directly, and surface the delegation failure to the user with a request to redelegate the review. NEVER silently self-execute without documenting why delegation was impossible. |
| **Repeatedly retrying the same failing approach** | Same tool/command fails 3+ times with identical or near-identical errors — orchestrator keeps varying parameters slightly and retrying | STOP on the 3rd failure. The tool is not the problem — the approach is. Generate an error report covering: what was attempted, what failed, root cause, and which fixes need code_architect. Do NOT attempt a 4th variation. The user's \"stop what you were doing and generate an error report\" directive is the canonical response to this pattern. |
| **Trusting MCP tool guardrails over cloud API capabilities** | An MCP tool returns a constraint error (\"requires self-hosted URL\", \"needs X configured\") — orchestrator interprets this as \"the entire service doesn't support this\" and falls back to local alternatives | MCP tools may impose tighter constraints than the underlying cloud API. When an MCP tool blocks, check the official docs for the service before assuming the capability is absent. Bypass the MCP tool with a direct API call if the cloud API supports it. See `references/mcp-tool-vs-cloud-api.md`. |
| **Trusting curator LLM narrative over run.json facts** | `hermes curator run` summary claims "archived 12 skills" but `run.json.consolidated` shows only 2 real absorptions | The curator's LLM describes intended actions in prose that it didn't actually execute. Always check `run.json` (specifically `consolidated[]`, `pruned[]`, `counts.consolidated_this_run`) for ground truth. The narrative in `last_run_summary` and REPORT.md prose is aspirational, not structural. |
| **Expecting curator to create umbrella skills** | Running `hermes curator run` after a dry-run that proposes new umbrellas (e.g., `ai-coding-agents`, `software-development-workflows`) — but the live run only performs simple absorptions into existing skills | The curator LLM can absorb skill A into existing skill B, but **cannot create new umbrella skills**. Umbrella creation requires delegate_task: (1) read all source SKILL.md files, (2) create merged umbrella, (3) `hermes curator archive` each source, (4) verify with `hermes skills list`. This is orchestrator work, not curator work. |

## Reference: Correct Flow Template

```
1. [clarify] Pipeline control preference (A/B/C)
2. [memory / session_search] Past work on this topic
3. [clarify] Confirm phase plan: "Phase 1: researcher gathers X → Phase 2: code_architect builds Y"
4. [delegate_task → researcher] "Gather current docs on <topic>"
5. [review output, present findings]
6. [clarify] "Findings complete. Proceed to implementation?"
7. [delegate_task → code_architect] "Scope: <what to build>. Constraints: <limits>. Reference: <researcher output>"
8. [verify implementation, present final result]
```

## Pitfall: "But This Is Infrastructure, Not Client-Scoped"

Infrastructure tasks still follow the same protocol. The only difference: skip the client isolation step (Step 1 acknowledges no client scope). Everything else — memory search, pipeline control, research first, delegate don't implement — still applies.
