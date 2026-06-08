---
name: hermes-railway-setup
description: "Setting up plugins, memory providers, and Python packages on the Hermes Railway deployment where the venv is root-owned and read-only."
triggers:
  - install plugin
  - memory provider setup
  - pip install fails permission denied
  - hermes memory setup
  - package not importable in hermes venv
  - supermemory setup
  - add Python dependency to hermes
  - add MCP server
  - firecrawl MCP
  - hermes mcp add
  - connect MCP tool
  - camofox setup
  - browser anti-detection
  - deploy camofox railway
  - CAMOFOX_URL
  - persistent browser sessions
  - persistent browser sessions
  - override bundled memory plugin
  - cap memory tool tokens
  - supermemory burning openrouter tokens
  - per-turn tool budget
  - container_tag voltaic
  - SOUL.md persona governance
  - inject agency-wide rules into agent
  - nous portal setup
  - switch provider
  - oauth login headless
  - hermes model
  - hermes auth
  - provider migration
  - inference provider
  - skills curator
  - curator run
  - curator dry-run
  - skill consolidation
  - skill lifecycle
---

# Hermes Railway Setup

## Environment Facts

- Hermes venv: `/opt/hermes/.venv` — **root-owned, not writable** by the `hermes` user
- Package manager for the venv: `uv` (no `pip` binary in the venv)
- PYTHONPATH (set in `/opt/hermes-railway/entrypoint.sh`):
  ```
  /opt/hermes-railway:/opt/hermes-webui:/opt/hermes:${PYTHONPATH:-}
  ```
- `/opt/hermes-railway/` is **writable** by the `hermes` user
- `/opt/hermes/plugins/**` is **root-owned, not writable** — but bundled plugins
  can be effectively overridden by renaming a copy under `$HERMES_HOME/plugins/`
  and pointing `memory.provider` (or the equivalent config key) at the new name.
  Discovery looks up by exact name — collisions favor bundled, distinct names
  resolve to the user-installed copy.
- `HERMES_HOME` defaults to `/data`; config lives at `/data/config.yaml`, keys at `/data/.env`
- The `hermes` CLI binary: `/opt/hermes/.venv/bin/hermes`
- **`$HERMES_HOME/SOUL.md` is auto-injected into the system prompt** (loaded by
  `agent/prompt_builder.py::load_soul_md`). This is the canonical place to drop
  agency-wide rules, persona, token-governance doctrine, multi-tenant boundary
  policy, etc. No `AGENTS.md` or wrapper needed — write the file and it appears
  in every new session's system prompt automatically. `AGENTS.md` works too but
  is scoped to a working directory; `SOUL.md` is global per Hermes home.

## Installing Python Packages (venv is read-only)

Since `uv pip install --python /opt/hermes/.venv/bin/python` fails with permission denied, and user site-packages are disabled in the venv (`site.ENABLE_USER_SITE = False`), the workaround is:

1. Install the package normally (user-space): `pip install <pkg>`
2. Copy the installed package dir(s) to `/opt/hermes-railway/`:
   ```bash
   cp -r ~/.local/lib/python3.13/site-packages/<pkg> /opt/hermes-railway/
   cp -r ~/.local/lib/python3.13/site-packages/<pkg>-*.dist-info /opt/hermes-railway/
   ```
3. Verify importability in the Hermes venv:
   ```bash
   /opt/hermes/.venv/bin/python -c "import <pkg>; print('ok')"
   ```

**Why it works:** `/opt/hermes-railway` is on `PYTHONPATH`, so anything placed there is importable by the Hermes venv Python without touching the venv itself.

**Pitfall:** Only copy the package itself and its dist-info. Don't blindly copy all user site-packages — dependency conflicts with venv packages can arise. Check if each dependency is already present in the venv first.

## Setting Up a Memory Provider

General flow (works for supermemory and other providers):

```bash
# 1. Set the provider in config
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes config set memory.provider <provider>

# 2. Add the API key to /data/.env
echo 'PROVIDER_API_KEY=<key>' >> /data/.env

# 3. Verify
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes memory status
```

Expected status output shows: `Plugin: installed ✓`, `Status: available ✓`.

## Supermemory Specific Setup

See `references/supermemory-setup.md` for the full procedure. For MCP servers (including Firecrawl), see `references/firecrawl-mcp-setup.md`. For Firecrawl Python SDK v4.x API shape (Pydantic models, not dicts), see `references/firecrawl-sdk-v4-usage.md`. For Camofox browser setup, see `references/camofox-railway-setup.md`.

Short form:
1. Install SDK: `pip install supermemory` → copy to `/opt/hermes-railway/`
2. `hermes config set memory.provider supermemory`
3. `echo 'SUPERMEMORY_API_KEY=<key>' >> /data/.env`

