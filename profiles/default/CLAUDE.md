# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 0. Workflow Protocol (Loaded Every Session)

If `/data/workflow/orchestration.md` exists, read and internalize it at session start. This
file contains multi-profile orchestration patterns (delegation, triage, routing, inbox
processing, error resolution) that are identity-agnostic and apply regardless of the agent's
personality. These patterns are distribution-owned and receive updates via the shared repo.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Supermemory Recall/Store Discipline (STRICTLY ENFORCED)

**Container architecture:** `voltaic` is the default container — it receives ALL auto-capture AND stores operational/technical context for all profiles. Client-specific containers (`mobilemd`, `west_shore_chamber`, etc.) store client business context only.

**Recall (two searches per task, agent-side):**
Before executing any client task, run TWO supermemory searches:
1. Against `voltaic` — operational/technical context (tool quirks, API endpoints, patterns)
2. Against `{active_client}` container — client business context (brand voice, audience, campaigns, objectives)
- **Skip search #2 when active client IS `voltaic`** — same container.
- If search #2 returns empty (new client, no context stored yet): proceed, no error.

**Store (memory tool, agent-side) — CLIENT BUSINESS CONTEXT ONLY:**
The `memory` tool (`action='add'`) is RESTRICTED to storing high-signal CLIENT BUSINESS CONTEXT ONLY:
- ✅ Client brand voice/guidelines, audience demographics, campaign history, business objectives, market positioning
- ❌ Operational facts — tool quirks, API endpoints, file paths, environment details. These reach `voltaic` through auto-capture.
- ❌ Task progress, session outcomes (use session_search for those).
- **When active client is `voltaic`:** Do NOT use the store tool. Auto-capture already writes operational context to `voltaic`, and when Voltaic IS the client, both operational and business context land in the same container automatically. The store tool adds nothing.

**Anti-duplication (orchestrator delegation):**
When the orchestrator delegates to a worker profile (researcher, code_architect):
- The orchestrator runs the two searches during triage and includes results in the task brief.
- Worker profiles do NOT re-run the same searches. The task brief IS their context.
- Exception: if the task brief explicitly says "memory search returned nothing" — worker may run its own search.

**Violation penalty:** Any `memory` store call for non-client-business content OR any recall duplication across orchestrator→worker is a doctrine violation. Profiles must self-audit before calling `memory` or running recall — check: "Is this client business context? Is the active client NOT voltaic? Has the orchestrator already provided this context?"

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.