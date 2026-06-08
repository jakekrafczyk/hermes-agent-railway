# Zero-Token Codebase Map Pattern

## Problem

When a profile needs to edit files across multiple profiles and directories,
discovery calls (`search_files(target="files")`, `ls`) burn 1-3 tool calls
and ~2-5k tokens per session just to locate files. In a multi-profile
deployment with shared infrastructure, this is wasteful — the filesystem
layout changes rarely.

## Solution

A **complete filesystem tree** hard-coded in the profile's AGENTS.md under a
`## Codebase Map (Zero-Token Index)` section. Every file and directory the
profile might need is pre-listed with a one-line description. A discovery
rule instructs the agent: "check map first, search only if not found."

## When to Apply

- Multi-profile deployments (orchestrator + worker + specialist profiles)
- Shared infrastructure (plugins, triage inbox, service configs)
- `auto_recall=false` (token-efficient mode — no memory prefetch)
- Profile expected to make filesystem changes without user guidance

## Format

```markdown
## Codebase Map (Zero-Token Index)

Complete filesystem tree. Use this instead of `search_files`/`ls` to locate
files — zero discovery tokens.

/data/                                    # DEFAULT PROFILE
/data/config.yaml                         # Main Hermes config
/data/CLAUDE.md                           # Cross-profile code conduct
...

**Discovery rule:** Before any `search_files(target="files")`, check this map
first. Every path listed is verified to exist (YYYY-MM-DD). If a path isn't
here, THEN search.
```

## Building the Map

Use `execute_code` with `os.listdir()` to walk all relevant directories,
filtering out binary files and non-text artifacts. Limit to depth 3-4.

Key directories to include:
1. The orchestrator profile root (`/data/`)
2. Every profile directory (`/data/profiles/<name>/`)
3. The triage inbox and task pipeline (`/data/workspace/triage/`)
4. Plugin directories (`/data/plugins/`)
5. Reference/doc indexes (`/data/system/reference/`)
6. Runtime installation paths relevant to debugging (`/opt/hermes-railway/`)

## Maintenance

- Update the map after ANY file creation, deletion, or directory restructuring
- Date-stamp the verification comment so future sessions know freshness
- The map lives in AGENTS.md (loaded with workspace context) — NOT SOUL.md
  (loaded every turn, token budget is tighter)

## Token Impact

| Approach | Cost per session |
|---|---|
| `search_files` discovery calls | 2-5k tokens (2-3 calls including results) |
| Pre-built codebase map in AGENTS.md | ~0 tokens (already in workspace context) |

The map adds ~1.5-2k chars to AGENTS.md but that's a one-time cost at context
load — every subsequent file access costs zero discovery tokens.

## Relationship to Self-Sufficient Profile Pattern

The codebase map is the **AGENTS.md complement** to the SOUL.md Infrastructure
Atlas. The Atlas gives the agent service endpoints, file paths, and config
keys. The map gives the agent the complete filesystem tree. Together they
eliminate all discovery calls for routine operations.

See also: `references/self-sufficient-profile.md`