**What "exposed as active tools" actually means:** The governed plugin's
`get_tool_schemas()` registers `supermemory_store`, `supermemory_search`,
`supermemory_forget`, and `supermemory_profile` directly with Hermes' tool
registry at load time — not via `tools.pre_selection` or any config key. They
are available to every profile (default + researcher) automatically. No
`explicit_tool_routing` toggle is needed. If you can call `supermemory_search`
in a session, the routing is already working. See
`references/governed-memory-plugin.md` for the pitfall explaining what
`tools.pre_selection` actually controls (Hermes built-in tools only, not
plugin-registered tools).

## Bundled Memory Plugins

All memory plugins are pre-bundled at `/opt/hermes/plugins/memory/`. No Git install needed. Their `plugin.yaml` declares `pip_dependencies` — but the auto-installer also uses `uv pip install --python sys.executable` and hits the same permission error. Use the copy-to-hermes-railway workaround instead.

Available bundled providers: `byterover`, `hindsight`, `holographic`, `honcho`, `mem0`, `openviking`, `retaindb`, `supermemory`.

## Sharing Plugins Across Profiles (Symlink Pattern)

When running multiple Hermes profiles (default + researcher + code_architect,
etc.), a plugin installed only in the default profile's `$HERMES_HOME/plugins/`
is invisible to named profiles. Hermes discovers plugins per-profile under
`$HERMES_HOME/plugins/<plugin_name>/` — there is no shared plugin path or
inheritance from the default profile.

**Symptom:** `hermes memory status` shows "Plugin: NOT installed ✗" even though
the plugin exists at `/data/plugins/<name>/`. The named profile simply can't
see it.

**Symptom (silent):** auto-capture appears configured (`auto_capture: true` in
`supermemory.json`, API key present, `hermes memory status` says "available ✓")
but no conversation turns are being stored. The plugin is silently failing to
load for this profile — the built-in `memory` tool still works (writes to local
MEMORY.md), but the supermemory provider never initializes, so `sync_turn()`
never fires and `on_memory_write()` never calls the API. This is the #1 cause
of "my memory isn't working but everything looks fine." **Diagnosis:** run
`HERMES_HOME=/data/profiles/<profile> /opt/hermes/.venv/bin/hermes memory status`
for EACH profile. If any says "NOT installed," the plugin is missing from that
profile's `$HERMES_HOME/plugins/` directory.

**Fix — symlink, don't copy:**
```bash
mkdir -p /data/profiles/<profile_name>/plugins
ln -s /data/plugins/<plugin_name> /data/profiles/<profile_name>/plugins/<plugin_name>
```

**⚠️ Pre-flight check — verify `plugins/` is a real directory, not a symlink:**
```bash
for d in /data/profiles/*/; do
  if [ -L "${d}plugins" ]; then
    echo "DANGER: ${d}plugins is a symlink to $(readlink ${d}plugins) — replace with real dir first"
  fi
done
```
If any profile's `plugins/` is a directory-level symlink, `rm -rf` operations inside it
will follow the symlink and destroy the canonical copies in `/data/plugins/`. Replace
directory symlinks with real directories containing per-plugin symlinks. See
`references/governed-memory-plugin.md` pitfalls for the full recovery recipe.

**Why symlink over copy:** the governed plugin's `__init__.py` may be actively
maintained (caps, container logic, routing rules). A symlink ensures all profiles
run the same version. A copy creates a fork that diverges silently.

**Verify:**
```bash
HERMES_HOME=/data/profiles/<profile_name> /opt/hermes/.venv/bin/hermes memory status
# Expect: Plugin: installed ✓
```

**This is a one-time per-profile setup**. When adding a new profile, create
the symlink as part of the profile initialization checklist. When replacing or
upgrading the plugin, the symlink automatically follows — no per-profile update
needed.

**Verified with:** supermemory_governed under the researcher profile
(`/data/profiles/researcher/plugins/supermemory_governed → /data/plugins/supermemory_governed`).

## Overriding a Bundled Plugin (token caps, container scoping, custom defaults)

Plugin discovery uses **exact name lookup**: collisions favor bundled, but a
*differently-named* copy under `$HERMES_HOME/plugins/<new_name>/` is loaded
normally as long as `memory.provider` points at the new name. This is how you
ship hard token-spend caps, default container tags, and per-turn tool budgets
on top of a stock provider without root access.

Full recipe (with the verified Voltaic Marketing example — supermemory →
`supermemory_governed` with max 3 results per search, max 3 tool calls per
turn, container `voltaic`): see `references/governed-memory-plugin.md`.

Short form:

```bash
mkdir -p /data/plugins/<provider>_governed
cp /opt/hermes/plugins/memory/<provider>/__init__.py /data/plugins/<provider>_governed/
cp /opt/hermes/plugins/memory/<provider>/plugin.yaml /data/plugins/<provider>_governed/
# Edit __init__.py: change `name` property, add module-level caps, enforce in handle_tool_call.
# Edit plugin.yaml: change top-level `name:` field.
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes config set memory.provider <provider>_governed
```

