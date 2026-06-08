---
name: hermes-agent-doctrine-authoring
description: Authoring and revising layered agent doctrine files (SOUL.md, profile AGENTS.md, config.yaml) for Hermes deployments. Covers separation of concerns, token-economy editing, duplication audits, and the draft → confirm → write workflow this user expects.
---

# Hermes Agent Doctrine Authoring

This skill governs how to write and revise the layered agent doctrine and
credentials that ship with a Hermes deployment:

| File | Scope | Owns |
|---|---|---|
| `$HERMES_HOME/SOUL.md` | Per-profile identity, loaded every turn | Persona, tone, hard rules, multi-tenant boundaries, memory engine contracts (Supermemory). Default profile resolves to `/data/SOUL.md`; named profiles resolve to `/data/profiles/<name>/SOUL.md`. There is **no fallback chain** — each profile reads only its own SOUL.md. |
| `/data/profiles/<profile>/AGENTS.md` | Per-profile operational doctrine (loaded by workspace/web UI context, not Hermes native system prompt) | Model routing, tool-stack API contracts, deterministic execution loops, reasoning style |
| `/data/config.yaml` | System bindings | Providers, models, auxiliary tasks, MCP servers, terminal/browser settings |
| `$HERMES_HOME/.env` | Per-profile credentials (NOT read by the agent — consumed by Hermes runtime and tools) | API keys, tokens, secrets. Default profile: `/data/.env`. Named profiles: `/data/profiles/<name>/env`. **Each profile has its own `.env`** — there is no inheritance or fallback. If two profiles use the same keys, duplicate them explicitly. Keep each profile's `.env` minimal — only the keys that profile's config.yaml and tool stack actually need. |

Load this skill whenever the user asks to write, refactor, condense, split, or
audit any of these files — especially when they mention SOUL, AGENTS.md,
profiles, tone, identity, model routing, or token budget of the system prompt.

## Hard Rules (this user)

1. **Strict separation of concerns.** Never let a piece of content live in two
   files. If global persona drifts into AGENTS.md, or tool contracts drift into
   SOUL.md, fix it. Decide which file owns the content and reference it from
   the others by path (`see /data/SOUL.md`).

