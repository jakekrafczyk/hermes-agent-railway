# AGENTS.md Structure Template

Template for a profile's AGENTS.md file. AGENTS.md holds operational doctrine:
sub-agent definitions, tool routing, execution patterns, and domain-specific
scales. It is NOT loaded by Hermes' native system prompt — it is consumed by
workspace/web UI context detection, Cursor, and Claude Code.

**Filename:** Always `AGENTS.md` (uppercase). Creating `agents.md` (lowercase)
is a silent miss — consumers look for the uppercase form and won't load the
lowercase variant.

## Required Sections

### 1. Task Request Polling (BEFORE Step 1 — Worker Profiles Only)

**This section is MANDATORY for every worker profile** (researcher, code_architect,
social_media, design, seo, etc.). Without it, the profile never picks up work from
`task_requests/`, and completed briefs pile up indefinitely in that directory.

The orchestrator profile does NOT need this section — it writes briefs, it doesn't
consume them.

**Standard pattern** (customize the `assignee_profile` / `assignee_domain` filter
and the extraction step for each profile):

```
# Task Request Polling (Before Step 1)

On session start, check `/data/workspace/triage/task_requests/` for `task_*.md`
files with `assignee_profile: <this_profile_name>` (or `assignee_domain: <this_domain>`).
If found:
1. Read the task brief (YAML frontmatter + body).
2. Extract: goal, scope, constraints, target URLs, output format.
3. Move consumed brief to `/data/workspace/triage/task_requests/consumed/`.
4. Proceed to execution.

If no task requests: proceed directly (user-initiated work).
```

**Profile-specific customizations:**

| Profile | Filter field | Extraction focus |
|---|---|---|
| `researcher` | `assignee_domain: research` | Research goal, scope, target sites/URLs, freshness override |
| `code_architect` | `assignee_profile: code_architect` | Goal, scope, constraints, reference files, verification steps |
| `social_media` | `assignee_domain: social` | Platform, goal, media files, brand guidelines, auto-publish flag |
| `design` | `assignee_domain: design` | Asset type, brand guidelines, target dimensions, style references |
| `seo` | `assignee_domain: seo` | Target URLs, keyword focus, competitor URLs, audit scope |

**Critical:** The consumption step (move to `consumed/`) must happen BEFORE
execution begins. If the profile crashes mid-execution, the brief is already
consumed and won't be re-processed. This is intentional — the orchestrator
handles retries via new task briefs.

### 2. Delegation Architecture (one sentence)
State the delegation pattern and any config-level constraints.
```
Single orchestrator → specialized leaf workers.
Leaf-only (max_spawn_depth: 1). Max 3 concurrent children.
```

### 3. Sub-agent Definitions
One subsection per agent. Each agent gets: role, toolsets, trigger, context
contract, and output description.

```markdown
### agent-name
- **Role:** leaf
- **Toolsets:** [terminal, file, search]
- **Trigger:** "when to dispatch this agent"
- **Context contract:** what the agent needs in its context parameter
- **Output:** what the agent returns
```

### 4. Tool Routing Matrix
Table mapping common task patterns to the correct tool. This prevents the
agent from using terminal grep when search_files is faster, or terminal cat
when read_file is paginated.

```markdown
| Task Pattern | Tool | Rationale |
|---|---|---|
| Read source files | `read_file` | Line-numbered, paginated |
| Search codebase | `search_files(target="content")` | Ripgrep-backed, regex |
| Find files by name | `search_files(target="files")` | Glob patterns |
| Edit files (targeted) | `patch` | Diff-safe, syntax-validated |
| Edit files (full rewrite) | `write_file` | Overwrites, auto-lints |
| Run tests/builds | `terminal` | Native shell |
| Git operations | `terminal` | All git commands |
```

### 5. Domain-Specific Scales
If the profile needs severity levels, priority bands, or other ordinal
scales, define them explicitly. Example for a code review profile:

```markdown
| Level | Tag | Criteria |
|---|---|---|
| **CRITICAL** | 🔴 | Security vuln, data loss, production outage |
| **HIGH** | 🟠 | Correctness bug, memory leak, race condition |
| **MEDIUM** | 🟡 | Performance regression, missing error handling |
| **LOW** | 🟢 | Style drift, minor optimization, naming |
| **INFO** | ⚪ | Observation, alternative approach |
```

### 6. Workspace/Codebase Map
Directory tree showing where things live. Essential for profiles that work
across multiple repos or directory structures.

**Pitfall:** Every path in the map must exist on disk. Before writing it, run
`search_files(target="files")` or `ls` to verify each directory. Paths like
`/data/workspace/src/hermes-railway/` that don't exist yet are a trap — the
agent will try to navigate to them later and fail silently. List only what
exists NOW. When the user scope-realigned a profile's target (e.g., from an
external app to `/data/profiles/`), the map needs a full rewrite, not a patch.

## Design Principles

- **AGENTS.md is operational, not identity.** Persona/tone/hard-rules go in
  SOUL.md. Tool routing/execution patterns go here.
- **Keep it actionable.** Every section should help the agent pick the right
  tool, dispatch the right sub-agent, or apply the right severity level on
  the next turn.
- **Sub-agent context contracts are critical.** The agent has no conversation
  history — the context parameter IS its world. Be specific: "Full file paths,
  unified diff, PR description, target branch" not "relevant info."
- **Scales must be decision-grade.** If a severity level doesn't change what
  the agent does next, merge it into the level above. Four levels that drive
  different actions are better than seven levels where three are cosmetic.
- **Task polling is not optional.** If you're writing AGENTS.md for a worker
  profile and it doesn't have a Task Request Polling section, it's incomplete.
  The profile will never receive work through the triage pipeline.