**Why caps must be in code, not config:** config defaults (`max_recall_results`,
`container_tag`) are advisory — the bundled `_tool_search` still accepts caller
`limit` up to 20, and nothing rate-limits multiple calls per turn. Only
module-level constants enforced inside `handle_tool_call` and `_tool_search`
defend against runaway model behavior. The reference file shows exactly which
lines to patch.

## Tuning a Governed Memory Plugin at Runtime (auto_recall, auto_capture)

Even after you've built `<provider>_governed` with module-level caps, the plugin
still has two **per-turn behaviors** that can quietly burn tens of thousands of
input tokens per user message. These are controlled by `$HERMES_HOME/<provider>.json`
(e.g. `/data/supermemory.json`) and load at session start, not from code constants:

| Flag | Default | What it does every turn |
|---|---|---|
| `auto_recall` | `true` | `prefetch()` queries memory with the user's message, retrieves matching memories + profile facts, and injects them as a `<supermemory-context>` block into the system prompt |
| `auto_capture` | `true` | `sync_turn()` stores user message + assistant response as a new memory document |

**The runaway loop** (verified on supermemory_governed, container `voltaic`):
each turn stores 1 new memory, the next turn's `prefetch()` retrieves it (plus
all earlier matches), formats them into the context block, and feeds the whole
growing pile back into the prompt. With `max_recall_results: 3` you still get a
profile dump every `profile_frequency` turns. Result: input tokens climb from
baseline to 40k+ within a handful of turns.

**Diagnostic clue:** if input tokens jump dramatically right after you wire up a
memory provider but `system_prompt_block()` text is unchanged, the burn is
coming from `prefetch()` injection, not the static system block.

### Fix — disable auto_recall while keeping memory tools available

```bash
cat > /data/supermemory.json <<'EOF'
{
  "auto_capture": true,
  "auto_recall": false,
  "container_tag": "voltaic",
  "max_recall_results": 3,
  "search_mode": "hybrid"
}
EOF
```

Takes effect on the **next new session** — `initialize()` reads this file once
per session. Existing sessions keep their loaded config.

What changes:
- `auto_recall: false` → no automatic context injection. `<supermemory-context>`
  block disappears entirely.
- `auto_capture: true` (kept) → conversations still get saved for future
  cross-session recall.
- Tool routes `supermemory_search`, `supermemory_store`, `supermemory_forget`,
  `supermemory_profile` keep working — the model calls them deliberately when
  needed instead of paying for a guess-injection every turn.

**Default policy for token-conscious agency setups:** ship `auto_recall: false`
from day one. Re-enable per session only if you specifically want passive
profile injection. Leave `auto_capture: true` — writes are cheap, the burn is
on the read side.

### Multi-Container Setup (Option B)

When you need profile-scoped container isolation (e.g., architecture facts in
`voltaic_code_architect` while conversation turns stay in `voltaic`), use
multi-container mode instead of changing the primary tag. Full recipe in
`references/supermemory-multi-container.md`.

Short form: add three keys to `/data/supermemory.json`:
- `enable_custom_container_tags: true`
- `custom_containers: ["voltaic_code_architect"]`
- `custom_container_instructions: "Use voltaic_code_architect for..."`

Then target the secondary container explicitly on tool calls:
`supermemory_store(content="...", container_tag="voltaic_code_architect")`.

**Critical limitation:** auto-capture and the built-in `memory` tool ALWAYS
write to the primary container only — they cannot target secondary containers.
Explicit `supermemory_store` with a container_tag is the only write path.

**Pitfall — don't blame the SOUL.md or system_prompt_block first.** Both are
small, static, and identical every turn. The `<supermemory-context>` block is
the only thing that grows turn-over-over, and it doesn't show up in any
`hermes config` output — only in the actual prompt sent to the model. Check
`$HERMES_HOME/<provider>.json` first.

**Pitfall — container_tag in config.yaml is NOT read by the plugin.** The
governed memory plugin resolves its active container tag from only two
sources (in priority order):

1. `SUPERMEMORY_CONTAINER_TAG` environment variable (highest)
2. `$HERMES_HOME/supermemory.json` → `container_tag` field
3. Hardcoded default: `"voltaic"`

`config.yaml`'s `supermemory.container_tag` key is **ignored** by the plugin
at initialization. If you set `container_tag: voltaic_code_architect` in
config.yaml and nothing else, writes silently go to `voltaic` — and the user
sees zero memories when searching their intended container.

**Fix — per-profile container isolation:** add `SUPERMEMORY_CONTAINER_TAG`
to the profile's `.env` file (e.g., `/data/profiles/code_architect/.env`).
This overrides the shared `supermemory.json` for that profile only, without
breaking other profiles that rely on the `voltaic` default. Takes effect
on next session start (plugin reads env vars at `initialize()` time).

Diagnostic: if the user reports memories are "not being stored" but API
tests show HTTP 200, check which container the plugin is actually writing
to — it's probably the shared default container, not the per-profile one.

