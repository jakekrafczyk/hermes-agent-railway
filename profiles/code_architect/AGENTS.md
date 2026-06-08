# Code Architect — Sub-agents & Tools

# Task Request Polling (Before Delegation Architecture)

On session start, check `/data/workspace/triage/task_requests/` for `task_*.md` files where `assignee_profile: code_architect` OR `assignee_domain: architecture`.
If found:
1. Read the task brief (YAML frontmatter + body).
2. Extract: task goal, scope constraints, What NOT to do, Output Format, priority.
3. Move consumed brief to `/data/workspace/triage/task_requests/consumed/`.
4. Proceed to execute the task.

If multiple task files exist: process oldest-first (by `created_at` in frontmatter).
If no matching task requests: proceed to normal idle state (user-initiated work).

## Delegation Architecture

Single orchestrator (this profile) → specialized leaf workers.
Leaf-only delegation enforced at config level (`max_spawn_depth: 1`).
Max 3 concurrent children.

## Sub-agents

| Agent | Trigger | Toolsets | Context Contract | Output |
|---|---|---|---|---|
| **code-reviewer** | PR review, diff analysis, pre-merge | terminal, file, search, web | File paths, unified diff, PR desc, target branch | Severity-tagged findings per Review Severity Levels |
| **test-writer** | "write tests for X", "add coverage" | terminal, file, search | Module path, test dir, coverage report, framework | Test file(s) + coverage summary |
| **dep-auditor** | CVE check, license review, upgrades | terminal, file, web, search | requirements.txt / pyproject.toml / package.json, lockfile | CVEs (ID+severity), license conflicts, upgrade candidates |
| **doc-generator** | "document X", "generate API docs" | terminal, file, search | Module path, doc style, existing patterns | Docstrings or standalone .md docs |
| **bug-hunter** | "debug X error", stack trace analysis | terminal, file, search, web | Error, stack trace, repro steps, module paths | Root cause + fix suggestion (diff-ready) |

## Tool Routing Matrix

| Task Pattern | Tool | Rationale |
|---|---|---|
| Read source files | `read_file` | Faster, line-numbered, paginated |
| Search codebase | `search_files(target="content")` | Ripgrep-backed, regex support |
| Find files by name | `search_files(target="files")` | Glob patterns, sorted by mtime |
| Edit files (targeted) | `patch` | Diff-safe, syntax-validated |
| Edit files (full rewrite) | `write_file` | Overwrites, auto-lints |
| Run tests/builds | `terminal` | Native shell, venv-aware |
| Git operations | `terminal` | All git commands |
| Hermes docs lookup | `read_file` on `/data/system/reference/hermes_llms.txt` | Compact doc index (135 lines) with links to full docs — saves ~59k lines of token bloat |
| Supermemory docs lookup | `read_file` on `/data/system/reference/supermemory_llms.txt` | Compact doc index (134 lines) with links to full docs |
| Research libraries/APIs | `web_search` → `web_extract` | Two-hop: find then extract |
| Python script (3+ chained calls) | `execute_code` | Loops, conditionals, batching |
| Dep graph analysis | `terminal` (pipdeptree/npm) | Native tooling |
| Rust/cargo operations | `terminal` | Cargo commands |

## Codebase Map (Zero-Token Index)

Complete filesystem tree. Use this instead of `search_files`/`ls` to locate files — zero discovery tokens.

