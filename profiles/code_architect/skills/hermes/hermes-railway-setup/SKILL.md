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

**Pitfall — don't blame the SOUL.md or system_prompt_block first.** Both are
small, static, and identical every turn. The `<supermemory-context>` block is
the only thing that grows turn-over-turn, and it doesn't show up in any
`hermes config` output — only in the actual prompt sent to the model. Check
`$HERMES_HOME/<provider>.json` first.

See `references/governed-memory-plugin.md` for the full plugin recipe and
`references/supermemory-runtime-tuning.md` for the JSON schema, every knob,
and the per-flag token impact analysis. For multi-tenant container tag
composition (the matrix routing pattern with `active_client.yaml`), see
`references/supermemory-matrix-routing.md`.

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