See `references/governed-memory-plugin.md` for the full plugin recipe and
`references/supermemory-runtime-tuning.md` for the JSON schema, every knob,
and the per-flag token impact analysis. For multi-tenant container tag
composition (the matrix routing pattern with `active_client.yaml`), see
`references/supermemory-matrix-routing.md`.

## Restricted Profile Security (Non-Technical Partners)

When giving a non-technical user access to Hermes (business partner, client, team member), the
core problem is blast-radius control: they can chat with the model, which means the model can
call any registered tool — including `write_file`, `patch`, and `terminal` that modify the system.

**Architecture constraint:** Hermes has **toolset-level** granularity, not per-tool. The `file`
toolset bundles `read_file`, `write_file`, `patch`, `search_files` — you cannot disable writes
while keeping reads. Same with `terminal` (all shell commands or none).

**Three-layer defense pattern** (defense-in-depth, no single point of failure):

1. **Hard block — `disabled_toolsets`**: Remove `terminal` (biggest blast radius — arbitrary shell),
   plus irrelevant toolsets (`kanban`, `discord_admin`, `spotify`, etc.). Keep `file` enabled
   because `read_file`/`search_files` are essential for context.

2. **Hard gate — `approvals.mode: always`**: Every tool call requires explicit user confirmation.
   If the model calls `write_file`, the partner sees a confirmation prompt with the file path.
   For non-technical users who can't evaluate whether a tool call is safe, this is the critical
   backstop. Trade-off: slightly annoying UX (every `read_file` and `web_search` also needs a click).

3. **Soft block — SOUL.md doctrine**: Write explicit "NEVER call write_file/patch/terminal" rules
   into the partner's `SOUL.md`. Injected into every session's system prompt. Not cryptographic,
   but highly effective when combined with Layer 2 — the model won't attempt writes in the first
   place, and if it does, Layer 2 catches it.

**Composio as sandboxed creation path**: For partners who need content creation capabilities
(social posting, analytics, image/video generation), Composio MCP tools provide external service
access without filesystem exposure. The partner can create and publish content through Composio's
API while the filesystem remains protected by the three layers above.

**Multi-client isolation**: Partner gets their own Composio `user_id` and connected accounts.
Never share an MCP URL or API key with the partner — separate Composio server per deployment.

**Memory isolation**: Partner gets their own `SUPERMEMORY_CONTAINER_TAG` in their profile `.env`.
Memory tools (`memory`, `supermemory_search`, etc.) are safe to leave enabled — they write to
the partner's isolated container and cannot access yours.

See `references/restricted-profile-security.md` for the full recipe (config template, SOUL.md
template, toolset decision matrix, pitfalls).

## Profile management (rename, list, switch)

Hermes profiles live at `$HERMES_HOME/profiles/<name>/` and each carries its
own `AGENTS.md`, `SOUL.md`, `config.yaml`, sessions, skills, and memories.
The CLI has first-class support for renaming and switching:

```bash
# List all profiles with their model + status + alias
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes profile list

# Rename — moves the directory AND updates the wrapper alias atomically
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes profile rename <old> <new>

# Launch a session under a specific profile
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes --profile <name>
# Or use the alias the rename created:
<name>
```

For testing changes across profiles from the code_architect session,
see `references/sub-profile-execution.md` — three-step verification
(boot → memory → tool test) with profile-specific recipes.

**What `profile rename` actually does** (verified by running it):
1. Moves `$HERMES_HOME/profiles/<old>/` → `$HERMES_HOME/profiles/<new>/`
2. Updates the wrapper script / alias so `<new>` launches a session in the
   renamed profile
3. Leaves the profile's `AGENTS.md` title, model config, sessions, and skills
   completely untouched — those are content, not identity

**Pitfall — the AGENTS.md title is independent of the profile name.** Renaming
the profile does NOT rewrite the `# Marketing Researcher Agent ...` header
inside `$HERMES_HOME/profiles/<name>/AGENTS.md`. Patch the file separately if
the user expects the in-doc title to match the new profile name.

## Agency-wide rules and persona: SOUL.md

For multi-tenant agency setups, multi-client isolation rules, token-conservation
doctrine, hyper-dense memory-write format, etc., write a markdown file at
`$HERMES_HOME/SOUL.md` (e.g. `/data/SOUL.md`). Hermes loads it automatically
into the system prompt as the agent identity (`agent/prompt_builder.py::load_soul_md`).

Takes effect on the **next new chat session** — current sessions keep their
already-built system prompt.

Use SOUL.md for durable doctrine (multi-client boundary rules, token discipline,
memory-write formatting standards). Use the memory provider's `system_prompt_block()`
output for plugin-state facts the model needs every turn (active container tag,
hard caps). The two compose: SOUL.md says "never mix client A and client B
vectors," the governed memory plugin says "you are talking to container X right
now."

## WebUI Workspace Configuration

The WebUI's active workspace path is stored in:

```
/data/.hermes/webui/settings.json  →  "default_workspace"
```