2. **Token economy is non-negotiable.** SOUL.md is loaded every turn — every
   byte costs. When the user gives a character budget (e.g., "2000–2800 chars
   max"), hit it. When they don't, default to the densest legible form.

3. **Draft → confirm → write.** For production files (anything under `/data/`
   that ships in the system prompt), always:
   - Show the full proposed content in a fenced code block.
   - Ask for explicit confirmation ("Confirm to overwrite?").
   - Only write after the user says yes / approves.
   - The exception: when the user explicitly says "write it" / "go ahead" /
     "you can write the files into production" in their request, skip the
     confirmation round and write directly.

4. **Audit for duplication before adding.** Before appending a new section,
   grep the other doctrine files for the same content. If it already lives
   elsewhere, either move it or link to it — do not duplicate.

5. **Verify cross-file consistency.** When changes touch config.yaml or the
   model-routing layer, confirm the other files still align. Specifically:
   - Does the SOUL/AGENTS reference any provider/model the config doesn't set?
   - Does the AGENTS execution loop assume tools the config doesn't expose?
   - Does memory provider / container_tag in config match what SOUL describes?
   - Does any profile's `.env` contain API keys for providers that profile's config.yaml doesn't reference?

## Active Client State (Multi-Tenant Routing)

When configuring a multi-tenant agency deployment, the active client is tracked
in a **dedicated state file** — NOT in `config.yaml`, NOT in `AGENTS.md`:

- **File:** `/data/workspace/active_client.yaml`
- **Content:** Single key: `active_client: <client_name>` (e.g. `mobilemd`)
- **Consumed by:** Profile doctrine (CLAUDE.md §5, SOUL.md, AGENTS.md) reads this file
  to determine which client container to target for Supermemory recall and store.
  Containers are client-only (`voltaic`, `mobilemd`, `west_shore_chamber`) — no domain suffixes.
  `voltaic` is the default: ALL auto-capture writes there, and it is the only operational
  context container for all profiles.

Write the file before switching client contexts. The orchestrator profile sets
or confirms the active client at the top of each session.

**CLAUDE.md §5 is the master cross-profile rule** for Supermemory recall (two searches
per task: `voltaic` + `{client}`), store discipline (client business context only,
skip when client=`voltaic`), and anti-duplication (orchestrator searches, workers
read the brief). All profile doctrine files delegate to it. See
`references/supermemory-container-isolation.md` for the full architecture.

## Content Allocation Map (where things go)

| Content type | Goes in |
|---|---|
| **Centralized behavioral baseline (CLAUDE.md)** | `/data/CLAUDE.md` — cross-profile code conduct (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution). Profiles reference it from their SOUL.md; it is NOT per-profile — it's a single shared file at the filesystem root. |
| **Centralized behavioral baseline (CLAUDE.md)** | `/data/CLAUDE.md` — cross-profile code conduct (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution). Profiles reference it from their SOUL.md; it is NOT per-profile — it's a single shared file at the filesystem root. |
| CLAUDE.md integration (reference + behavioral gate alignment) | SOUL.md § Hard Rules — each rule maps to a CLAUDE.md section (e.g., §1 → CLAUDE §1). AGENTS.md does NOT reference CLAUDE.md. |
| CLAUDE.md procedural gate enforcement | SOUL.md §4 (Pre-Change Gate) — mandatory 3-step self-check (state assumption → minimality check → verification) before ANY write_file/patch/terminal. If unclear: stop and ask. This is the enforcement mechanism; a file reference alone is not sufficient. |
| User skill level / explain-for-understanding directive | SOUL.md § Hard Rules — "assume the user is not an experienced developer; explain from first principles." |
| Multi-tenant client isolation rules | SOUL.md |
| Token conservation / memory-write format | SOUL.md |
| Memory provider API contracts (Supermemory v3) | SOUL.md (it's the memory engine the persona depends on) |
| Model routing (default vs DeepSeek Pro for sensitive phases) | profile AGENTS.md |
| Reasoning style (High-Structured, escalation rules) | profile AGENTS.md |
| Tool stack API contracts (Firecrawl, Camofox, SearXNG) | profile AGENTS.md |
| Deterministic execution loops, step-by-step curl recipes | profile AGENTS.md |
| Provider / model bindings, MCP server config | config.yaml |
| Terminal backend, workspace cwd | config.yaml |

**Exception override:** if the user explicitly directs content to a different
file ("put all supermemory stuff in SOUL"), follow the user. Their direction
overrides this map.

## Recommended Workflow

1. **Read all three files first.** Before any edit, `read_file` on SOUL.md,
   the relevant profile AGENTS.md, and config.yaml — even if the request only
   names one. You need cross-file context to avoid creating duplication.

2. **Run a duplication audit.** Note any content that appears in more than one
   file. Flag it to the user as a consolidation opportunity if they haven't
   already asked.

3. **Determine the write mode.** The user will indicate one of two patterns:

   ### Pattern A: Direct Write (agent writes the files)
   The user says "write it," "go ahead," "you can write the files," or asks
   to update a production file directly. Proceed to draft → confirm → write.

   ### Pattern B: Prompt File Handoff (user gives the prompt to a profile)
   The user asks for a prompt they can hand to another profile ("write a prompt
   I can give to the researcher profile," "give me a markdown file with prompts
   for the remaining work"). **Do NOT write the doctrine files directly.**
   Instead, write the prompt as a self-contained markdown file to the workspace
   (e.g., `/data/home/workspace/<descriptive-name>.md`). The prompt must be:
   - Self-contained — the target profile has no conversation context
   - Procedural — numbered steps with exact file paths
   - Specific about what file to write and where
   - Without "you can" language — imperative instructions ("Write X to Y")
   - Use a fenced code block labeled with the target path for any file the
     profile should create

   If multiple profiles need prompts, put them in one file with clear headers
   ("Prompt 1: Give to `default` profile", "Prompt 2: Give to `researcher`
   profile") and note the execution order.

4. **Draft in chat** (Pattern A) or **write the prompt file directly**
   (Pattern B — no confirmation round needed for prompt files, since they're
   staging documents, not production files).

5. **Batch multi-change proposals into a single confirmation.** When multiple
   config or doctrine changes are needed at once (e.g., move Kanban from
   researcher→default, move curator, add guardrails, change delegation model),
   present them as a single table with the proposed changes, ask once
   ("Proceed with all four changes?"), and apply all after a single "yes."
   Do NOT seek per-change approval — the user expects one round-trip.

6. **After config migrations, run a structured verification.** When moving
   blocks between profile configs (or adding new sections), verify with a
   checklist script:
   - Target section present/absent per profile
   - No stale references remain (old profile names, retired formats)
   - No secret redactions (check API key length ≠ 13, no `...` in values)
   - Line counts confirm adds/removals match expectations

## Pitfalls

- **Don't put tool/API contracts in SOUL.md.** SOUL is loaded every turn for
  every profile. Tool contracts belong in the profile AGENTS.md that uses
  them. Supermemory is the documented exception (per the user's directive)
  because it's the persistent memory engine the persona itself depends on.

- **Don't duplicate "Model Routing" across files.** It belongs in profile
  AGENTS.md only. If you find it in two places, consolidate.

- **When asked to print/show/see existing doctrine files**, put the file content
  in the main response body (fenced code block), not only in tool output blocks.
  The user expects to read files in the chat, not hunt through tool results.
  `read_file` produces tool output — that's for YOUR context, not theirs.

- **Don't write before confirmation** on production files unless the user
  used unambiguous write-now language. Phrases like \"looks good\", \"I have
  one more edit\", or \"let's see it\" are NOT write authorizations — they're
  iteration signals.

- **Don't invent config.yaml keys.** Hermes config has a defined schema
  (model, delegation, memory, auxiliary, approval, terminal, browser,
  tools, compression, mcp_servers, workspace). There is no `background`
  block — background/cron tasks inherit from `model.default` or
  `delegation` depending on invocation path, or get per-job overrides via
  the cronjob tool. If the user references a "background task model"
  setting, ask which lines they mean rather than guessing.

- **Don't strip the user's verbatim additions.** When they say "add this
  word for word" or paste a block in quotes, preserve the wording exactly,
  even if it slightly duplicates phrasing elsewhere. Their wording is
  authoritative.

- **Named-profile SOUL.md files are auto-seeded with generic boilerplate** at
  profile creation (from `hermes_cli/default_soul.py`). A named profile created
  with `hermes profile create <name>` will have a stale 513-byte default that
  says "You are Hermes Agent, an intelligent AI assistant..." — it was never
  customized. When auditing a profile, check whether its SOUL.md is still the
  default template. If it is, either replace it with profile-specific identity
  or delete it to avoid injecting contradictory generic persona text alongside
  the profile's actual doctrine.

- **Existing SOUL.md may carry the wrong persona entirely**, not just the stale
  default. When a profile directory was copied or repurposed (e.g., a marketing
  agency profile reborn as a code architect), SOUL.md can contain a fully
  customized but incorrect identity. Always read SOUL.md first — do not assume
  it matches the profile name. If the persona is wrong, replace the whole file
  rather than patching; persona rewrites are full-file replacements by nature.

- **Confirm the assignment scope before initializing.** When the user says
  "you are the Code Architect" or similar, do not assume what the architect
  BUILDS. The target could be an external application repo under
  `/data/workspace/src/`, or it could be the multi-profile Hermes framework
  itself at `/data/profiles/`. State your assumption about the target codebase
  before writing doctrine files — the wrong assumption ripples into the
  Codebase Map, config defaults, and workspace path. If the user says "your
  target is not X, it's Y," that's a scope realignment — the Codebase Map
  and workspace path need a full rewrite, not a patch.

- **AGENTS.md is the canonical filename — always uppercase.** Hermes tooling
  (workspace/web UI context detection, Cursor, Claude Code) looks for `AGENTS.md`,
  not `agents.md`. Creating `agents.md` (lowercase) is a silent miss — the file
  won't be loaded by any consumer. When creating a new AGENTS.md from scratch,
  use `AGENTS.md` explicitly. When the user says "change agents.md to AGENTS.md,"
  they mean `mv`, not a content edit.

- **CLAUDE.md on disk ≠ CLAUDE.md enforced.** A file reference in SOUL.md
  ("see /data/CLAUDE.md") is not enough — the agent will skip it during
  mechanical tasks (config changes, API checks) unless there is a hard
  procedural gate. The Pre-Change Gate pattern (SOUL.md §4: state assumption →
  minimality check → verification, stop if unclear) embeds CLAUDE.md compliance
  into every file-modifying action. When the user asks "did you reference
  CLAUDE.md," the real question is "did you follow it." The gate answers that.

- **The Codebase Map in AGENTS.md must reflect the actual filesystem layout**,
  not an aspirational or imagined target. Before writing it, run `search_files`
  or `ls` to verify every path in the tree exists. Paths like
  `/data/workspace/src/hermes-railway/` that don't exist yet are a trap — the
  agent will try to navigate to them and fail silently. List only directories
  that exist NOW. When the user scope-realigned the architect's target from
  an external app to `/data/profiles/`, the map needed a full rewrite, not a
  patch.

- **The `memory` tool uses `content` not `new_string` for replace actions.**
  Unlike `patch` (which takes `old_string` + `new_string`), `memory(action='replace')`
  takes `content` + `old_text`. Using `new_string` silently fails. This is
  different from every other replace interface in Hermes — it is a trap.

- **Prompt-injected memory ≠ tool's internal store.** An entry visible in your
  injected context may not be findable by `memory(action='replace')` or
  `memory(action='remove')`. The tool's `current_entries` list (shown during
  capacity errors) is the ground truth — if an entry isn't there, no `old_text`
  substring will match it, regardless of what appears in the prompt. This hits
  when: (a) the entry was trimmed due to capacity, (b) the injected text is a
  normalized/generated version of the stored raw text, or (c) the entry lives
  in a different container tag. **Diagnosis**: if you fail 2+ times, call
  `memory(action='add')` with deliberately small content to trigger a capacity
  error — the error message lists `current_entries` which is the authoritative
  index. If your target entry is absent, abandon `replace`/`remove` and add a
  corrected entry (compacting elsewhere first if needed).

- **Memory compaction is part of profile initialization.** When memory is near
  capacity, initializing a new profile requires compacting existing entries
  first. Workflow: `replace` verbose entries with denser versions, then `remove`
  entries that were merged into other entries, then `add` the new profile record.
  See `references/profile-initialization.md` for the full sequence.

- **Each profile has its own `.env` — no inheritance.** `/data/.env` belongs to
  the default profile; `/data/profiles/<name>/.env` belongs to that named
  profile. Hermes does NOT fall back to the default `.env` when a named
  profile's `.env` is missing a key. If both profiles need the same API key
  (e.g., OPENROUTER_API_KEY, FIRECRAWL_API_KEY), it must be in both files.
  If a key is only needed by one profile, only put it there — keeping each
  `.env` minimal reduces risk of a profile accidentally consuming the wrong
  credential.

- **AGENTS.md is NOT loaded by Hermes native system prompt.** The string
  "AGENTS.md" appears zero times in the Hermes Python source. AGENTS.md files
  are loaded by external tooling — the web UI's workspace subdirectory context
  detection, Cursor, or Claude Code. Operational doctrine that must travel
  with the agent (CLI, gateway, cron) belongs in SOUL.md. Reserve AGENTS.md
  for IDE/workspace-injected context.

- **Character-count audits cost nothing.** When the user asks to shorten
  a file, also report opportunities you found beyond what they asked for
  (e.g., "the new section adds ~900 chars but I can claw back ~1,700 by
  consolidating these duplications") — gives them an informed choice.

- **"Current State" sections accumulate transient facts that violate the
  Bright-Line Rule.** SOUL.md §6 says environmental facts go in memory,
  not profile files. But Current State sections drift: historical debug
  narratives ("CRITICAL DISCOVERY 2026-05-29: ..."), stale counts ("0
  memories stored"), and one-time migration notes ("FIXED: Copied
  supermemory.json → ...") accumulate and never get cleaned up. Audit
  Current State on every doctrine pass — transient play-by-play goes to
  the memory tool; the profile file keeps only the 4-5 durable
  configuration facts (container tag, caps, auto_recall status, routing
  rule, index verification date). See `references/token-compression-patterns.md`
  §3 for the before/after example.

- **`patch` tool redacts secrets in YAML config files.** When `old_string`
  or `new_string` contains an API key or bearer token, the patch tool's
  secret-scanning pass may write a literal placeholder (`fc-f6b...9a3e`)
  into the file. For config edits touching `mcp_servers` env blocks or any
  section with credentials, use `execute_code` (in-memory replace + write)
  or `write_file` (full rewrite) instead of `patch`. Always verify with
  `search_files` after: check the value doesn't contain `...` and the key
  length matches the real key from `.env`.

- **`config.yaml` is write-protected against `patch` and `write_file`.** Both
  tools reject writes to `/data/config.yaml` with "Write denied: '...' is a
  protected system/credential file." Three alternatives, in preference order:

  1. **`hermes config set <key> <value>`** — best for scalar values. Understands
     dotted key paths (e.g., `model.default`, `delegation.model`, `memory.provider`).
     **CRITICAL**: always set `HERMES_HOME=/data` when targeting the default profile:
     ```bash
     HERMES_HOME=/data /opt/hermes/.venv/bin/hermes config set model.default deepseek/deepseek-v4-flash
     ```
     Without `HERMES_HOME=/data`, the command writes to the **current session's
     profile** config (e.g., code_architect), silently mutating the wrong file.
     For named profiles, use `HERMES_HOME=/data/profiles/<name>`.

  2. **`sed` via `terminal`** — for simple substitutions when `hermes` CLI isn't
     available or for multi-value regex:
     ```bash
     cd /data && sed -i 's|old_value|new_value|' config.yaml
     ```
     Use `|` as the sed delimiter when values contain `/` (e.g., URLs).

  3. **`execute_code` with Python in-memory replace** — for multi-line or
     structural YAML changes. Bypasses the tool-level write guard.

  Always verify with `grep -n "new_value" config.yaml"` after any approach.

  **WARNING: `hermes config set` creates new YAML sections when the dotted path
  doesn't match the existing structure.** For example, `hermes config set
  model.reasoning_effort high` on a config where `reasoning_effort` lives under
  `agent:` (not `model:`) will create a duplicate `model:` section at the file's
  end instead of modifying the existing value. The CLI reports success but writes
  to the wrong location — the old value remains intact under `agent:`. Always
  grep for the key BEFORE running `hermes config set` to identify its actual
  section, and grep again AFTER to confirm the change landed in the right place.

- **Named profiles inheriting API keys: each `.env` is fully standalone.**
  A named profile's one-shot test (`hermes -z`) that fails with "No LLM
  provider configured" even though the model appears correct in `hermes
  profile` output means the `.env` is missing credentials. Check for
  `OPENROUTER_API_KEY`, `FIRECRAWL_API_KEY`, and `SUPERMEMORY_API_KEY` —
  Hermes does NOT fall back to the default profile's `.env` for named
  profiles. Copy missing keys from `/data/.env` to the profile's `.env`.
  The same applies for any MCP or tool credential (Firecrawl, SearXNG
  tokens, browser auth). Profile isolation is strict — no inheritance.

- **Named profiles need their own plugins/ directory with symlinks to shared plugins.**
  Hermes discovers plugins under `$HERMES_HOME/plugins/<name>/`. When a plugin
  is installed only in the default profile's `/data/plugins/` directory,
  named profiles (e.g., researcher) cannot see it — `hermes memory status`
  will show the plugin as "NOT installed" even though it exists on disk.
  The fix is a symlink:
  ```bash
  mkdir -p /data/profiles/<name>/plugins
  ln -s /data/plugins/<plugin_name> /data/profiles/<name>/plugins/<plugin_name>
  ```
  This works because plugin discovery walks real paths — symlinks resolve
  correctly. No plugin copy needed, no code changes. After symlinking,
  verify with `HERMES_HOME=/data/profiles/<name> /opt/hermes/.venv/bin/hermes memory status`.
  This pitfall hit for `supermemory_governed` under the researcher profile
  and will recur for every new profile that needs governed memory caps.

- **Container tag naming consistency between `.env` and governed allowlist.**
  If `.env` sets `SUPERMEMORY_CONTAINER_TAG=voltaic_researcher` but
  `supermemory.json` `custom_containers` only has `voltaic_research`, the
  governed plugin will reject the tag on memory operations and silently
  fall back to the default container. Verify the env var value appears in
  `custom_containers` after any profile rename or domain change. The
  governed plugin matches exact strings — no pattern or prefix matching.

  **DEPRECATED (2026-06-05):** `SUPERMEMORY_CONTAINER_TAG` env var is no longer
  used. All profiles use `voltaic` as the default container. If you find this var
  in any `.env` file, remove it and update the profile's doctrine to reference
  CLAUDE.md §5 instead. See `references/supermemory-container-isolation.md` for
  the current architecture.

- **Supermemory architecture changes touch 8-10 files across profiles.**
  Changing container architecture is not a single-file edit. Minimum change
  surface: `supermemory.json` (containers), `CLAUDE.md` (cross-profile rules),
  3× config.yaml (container_tag), 2× .env (remove env overrides), 3× doctrine
  files (SOUL.md + AGENTS.md for recall/store/anti-duplication), plus memory
  cleanup of stale facts. Audit all three profiles before starting — check for
  `SUPERMEMORY_CONTAINER_TAG` env vars, config container_tag values, doctrine
  references to old container names, and `supermemory.json` custom_containers.
  Present the full change plan as a table before touching files. Follow the
  multi-change batch protocol (step 5 above): one table, one confirmation,
  one batch apply.

- **CLAUDE.md as cross-profile hard-rule carrier.** When a rule must be enforced
  across ALL profiles (orchestrator, researcher, code_architect, future workers),
  put it in `/data/CLAUDE.md` — all profiles reference it from their SOUL.md.
  Examples: Supermemory recall/store discipline (§5), code conduct (§1-4).
  This avoids duplicating the same rule in 3+ doctrine files and ensures a single
  point of truth. The pattern: CLAUDE.md states the rule; profile SOUL.md/AGENTS.md
  references the specific section and adds profile-specific application notes
  (e.g., "orchestrator searches first," "researcher reads the brief").

- **Pre-audit clarification protocol.** When the user asks you to audit or
  improve a profile, ask 5-10 targeted clarifying questions before making
  any changes — even if you think you understand the requirements. Use
  `clarify` one question at a time. This surfaced 7 critical design
  decisions for the orchestrator (manifest-driven discovery, investigation
  scope, memory provider, client selection protocol) and changed the
  researcher from a curl-based scraper into a domain-context researcher.
  The user explicitly expects questions before execution: "Before executing
  anything ask questions to clarify how i want things setup." The questions
  ARE the work — they define the design before a single file is touched.

- **Cron prompt minimalism.** When a cron job runs as a profile whose
  AGENTS.md already carries the full operational doctrine, the cron prompt
  must be a table of contents, not a textbook. Every procedural detail in
  the prompt duplicates what the system prompt already carries — dead
  weight. The prompt only needs: (1) what to check (path + file pattern),
  (2) silence rule, (3) output contract (1-2 lines per file), (4) reference
  to the authoritative doctrine file. The triage-inbox-watcher went from
  2,060 chars to 393 chars (81% smaller) by stripping all procedure and
  delegating to AGENTS.md. Same principle applies to any profile-scoped
  cron job: prompt lists the steps by name, AGENTS.md knows how to execute
  them. See `triage-error-resolution` skill → `references/triage-cron-watcher.md`.

- **Multi-profile model changes require both `model.default` and `delegation.model`.**
  When changing a profile's default model, also change its `delegation.model`
  unless you intentionally want subagents on a different model. Delegation
  children use `delegation.model`, not `model.default` — forgetting to update
  it leaves spawned subagents on the old (possibly more expensive) model.
  For bulk changes across profiles, iterate with `HERMES_HOME` set per profile
  and verify both keys afterward:
  ```bash
  HERMES_HOME=/data /opt/hermes/.venv/bin/hermes config set model.default <new_model>
  HERMES_HOME=/data /opt/hermes/.venv/bin/hermes config set delegation.model <new_model>
  # Then for each named profile:
  HERMES_HOME=/data/profiles/<name> /opt/hermes/.venv/bin/hermes config set model.default <new_model>
  HERMES_HOME=/data/profiles/<name> /opt/hermes/.venv/bin/hermes config set delegation.model <new_model>
  ```

- **Config migration verification is mandatory.** After moving blocks between
  profile configs, run a structured check: target sections present/absent
  per expectations, no stale references to old profile names or retired
  formats, no redacted secrets, line counts confirm the delta.

- **`read_file` tool has aggressive dedup that blocks re-reading unchanged files.**
  When `read_file` returns \"BLOCKED: You have called read_file on this exact
  region 3 times and the file has NOT changed\" or \"File unchanged since last
  read,\" you cannot directly re-read. Workaround: use `execute_code` with the
  `read_file` import (`from hermes_tools import read_file`), which bypasses the
  tool-level dedup tracking. This is essential when verifying config changes
  across multiple profiles — `grep -n` via `terminal` also works for quick
  spot-checks.
- **The orchestrator WILL short-circuit on familiar patterns.** When it
  recognizes a task ("git repo bootstrap + profile sync — I've done this
  before"), loads the reference docs, and knows how to implement the fix,
  the natural impulse is to execute it instead of delegating. This is the
  #1 failure mode of multi-profile architectures. The fix is a hard
  Anti-Execution Gate in the orchestrator's SOUL.md (3-question self-check
  before any write_file/patch/terminal, litmus test, DANGER ZONE language)
  AND a parallel Research Boundary in worker profiles. See
  `references/execution-boundary-pattern.md` for the full pattern with
  copy-paste markdown for new profiles. Test the boundary immediately
  after installation — ask the orchestrator to walk through a danger-zone
  scenario and confirm it self-identifies the delegation requirement
  before touching tools.

- **Every worker profile's AGENTS.md MUST include a task request polling section**
  as the first step of its execution loop. Without it, the profile never picks up
  work from `task_requests/`, and completed briefs pile up indefinitely. The
  required pattern:
  ```
  # Task Request Polling (Before Step 1)
  On session start, check `/data/workspace/triage/task_requests/` for `task_*.md`
  files with `assignee_profile: <this_profile_name>` (or `assignee_domain: <this_domain>`).
  If found:
  1. Read the task brief (YAML frontmatter + body).
  2. Extract: goal, scope, constraints, target URLs, output format.
  3. Move consumed brief to `/data/workspace/triage/task_requests/consumed/`.
  4. Proceed to execution.
  If no task requests: proceed directly.
  ```
  The `researcher` and `social_media` profiles have this. The `code_architect` profile
  does NOT — it was created without the polling section, which means task briefs
  assigned to it accumulate in `task_requests/` forever. When auditing a profile,
  check for this section. If missing, add it. See `references/agents-md-structure.md`
  §6 for the full template with profile-specific customization notes.

- **Supermemory container_tag resolution: config.yaml is NOT read by the plugin.**
  The governed plugin resolves the container tag at init (line 504-507) from
  three sources in strict priority: (1) `SUPERMEMORY_CONTAINER_TAG` env var,
  (2) `/data/supermemory.json` `container_tag` field, (3) hardcoded default
  `"voltaic"`. Config.yaml's `supermemory.container_tag` field is never
  consulted. Setting `voltaic_code_architect` in config.yaml has zero effect —
  the memories will still land in `voltaic`. The fix is to add
  `SUPERMEMORY_CONTAINER_TAG=voltaic_code_architect` to the profile's `.env`.
  The same rule applies to all profiles that need container isolation. See
  `references/supermemory-container-isolation.md` for the full recipe.

- **WebUI "next session" ≠ "next turn."** When the user is on the WebUI (not
  CLI), env var changes and `.env` edits take effect on the *next new
  conversation*, not the current one. There is no "profile reload" or
  "restart" concept — the WebUI reads `.env` once at conversation start.
  When explaining when a change takes effect, say "next conversation" not
  "next session" or "next profile load." The user confirmed they're on
  WebUI, so this distinction matters for every env-var change you propose.

## Support Files

- `references/file-allocation-map.md` — extended notes on what goes where
  and the reasoning, for cases where this skill's table is ambiguous.
- `references/task-coordination.md` — multi-profile task coordination
  pattern (profiles.yaml + clients.yaml manifests, session startup protocol,
  triage checklist, generalized task format, routing matrix, backward
  compatibility). Covers the full orchestrator→worker pipeline with
  manifest-driven discovery instead of hardcoded profile names.
- `references/profile-initialization.md` — full 5-phase workflow for
  initializing a new profile persona from an existing directory (audit →
  write doctrine → workspace setup → memory compaction → verify). Includes
  memory tool parameter gotcha (`content` vs `new_string`) and config
  defaults table for common profile types. Load when rebirthing a profile
  with a wrong persona or creating a net-new profile from scratch.
- `references/agents-md-structure.md` — template for AGENTS.md content:
  sub-agent definitions, tool routing matrix, domain-specific scales,
  workspace map, and design principles. Load when creating AGENTS.md for
  a new profile or auditing an existing one for completeness.
- `references/hermes-docs-cache.md` — pattern for caching compact doc indexes
  at `/data/system/reference/` (hermes_llms.txt: 135 lines, supermemory_llms.txt:
  134 lines). Replaces the old 59k-line full dump — indexes link to live docs
  pages on demand.
- `references/supermemory-container-isolation.md` — recipe for per-profile
  Supermemory container isolation using the `SUPERMEMORY_CONTAINER_TAG`
  env var. Covers the plugin's resolution priority, the `{identity}`
  template variable, multi-client dynamic routing, and verification
  procedure.
- `references/self-sufficient-profile.md` — three-part SOUL.md pattern for
  profiles with `auto_recall=false`: Infrastructure Atlas (hard-coded service
  endpoints, file paths, plugin inventory, config keys), Current State tracking
  (mutable facts with date stamps), and Session Startup Protocol (5 deliberate
  reads replacing auto_recall at ~3-4k tokens vs up to 40k).
- `references/token-compression-patterns.md` — six concrete compression
  techniques for shrinking doctrine files without losing behavioral info:
  table-ifying sub-agent lists, ASCII art → text flow, Bright-Line enforcement
  on Current State cruft, inline comments, one-line routing rules, template
  de-scaffolding. Always end with a before/after scorecard. Saves 10-20% per
  file with zero behavioral change.

## When to Use `patch` vs `write_file` for AGENTS.md

The skill's default is `write_file` (full rewrite) because doctrine files
are short enough that whole-file replace is clearer. Use `patch` instead
when ALL of these are true:
1. The file is small but the change is genuinely a single targeted block
   swap (e.g., converting a JSON example to YAML frontmatter).
2. There are 2–5 discrete, non-overlapping line-range changes that would
   be harder to review as one blob.
3. The user hasn't asked for a full rewrite or content reshuffle.

`patch` is WRONG when: restructuring sections, moving content between
files, or rewriting >50% of the file. Use `write_file` for those.

## Multi-Profile Coordination

When two profiles share one filesystem and Supermemory container tag,
the coordination layer needs:
1. A shared task format spec (`.task-format.md`) that both profiles'
   doctrine files reference — single source of truth for frontmatter
   fields, output types, and body structure.
2. Clear write/read roles per directory (`task_requests/`, `inbox/`,
   `resolved/`) so no profile writes where it should only read.
3. The orchestrator's AGENTS.md must include the complete error-type → fix
   map so it can resolve worker errors without guessing.
4. The worker's AGENTS.md must include task-request polling as the first
   step of its execution loop.

See `references/task-coordination.md` for the full template.
- `references/researcher-profile-patterns.md` — research-for-quality mission,
  domain-specific research modes (architecture, design, social, orchestration),
  context freshness rules, Firecrawl MCP integration replacing curl, Camofox
  curl retention for reliability, anti-ban rules for authenticated scraping,
  and owl-alpha model rationale. Load when configuring or auditing a researcher
  profile in a multi-profile agency deployment.
- `references/approval-gates.md` — per-task delegation control pattern. The
  orchestrator prompts the operator at task creation for one of three modes
  (auto-pipeline, gate-each-step, output-only) and stores the choice in the
  `approval_gates` field of the task brief frontmatter. Inbox processor checks
  the field before delegating to the next profile. Load when designing handoff
  flows in multi-profile pipelines.
- `references/profile-permissions.md` — clean architecture for granting full
  file/terminal access to all profiles while keeping a git-push approval gate
  on the single profile that touches repos. Covers command_allowlist cleanup,
  approvals.mode, tirith, config.yaml write-protection workaround, and a
  three-profile verification loop.
- `references/composio-mcp-integration.md` — Composio MCP config block,
  .env pattern, platform tool inventory (Twitter/X 78 tools, YouTube 47,
  Facebook 39, Instagram 29, LinkedIn 22, TikTok 10), managed OAuth2 auth
  model, pricing tiers for agency use, 12 gotchas, and multi-client
  isolation patterns. Load when wiring Composio into any Hermes profile.

## Related Skills

- `hermes-railway-setup` — environment-level config (venv, plugins, memory
  providers). Load alongside this skill when the doctrine change requires
  a config.yaml provider/plugin change.
- `hermes-system-check` — run after major doctrine edits to verify the
  agent still boots cleanly and tools are reachable.
