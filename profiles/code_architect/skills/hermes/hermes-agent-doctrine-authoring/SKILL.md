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

## Content Allocation Map (where things go)

| Content type | Goes in |
|---|---|
| Persona / voice / tone | SOUL.md |
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

- **Don't write before confirmation** on production files unless the user
  used unambiguous write-now language. Phrases like "looks good", "I have
  one more edit", or "let's see it" are NOT write authorizations — they're
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

- **The `patch` tool redacts secrets in YAML config files.** When `old_string`
  or `new_string` contains an API key or bearer token, the patch tool's
  secret-scanning pass may write a literal placeholder (`fc-f6b...9a3e`)
  into the file. For config edits touching `mcp_servers` env blocks or any
  section with credentials, use `execute_code` (in-memory replace + write)
  or `write_file` (full rewrite) instead of `patch`. Always verify with
  `search_files` after: check the value doesn't contain `...` and the key
  length matches the real key from `.env`.

- **Config migration verification is mandatory.** After moving blocks between
  profile configs, run a structured check: target sections present/absent
  per expectations, no stale references to old profile names or retired
  formats, no redacted secrets, line counts confirm the delta.

## Support Files

- `references/file-allocation-map.md` — extended notes on what goes where
  and the reasoning, for cases where this skill's table is ambiguous.
- `references/task-coordination.md` — multi-profile task coordination
  pattern (task_requests → inbox → resolved pipeline, YAML frontmatter
  spec, error type → fix map). Load when setting up orchestrator-worker
  profile pairs that share a filesystem and Supermemory container tag.

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

## Related Skills

- `hermes-railway-setup` — environment-level config (venv, plugins, memory
  providers). Load alongside this skill when the doctrine change requires
  a config.yaml provider/plugin change.
- `hermes-system-check` — run after major doctrine edits to verify the
  agent still boots cleanly and tools are reachable.