**Not** in `config.yaml`, not in `AGENTS.md`, not in `supermemory.json`. This is
the single source of truth for:
- The `[Workspace: /path]` tag prefixed to every user message
- The default directory the WebUI file browser shows
- The working directory the agent uses for all file operations

**To change the workspace:**
```json
{
  "default_workspace": "/data/workspace"
}
```

Use `read_file` + `patch` (or `write_file`) on `/data/.hermes/webui/settings.json`.
Takes effect on the next new session — existing sessions keep their already-built
workspace path.

**Pitfall:** `/data/home/workspace` is a legacy path created by the entrypoint's
`mkdir -p ${HERMES_HOME}/home/workspace` boot strap. If the WebUI points there
but all your actual files are in `/data/workspace`, the agent will write to the
wrong directory and the user won't see files in the dashboard. Always verify
`default_workspace` matches where your triage/, AGENTS.md, and other working
files actually live.

## Reading JS-Rendered Documentation

On this Railway deployment, `web_extract` uses SearXNG (search-only) and cannot fetch page content. When you need to read a doc URL that isn't a raw file:

1. **Try `curl` on the raw URL first** — works for GitHub raw files, plain markdown endpoints
2. **For JS-rendered sites (Mintlify, Next.js SSR):** use `curl` + regex on embedded `__next_f` data chunks

See `references/reading-js-rendered-docs.md` for the full pattern with code.

Short version:
```python
import subprocess, re
from html import unescape
html = subprocess.run(['curl', '-s', url], capture_output=True, text=True).stdout
chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL)
for chunk in chunks:
    for t in re.findall(r'children: \\\\"([^\\\\"]{3,})\\\\"', chunk):
        print(unescape(t.replace('\\\\\\\\n', '\n').replace('\\\\"', '"')))
```

## Adding MCP Servers

Hermes supports MCP (Model Context Protocol) servers via `hermes mcp`. MCP servers run as subprocesses (stdio) or over HTTP/SSE and provide additional tools.

### ⚠️ Critical pitfall: `hermes mcp add --args` eats leading dashes

`hermes mcp add <name> --command npx --args -y firecrawl-mcp` **fails** because argparse interprets `-y` as a flag and errors out. There is no workaround via CLI flags.

**Fix: write directly to `/data/config.yaml`** under the `mcp_servers` key:

```yaml
mcp_servers:
  firecrawl:
    command: npx
    args:
      - -y
      - firecrawl-mcp
    env:
      FIRECRAWL_API_KEY: <key>
```

After editing config.yaml, verify with:
```bash
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes mcp list
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes mcp test firecrawl
```

### Firecrawl MCP

Full setup: `references/firecrawl-mcp-setup.md`

Short form:
1. Write config block above to `/data/config.yaml`
2. Also add `FIRECRAWL_API_KEY=<key>` to `/data/.env`
3. Test: `hermes mcp test firecrawl` — expect "✓ Connected" and "16 tools discovered"
4. Quick scrape test: `hermes -z "Use firecrawl_scrape to get the title of https://example.com"`

### MCP Server Config Schema

| Key | Description |
|-----|-------------|
| `command` | Executable to run (e.g. `npx`, `python`) |
| `args` | List of arguments — **use YAML list format, not inline** |
| `env` | Key-value env vars injected into the subprocess |
| `url` | For HTTP/SSE transport instead of stdio |

### ⚠️ Pitfall: `patch` tool redacts secrets in YAML config

When using the `patch` tool on `/data/config.yaml` with an `old_string` that
contains an API key (e.g., the `FIRECRAWL_API_KEY` value in the `mcp_servers`
block), the tool may redact the key in the diff output — and sometimes
corrupt the in-file value by writing the literal placeholder
(e.g., `fc-f6b...9a3e`) instead of the real key.

**Root cause:** the tool's secret-scanning pass treats the key in the diff as
a secret to redact, and the redaction can bleed into the file write.

**Fix: use `execute_code` for YAML config patches that touch secret values.**
```python
# Read file, do in-memory replace, write back
with open('/data/config.yaml') as f:
    content = f.read()
content = content.replace('fc-f6b...9a3e', real_key)
with open('/data/config.yaml', 'w') as f:
    f.write(content)
```
Double-check with `search_files` after: confirm the placeholder string is gone
and the key length matches the real key from `.env`.

**Alternate fix:** use `write_file` to rewrite the entire file (safer, but
requires knowing the full content). Avoid `patch` entirely for config
sections that contain bearer tokens, API keys, or other secrets.

## Camofox Anti-Detection Browser

Camofox is a self-hosted Firefox-based anti-detection browser server. When
`CAMOFOX_URL` is set, **all Hermes browser tools route through it automatically**
instead of Browserbase or local agent-browser. Best for social media feeds,
sites with bot detection, and tasks needing persistent logins.