```
/data/                                    # DEFAULT (orchestrator) PROFILE
/data/CLAUDE.md                           # Cross-profile code conduct (Think Before Coding, etc.)
/data/SOUL.md                             # Orchestrator persona + doctrine
/data/AGENTS.md                           # Orchestrator operational doctrine
/data/config.yaml                         # Main Hermes config (memory, delegation, MCP, models)
/data/.env                                # Default secrets (OPENROUTER, FIRECRAWL, SUPERMEMORY keys)
/data/supermemory.json                    # Memory runtime tuning (auto_recall, container_tag, caps)
/data/system/reference/hermes_llms.txt    # Compact Hermes doc index (135 lines)
/data/system/reference/supermemory_llms.txt # Compact Supermemory doc index (134 lines)

/data/plugins/
/data/plugins/supermemory_governed/       # Governed supermemory with caps (3 results, 3 calls/turn)
/data/plugins/supermemory_governed/__init__.py
/data/plugins/supermemory_governed/plugin.yaml

/data/profiles/code_architect/            # THIS PROFILE
/data/profiles/code_architect/SOUL.md     # Code Architect persona + Infrastructure Atlas
/data/profiles/code_architect/AGENTS.md   # Sub-agents, tool routing, codebase map, ecosystem
/data/profiles/code_architect/config.yaml # Profile-specific config (model, terminal cwd, memory)
/data/profiles/code_architect/.env        # Profile secrets (OPENROUTER, SUPERMEMORY_CONTAINER_TAG, etc.)
/data/profiles/code_architect/skills/     # Profile-local skill copies
/data/profiles/code_architect/memories/   # Profile-local MEMORY.md + USER.md

/data/profiles/researcher/                # SIBLING WORKER PROFILE
/data/profiles/researcher/SOUL.md         # Researcher persona
/data/profiles/researcher/AGENTS.md       # Research execution loop, error triage, task polling
/data/profiles/researcher/config.yaml     # Researcher config (Camofox user_id=researcher, SearXNG, etc.)
/data/profiles/researcher/.env            # Researcher secrets (CAMOFOX_URL, SUPERMEMORY_CONTAINER_TAG)

/data/workspace/triage/                   # INTER-PROFILE COORDINATION (shared filesystem)
/data/workspace/triage/.task-format.md    # Task file spec — single source of truth for frontmatter
/data/workspace/triage/inbox/             # Researcher writes completed task_<uuid>.md files here
/data/workspace/triage/in_progress/       # Orchestrator moves files here during processing
/data/workspace/triage/resolved/          # Processed files with ## Resolution appended
/data/workspace/triage/archive/           # Files >30 days old
/data/workspace/triage/task_requests/     # Orchestrator writes new task briefs here
/data/workspace/triage/task_requests/consumed/ # Researcher archives read briefs here
/data/workspace/active_client.yaml        # Multi-tenant routing: {active_client: <name>}

/data/skills/                              # Agent-created and replicated skills
/data/skills/productivity/ocr-and-documents/ # PDF/OCR extraction (pymupdf + marker-pdf)
/data/skills/productivity/ocr-and-documents/SKILL.md
/data/skills/productivity/ocr-and-documents/scripts/extract_pymupdf.py
/data/skills/productivity/ocr-and-documents/scripts/extract_marker.py
/data/venv/                                 # Python venv (pymupdf, pymupdf4llm, marker-pdf)

/data/workspace/src/                      # Active code repos (clone target)
/opt/hermes-railway/                      # Runtime installation (read-only, on PYTHONPATH)
/opt/hermes-railway/supermemory/          # Supermemory SDK (pip-installed, copied here)
/opt/hermes-railway/sitecustomize.py      # Monkey-patch overrides for baked Hermes modules
```

**Discovery rule:** Before any `search_files(target="files")` to locate a file, check this map first. Every path listed above is verified to exist (2026-05-29). If a path isn't here, THEN search.

## Ecosystem Pipeline (Inter-Profile Coordination)

```
default (orchestrator) → task_requests/ → researcher (worker) → inbox/ → orchestrator
  → resolves errors OR delegates → code_architect (this profile) → implements → resolved/
```

**Flow:** User → orchestrator writes task brief → `task_requests/` → researcher polls, consumes → `consumed/` → researcher runs SearXNG→Firecrawl→Camofox → writes findings → `inbox/` → orchestrator resolves errors or delegates implementation → Code Architect reads inbox context, implements changes → Resolution appended → `resolved/`.

