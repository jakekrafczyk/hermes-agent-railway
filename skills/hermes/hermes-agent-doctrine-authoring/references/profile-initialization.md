# Profile Initialization — Full Workflow

Checklist for initializing a new profile persona from an existing (possibly
wrong-persona) profile directory. Different from editing an existing correct
profile — this is the "rebirth" workflow.

## Phase 1: Audit Current State

1. `read_file` on all doctrine files: SOUL.md, AGENTS.md (if exists), config.yaml
2. Check SOUL.md content against profile name — is it the right persona?
   - Stale default template (513-byte generic)? → Replace entirely.
   - Wrong persona entirely (e.g., marketing soul in code_architect)? → Replace entirely.
   - Correct but needs edits? → Use the normal patch workflow in the parent skill.
3. Check AGENTS.md exists. If missing, create from scratch.
4. Check `/data/CLAUDE.md` exists. The centralized behavioral baseline (Think Before Coding,
   Simplicity First, Surgical Changes, Goal-Driven Execution) must be present. If missing,
   the user will often attach it during init — write it to `/data/CLAUDE.md`.
5. Check config.yaml for persona-specific defaults:
   - `display.personality` — should match profile role
   - `terminal.cwd` — should point to the profile's workspace directory
   - `supermemory.container_tag` — may need adjustment for profile-scoped memory
6. Read `active_client.yaml` — what client/context does the profile serve?
7. Verify workspace directories exist (e.g., `/data/workspace/src/` for code architect)

## Phase 2: Write Doctrine Files

### SOUL.md (full rewrite for wrong persona)
Write a new SOUL.md from scratch. Structure:
- Core Identity (one paragraph)
- Tone (one paragraph)
- Hard Rules (bulleted, dense)
- Tool-specific contracts (Supermemory, etc.) if persona depends on them

### AGENTS.md (create from scratch if missing)
Structure template:
- Delegation Architecture (single sentence)
- Sub-agent Definitions (one per agent: role, toolsets, trigger, context contract, output)
- Tool Routing Matrix (| Task Pattern | Tool | Rationale | table)
- Codebase/Workspace Map (directory tree — MUST reflect actual filesystem, not aspirational)
- Domain-specific scales (review severity, priority bands)
- **Append Supermemory matrix routing** — copy from `/data/workspace/supermemory-matrix-routing.md` and append to end of AGENTS.md. Customize the profile-specific routing line with the correct `{active_client}_{domain}` container_tag.
- **IMPORTANT:** Always use the filename `AGENTS.md` (uppercase). Consumers look for the uppercase form; `agents.md` is a silent miss.

### SOUL.md — CLAUDE.md Wiring
When creating or rewriting SOUL.md, the header MUST reference the centralized behavioral baseline:
```markdown
**Behavioral baseline:** `/data/CLAUDE.md` — governs all code changes across profiles.
These architectural principles extend CLAUDE.md; where they conflict, CLAUDE.md wins.
```
Then align the Hard Rules section to CLAUDE.md's structure:
```markdown
## 1. Think Before Coding (CLAUDE.md §1)
## 2. Surgical Changes (CLAUDE.md §3)
## 3. Goal-Driven Execution (CLAUDE.md §4)
```
This replaces any generic "Code Quality Gates" section. The profile's own Architecture
Principles and domain-specific rules go below these three CLAUDE-aligned gates.

### config.yaml patches
Targeted `patch` calls for persona-specific defaults. Four common changes:
- `personality:` — profile-appropriate value
- `cwd:` — workspace directory
- `supermemory.container_tag:` — set to `{active_client}_{domain}` (e.g., `voltaic_code_architect`). Must match the container_tag in SOUL.md and the profile-specific routing line in AGENTS.md.
- `memory.provider:` — confirm it's set to `supermemory`

## Phase 3: Workspace Setup

1. Create workspace directories if they do not exist (`mkdir -p`)
2. Write `active_client.yaml` with the profile's context
3. **Copy `supermemory.json` to the profile's `$HERMES_HOME`.** Named profiles do
   NOT inherit `/data/supermemory.json`. Without it, `enable_custom_container_tags`
   defaults to `false` and `supermemory_*` tool schemas drop the `container_tag`
   parameter — multi-container mode silently disables. Copy from the default
   profile: `cp /data/supermemory.json /data/profiles/<name>/`. See
   `hermes-railway-setup` skill's `references/supermemory-multi-container.md`
   for the full pitfall explanation.

## Phase 4: Memory Cleanup and Persist

Memory is often near capacity from the previous profile's usage. The cleanup sequence:

1. Check current usage (the tool returns `usage: "XX/2,200 chars"`)
2. If >80%, compact existing entries:
   - `replace` — condense verbose entries to shorter versions
   - `remove` — delete entries that were merged into other entries
   - Target: get below 50% before adding new entries
3. `add` the profile initialization record
4. Update USER profile if the profile list changed

### Memory Tool Parameter Gotcha
The `memory` tool uses `content` for the new text in replace actions, NOT `new_string`.
```
memory(action='replace', target='memory', content='shorter text', old_text='text to find')
```
This is different from `patch` which uses `old_string` + `new_string`. Using `new_string` on `memory` silently fails — the tool returns an error about `content` being required.

## Phase 5: Verify

1. Confirm SOUL.md, AGENTS.md, config.yaml are written
2. Confirm active_client.yaml has correct value
3. Confirm workspace directories exist
4. Confirm memory entry for profile initialization exists
5. Report final file manifest and memory state to user

## Common Profile Types and Their Config Defaults

| Profile | personality | cwd | active_client | container_tag |
|---|---|---|---|---|
| orchestrator | (varies) | /data/workspace | agency/client | {client}_{domain} |
| researcher | (varies) | /data/workspace | agency/client | {client}_{domain} |
| code_architect | architect | /data/workspace/src | voltaic | voltaic_code_architect |
| seo | (varies) | /data/workspace | client | {client}_seo |

**Note:** `active_client` is the primary agency client (e.g., `voltaic`). The `_code_architect`
suffix identifies the profile role. The default profile lives at the `/data/` root — its
SOUL.md, AGENTS.md, and config.yaml are NOT under `/data/profiles/`.