See `references/camofox-railway-setup.md` for full deployment steps.
For multi-profile coordination architecture (profile filesystem layout, Kanban
as coordination primitive, Supermemory cross-profile sharing, task dispatch
contracts, Railway volume constraints), see `references/multi-profile-architecture.md`.
For the complete recipe to bootstrap a git repo from a bare `/opt/hermes-railway/`
and wire profile sync into the entrypoint (init, PAT push, config modernization
across versions, FIRECRAWL_API_KEY stripping, .gitignore, verification),
see `references/git-repo-bootstrap-with-profiles.md`.
For the partner onboarding flow (required API keys, Railway env vars, deployment
prerequisites, what your fork must contain before a partner can deploy),
see `references/partner-deployment-checklist.md`.
For sharing profile files via GitHub while preserving the partner's personalized
SOUL.md, AGENTS.md, and USER.md (three merge strategies: exclude-from-ownership,
_templates/, local/ overlay), see `references/profile-distribution-sync.md`.

### Quick setup (Railway)

1. New service → GitHub repo `jo-inc/camofox-browser` → **branch: `master`** (not `main`)
2. Railway auto-detects `railway.toml` and uses `Dockerfile.ci` (downloads binary at build time)
3. On the Camofox service set: `PORT=9377`, optionally `MAX_OLD_SPACE_SIZE=512`
4. Add a **Railway Volume** mounted at `/root/.camofox` for session persistence
5. Wire into Hermes: `echo 'CAMOFOX_URL=http://camofox-browser.railway.internal:9377' >> /data/.env`
6. Enable persistent logins in `/data/config.yaml`:
   ```yaml
   browser:
     camofox:
       managed_persistence: true
   ```

### ⚠️ Critical pitfall: branch is `master` not `main`
Railway defaults to `main` when connecting a GitHub repo. `jo-inc/camofox-browser`
uses `master`. Change the branch in Railway → Service → Settings → Source before
deploying or the build fails immediately with "Branch 'main' not found".

### Health check
```bash
timeout 10 curl -s "http://camofox-browser.railway.internal:9377/health"
# Expected: {"ok":true,"engine":"camoufox","browserConnected":true,...}
```

### Camofox API basics (direct calls)
The browser tools call this automatically, but useful for testing:
```bash
# Create a tab
curl -X POST "http://camofox-browser.railway.internal:9377/tabs" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "userId": "hermes-default", "sessionKey": "test"}'

# Snapshot (userId required)
curl "http://camofox-browser.railway.internal:9377/tabs/<tabId>/snapshot?userId=hermes-default"

# Screenshot
curl "http://camofox-browser.railway.internal:9377/tabs/<tabId>/screenshot?userId=hermes-default" -o shot.png

# Delete tab
curl -X DELETE "http://camofox-browser.railway.internal:9377/tabs/<tabId>?userId=hermes-default"
```

### Private URL pattern
Follows the same Railway private networking convention as SearXNG:
`http://<service-name>.railway.internal:<PORT>`

The service name in Railway is `camofox-browser` → `http://camofox-browser.railway.internal:9377`

## Monkey-patching baked Hermes modules (sitecustomize.py override)

`/opt/hermes/` and its venv are root-owned and read-only — you can't edit
`/opt/hermes/tools/lazy_deps.py`, `/opt/hermes/run_agent.py`, or anything else
baked into the image. But `/opt/hermes-railway/` is **hermes-owned, earlier in
PYTHONPATH, and Python auto-loads `sitecustomize.py` from any sys.path entry
at startup**. That gives you a write-anywhere override hook into every Python
process Hermes spawns, without rebuilding the image.

**When to reach for this:** any time a baked module has a stale constant,
pin, or default that you can't change from config — and reaching for a
Dockerfile rebuild would be overkill.

Canonical example (already deployed): `lazy_deps.LAZY_DEPS['search.firecrawl']`
was pinned to `firecrawl-py==4.17.0`, but `/opt/hermes-railway/` ships 4.27.1.
`_is_satisfied()` saw the version mismatch, tried to downgrade-install into
the root-owned venv, and broke `web_search` / `web_extract`.

Live file: `/opt/hermes-railway/sitecustomize.py` — rewrites the pin to
`4.27.1` at import time. See `references/sitecustomize-override-pattern.md`
for the full recipe (template, verification command, pitfalls,
when-to-prefer-this-over-Dockerfile).

**Pitfall — don't make this the default fix.** sitecustomize hooks are
invisible to anyone reading the baked tree and survive across redeploys via
the persistent `/opt/hermes-railway/` volume. Use it for surgical pin/constant
overrides; use the Dockerfile for anything structural.

**Pitfall — never write "tool X is broken" into the SKILL.md or memory based
on a lazy-install failure.** The fix is always a writable override path
(sitecustomize, copy-to-hermes-railway, MCP route). Capture the fix, not the
negative claim.

## Nous Portal Setup (OAuth on Headless Containers)

Nous Portal is Nous Research's unified inference provider — one OAuth login gives
access to 300+ models (Claude, GPT, Gemini, DeepSeek, Qwen, etc.) plus a Tool
Gateway (web search, image gen, TTS, browser automation). All billed against a
single Nous subscription.