**Key principle:** A change to any profile's config or doctrine affects the pipeline. Think in terms of the pipeline, not individual files.

## Review Severity Levels

| Level | Tag | Criteria |
|---|---|---|
| **CRITICAL** | 🔴 | Security vuln, data loss, production outage, credential leak |
| **HIGH** | 🟠 | Correctness bug, memory leak, race condition, deadlock |
| **MEDIUM** | 🟡 | Performance regression, missing error handling, test gap, coupling issue |
| **LOW** | 🟢 | Style drift, minor optimization, naming, doc gap |
| **INFO** | ⚪ | Observation, alternative approach, forward-compatibility note |

## Review Format

```markdown
## Review: <module> | 🔴0 🟠0 🟡0 🟢0 ⚪0
- **<file>:<line>** — <finding> (🔴/🟠/🟡/🟢/⚪) → Fix: <suggestion>
## Summary: <1-2 sentence verdict>
```

## Review Verification Gates (MANDATORY — Prevent False Positives)

**Before flagging ANY finding, consult the authoritative source. Do NOT rely on pattern-matching or "what seems right."**

| Gate | When | Verdict Question | Authoritative Source | Action |
|---|---|---|---|---|
| **G1 — Parameters** | Flagging a parameter as "may not exist" / "may not be accepted" | Is this parameter in the tool's schema? | Tool parameter schema (read the tool definition) | Read the tool's parameter description. If the parameter appears in the schema with valid enum/type, drop the finding. |
| **G2 — Toolsets** | Flagging a toolset name as "non-standard" / "not valid" | Is this toolset in the `delegate_task` enum? | `delegate_task` tool parameter schema (toolsets enum) | Check the `delegate_task` parameter description for the authoritative list. If the name appears, drop the finding. |
| **G3 — Files/Skills** | Claiming a file/skill "not found" / "does not exist" | Does a broad search find it? | `search_files(target="files")` with broad glob paths | Search with broad scopes: `/data/skills/`, `/data/profiles/`, `/data/workspace/`. If found, drop the finding. |

**Rule of thumb:** If your finding involves a claim of non-existence ("not found," "doesn't exist," "may not," "not standard"), you MUST verify against the authoritative source before issuing the finding. The cost is 1-2 tool calls; the cost of a false positive is eroded trust in the entire review.

### Token Optimization

These rules minimize token waste during verification. The three gates above are correct — they stay as-is. These rules govern *how* you execute them.

| Rule | Description |
|---|---|
| **Rule 1 — Category-scoped verification** | Only check the gate relevant to your finding. Flagging a parameter? Run only G1. Don't run G1+G2+G3 every time. |
| **Rule 2 — Batch verification calls** | If verifying multiple categories (e.g., a file AND a parameter), batch into one `execute_code` block or parallel `delegate_task` calls. Sequential isolated calls cost ~2× the tokens. |
| **Rule 3 — Prefer local schema from context** | When checking a tool parameter (G1), the schema is already in the tool description loaded into context. Reread from context first. Use `web_extract` only as a fallback. |
| **Rule 4 — Narrow glob first, then widen** | When checking file existence (G3), start with a narrow glob (e.g., `*reddit*` in `/data/skills/`) before widening to `*.md` in `/data/skills/`. A 3-result glob costs fewer tokens than a 50-result glob. |
| **Rule 5 — The 1-tool-call rule** | If verification needs >1 tool call, question whether the finding is worth flagging. Most "may not exist" claims can be verified or disproven with a single `search_files` or `read_file` on a known schema location. |

## Supermemory Routing

Before ANY supermemory tool: read `/data/workspace/active_client.yaml` → compose container_tag as `{client}_{domain}` (e.g. `voltaic_code_architect`). NEVER use blank/global tag. Applies to all four ops: search, store, forget, profile.