### First-time login (headless Railway container)

No local browser available — use `--no-browser` for device code flow:

```bash
# Start OAuth — produces a URL + device code
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes auth add nous --type oauth --no-browser
```

Output:
```
To continue:
  1. Open: https://portal.nousresearch.com/manage-subscription?user_code=XXXX-XXXX
  2. If prompted, enter code: XXXX-XXXX
Waiting for approval (polling every 1s)...
```

The user opens the URL in their own browser, signs in, and authorizes the device.
The CLI auto-detects approval and stores the token. **Auth is global** — one login
covers all profiles (stored in `~/.hermes/` or the Hermes home credential store).

### Alternative: `hermes model` (interactive provider + model picker)

```bash
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes model
# → pick "Nous Portal" from the list → triggers same OAuth flow
```

Use `hermes model` when setting up for the first time (picks provider AND model).
Use `hermes auth add nous` when you just need to authenticate.

### Checking portal status and tools

```bash
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes portal status
# Auth state, sign-up link, current model, Tool Gateway status

HERMES_HOME=/data /opt/hermes/.venv/bin/hermes portal tools
# Tool Gateway catalog: web search, image gen, TTS, browser, cloud terminal
```

⚠️ The subcommands are `status`, `open`, `tools` — NOT `info`. Running
`hermes portal info` errors with "invalid choice: 'info'".

### Viewing available models

`hermes model` is an **interactive PTY picker** — two screens: (1) select provider,
(2) select model. Cannot be driven non-interactively. To inspect without changing:

```bash
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes model
# → pick provider → see model list → pick "Skip (keep current)" to exit unchanged
```

Models are split into **free** (available on any account) and **paid** (requires
subscription upgrade). Free models have `:free` suffix. Paid models are listed but
shown as "Unavailable" until upgraded at https://portal.nousresearch.com.

For the full model catalog with pricing, see `references/nous-portal-models.md`.

**Pitfall — the interactive picker changes config on selection.** If you select a
provider but don't want to change the model, pick "Skip (keep current)" (option 4
on the model screen). Simply killing the process after selecting a provider may
leave config in an intermediate state.

### Multi-profile provider migration

After authenticating once, set the model and provider on each profile:

```bash
# For each profile:
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes config set model.provider nous
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes config set model.default <model-name>

# For named profiles:
HERMES_HOME=/data/profiles/<name> /opt/hermes/.venv/bin/hermes config set model.provider nous
HERMES_HOME=/data/profiles/<name> /opt/hermes/.venv/bin/hermes config set model.default <model-name>
```

**Auth is shared** (one login = all profiles). **Model selection is per-profile** (each
profile's `config.yaml` has its own `model.default`). Verify with:

```bash
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes profile list
# Shows each profile's current model
```

### Verification after provider switch

```bash
# 1. Confirm auth
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes portal status

# 2. Confirm model per profile
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes profile list

# 3. Quick inference test
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes -z "Say hello in one word."

# 4. Per-profile test
HERMES_HOME=/data/profiles/<name> /opt/hermes/.venv/bin/hermes -z "Say hello in one word."
```

## Enabling the Gateway (for Cron Jobs)

The gateway is a messaging platform daemon that also runs the cron scheduler ticker. It's disabled by default (`START_GATEWAY=false` in the entrypoint) because it retries unconfigured platforms on startup.

**When to enable:** whenever you need cron jobs to fire automatically. The cron ticker calls `scheduler.tick()` every 60 seconds — without the gateway, jobs are written to `jobs.json` but never execute.

```bash
# Set in Railway service env vars, then redeploy
START_GATEWAY=true
```

**What happens on startup with no messaging platforms configured:**
- Gateway starts, logs warnings about failed platform connections
- Cron ticker starts as a daemon thread (60s interval)
- `hermes cron status` shows running scheduler

**If you only need cron (no messaging platforms):** the gateway handles this gracefully. Failed platform connections are retried in the background but don't block the cron ticker.

**Pitfall — platform config sections trigger auto-detection.** Even without a bot token, having a `discord:` (or `telegram:`, `slack:`, etc.) section in config.yaml with default values causes the gateway to attempt connection and retry every 60 seconds. Remove unused platform sections from all profile configs to stop the spam. Use Python via terminal (not `patch`, which is blocked on protected configs) to safely edit config.yaml.

For full debugging reference (script path semantics, deliver modes, output locations, timezone gotchas), see the `cron-scheduling` skill → `references/cron-gateway-debugging.md`.

## Skills Curator (Lifecycle Maintenance)

The curator manages agent-created skills: tracks usage, identifies stale skills, proposes consolidation into class-level umbrellas, and archives unused ones.

**Binary:** `/opt/hermes/.venv/bin/hermes curator <verb>`

### Operational Workflow

```
1. Status check    →  hermes curator status     (see run_count, last_run, skills breakdown)
2. Dry-run         →  hermes curator run --dry-run  (LLM proposes consolidations, no mutations)
3. Review report   →  read /data/logs/curator/<timestamp>/REPORT.md
4. Live run        →  hermes curator run         (applies consolidations + archives)
```

### Profile Scope

All profiles (default, code_architect, researcher, social_media) share the skills directory at `/data/skills/`. Running the curator once against the default profile covers all profiles. No per-profile curator run needed.

### Key Flags

| Verb | What it does |
|------|-------------|
| `status` | Shows enabled/disabled, run_count, interval, stale/archive thresholds, most/least active skills |
| `run --dry-run` | LLM pass proposes consolidations and archives — writes report, makes zero mutations |
| `run` | Applies proposed changes: creates umbrella skills, archives absorbed originals, writes tar.gz backup |
| `restore <name>` | Recovers an archived skill from `~/.hermes/skills/.archive/` |
| `pin <name>` | Protects a skill from auto-archive/consolidation (still patchable) |
| `unpin <name>` | Removes pin protection |
| `backup` | Manual tar.gz backup of current skills state |
| `rollback` | Restore from last backup |

### Config Defaults

```yaml
curator:
  enabled: true
  interval_hours: 168    # 7 days
  min_idle_hours: 720    # 30 days unused → stale
  stale_after_days: 30
  archive_after_days: 90
```

### Safety Properties

- **Only touches agent-created skills** (`created_by: "agent"` in frontmatter). Bundled and hub-installed skills are off-limits.
- **Never deletes** — max destructive action is archive. All originals recoverable via `restore`.
- **Pre-run backup** — tar.gz snapshot before every live run. `rollback` undoes the last run.
- **Pinned skills exempt** — pin blocks archive/consolidation but not content patches.
- **Telemetry** at `/data/skills/.usage.json` tracks `use_count`, `view_count`, `patch_count`, `last_activity_at` per skill.

### Consolidation Output

Reports land at `/data/logs/curator/<timestamp>/REPORT.md` with a `run.json` machine-readable sidecar. The report lists:
- Auto-transitions (time-based stale marking)
- LLM consolidation pass (umbrella merges) with per-cluster rationale
- Prunings (archives) with absorbed_into target
- Skills left alone with justification

### Typical First Run

On a fresh deployment the curator seeds its state file (`/data/skills/.curator_state`) but defers the first run until one interval elapses. To run immediately:

```bash
/opt/hermes/.venv/bin/hermes curator run --dry-run   # preview
# review /data/logs/curator/<timestamp>/REPORT.md
/opt/hermes/.venv/bin/hermes curator run              # apply
```

### ⚠️ Critical: LLM Pass Can Only Absorb, Not Create Umbrellas

The curator's LLM consolidation pass can **absorb one skill into an existing skill** (e.g., merge `hermes-profile-auth` into `hermes-model-debugging`), but it **cannot create new umbrella skills**. When the dry-run proposes clusters like `ai-coding-agents` or `software-development-workflows`, the live run will NOT create those umbrellas — it will only perform simple absorptions between existing skills.

**The practical workflow for consolidation:**

```
1. hermes curator run --dry-run          # get LLM cluster proposals
2. Read REPORT.md for the consolidation plan
3. hermes curator run                    # apply what the LLM can (absorptions only)
4. Check run.json → consolidated[]       # see what ACTUALLY happened (not the narrative)
5. For each remaining cluster:
   a. delegate_task to create the umbrella SKILL.md
   b. hermes curator archive <source> for each absorbed skill
   c. Verify: hermes skills list | grep <umbrella-name>
```

**Do NOT trust the LLM narrative summary** in `last_run_summary` or the REPORT.md prose. The LLM describes actions it *intended* but only structured YAML in `run.json` reflects what actually executed. Example: a run claimed "archived 12 skills" but `run.json.consolidated` showed only 2 real absorptions — the other 10 were LLM hallucination in the summary.

**Recovery from partial state:** if the curator archives skills without creating their intended umbrellas, `hermes curator restore <name>` recovers each one individually. Then manually apply the umbrella creation via delegate_task.

### `hermes curator archive` Flags

The archive command takes only the skill name — there is **no `--absorbed-into` flag** in this version:

```bash
/opt/hermes/.venv/bin/hermes curator archive <skill-name>
# Moves to /data/skills/.archive/<skill-name>/
# No --absorbed-into option available
```

### Monitoring Ongoing Health

```bash
# Quick status
/opt/hermes/.venv/bin/hermes curator status

# Check if any skills are stale or archived
/opt/hermes/.venv/bin/hermes curator status | grep -E "stale|archived"

# View usage telemetry
cat /data/skills/.usage.json | python3 -m json.tool | head -40
```

## Hermes Config Commands

```bash
# Set any config key
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes config set <key> <value>

# Check memory status
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes memory status

# List plugins
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes plugins list

# MCP management
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes mcp list
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes mcp test <name>
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes mcp remove <name>
```