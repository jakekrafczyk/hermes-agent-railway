# Git Repo Bootstrap + Profile Sync on Railway

Full recipe: turn a bare `/opt/hermes-railway/` (no `.git` — copied at build time)
into a GitHub-connected repo with profile configs synced on every boot.

## Why the repo has no `.git`

`/opt/hermes-railway/` is a bare copy of the template, not a clone. The entrypoint
copies code in at build time; `.git` is excluded. You must `git init` from scratch.

## Step 1 — Init repo from live code

```bash
cd /opt/hermes-railway
git init
git checkout -b main
git config user.email "your@email.com"
git config user.name "Your Name"
git add -A
git commit -m "Initial commit: snapshot of running Railway instance"
```

**Pitfall:** `git commit` fails with "Author identity unknown" if `user.email` and
`user.name` aren't set. Set them at repo level (`git config`) to avoid polluting
global gitconfig.

## Step 2 — Connect to GitHub fork and force-push

PAT format for git remote URL:

```
https://<PAT>@github.com/<username>/<repo>.git
```

```bash
git remote add origin "https://<PAT>@github.com/<username>/hermes-agent-railway.git"
git push -u origin main --force
```

Use `--force` because the fork may have an initial commit from GitHub's fork
process — the live state wins.

**Security:** The PAT only needs `Contents: Read+Write` scope. Use a fine-grained
token, not a classic PAT. The token appears in the git remote URL — after push,
the remote URL in `.git/config` contains it. The `.git/` directory is on the
persistent volume; Railway env vars don't touch it. Acceptable for an agent-owned
repo.

## Step 3 — Add profiles/ directory

```bash
mkdir -p /opt/hermes-railway/profiles/default
mkdir -p /opt/hermes-railway/profiles/researcher
```

### 3a — Default profile config (orchestrator)

Copy from `/data/config.yaml` but **upgrade from config_version 5 to modern
structure** (use researcher's v23 config as reference). Key customizations for
the orchestrator role:

| Setting | Value | Reason |
|---------|-------|--------|
| `agent.reasoning_effort` | `low` | Orchestrator coordinates, doesn't research |
| `delegation.model` | `deepseek/deepseek-v4-pro` | Keep main model, not anthropic |
| `delegation.provider` | `openrouter` | Same provider as main |
| `browser.camofox.user_id` | `default` | Separate from researcher's Camofox sessions |
| `browser.camofox.session_key` | `default-session` | |
| `kanban.orchestrator_profile` | `default` | Self-reference for Kanban dispatch |
| `kanban.dispatch_in_gateway` | `true` | |
| `cron.wrap_response` | `true` | Orchestrator runs cron jobs |

Sections to **include** that aren't in the old v5 config:
- `security:` block (from researcher)
- `code_execution:` block
- `logging:` block
- `model_catalog:` block
- `network:` block
- `sessions:` block
- `onboarding:` block
- `updates:` block
- `lsp:` block
- `x_search:` block
- `secrets:` block

Sections to **add** that researcher doesn't have:
- `kanban:` block (orchestrator-only)
- `cron:` block (orchestrator-only)
- `curator:` block with `backup.enabled: true`
- `auxiliary.session_search:` (orchestrator uses session_search)

**Strip:** `_config_version` — Hermes upgrades it on next run. **Strip:**
`mcp_servers.firecrawl.env.FIRECRAWL_API_KEY` → replace with `__FIRECRAWL_API_KEY__`.

### 3b — Researcher profile config

Copy `/data/profiles/researcher/config.yaml` as-is, then:
- Replace `FIRECRAWL_API_KEY: fc-f6b...` with `__FIRECRAWL_API_KEY__`
- Keep `_config_version` if present (unlike default, prompt doesn't require stripping)

### 3c — profiles/.gitignore

```
*.env
*.lock
auth.lock
auth.json
cache/
sessions/
models_dev_cache.json
webui_state/
browser_screenshots/
memories/
.usage.json
```

This blocks secrets and runtime state from being committed.

## Step 4 — Insert profile sync into entrypoint.sh

**Critical ordering:** insert the profile sync block **IMMEDIATELY BEFORE** the
skills sync block (around line 216). Do NOT place it after — the entrypoint flow
is sequential and skills may depend on profile state.

```bash
# Sync bundled profiles into /data/ on every boot.
if [ -d "/opt/hermes-railway/profiles" ]; then
  for profile_dir in /opt/hermes-railway/profiles/*/; do
    [ -d "${profile_dir}" ] || continue
    profile_name="$(basename "${profile_dir}")"
    [ "${profile_name}" = ".gitignore" ] && continue
    if [ "${profile_name}" = "default" ]; then
      cp -R "${profile_dir}"/* "${HERMES_HOME}/"
      echo "Synced profile: default (→ HERMES_HOME)"
    else
      mkdir -p "${HERMES_HOME}/profiles/${profile_name}"
      cp -R "${profile_dir}"/* "${HERMES_HOME}/profiles/${profile_name}/"
      echo "Synced profile: ${profile_name}"
    fi
  done
fi
```

Key behaviors:
- "default" profile syncs to `HERMES_HOME` itself (`/data/`) — overwrites
  `config.yaml`, `SOUL.md`, `AGENTS.md` at root
- Named profiles sync to `HERMES_HOME/profiles/<name>/`
- `.gitignore` is skipped (it's a file in `profiles/`, not a profile dir)
- First sync on existing install is a no-op (files match)

## Step 5 — Commit and push

```bash
cd /opt/hermes-railway
git add profiles/ entrypoint.sh
git commit -m "Add profile configs for default (orchestrator) and researcher, entrypoint syncs profiles on boot"
git push origin main
```

## Step 6 — Verify

1. `git remote -v` → points to your fork
2. `git log --oneline -3` → shows initial commit + profile commit
3. Open repo on GitHub → verify `profiles/default/config.yaml`,
   `profiles/researcher/config.yaml`, and updated `entrypoint.sh` are visible
4. **Secret scan:** `grep -r "FIRECRAWL_API_KEY" profiles/` → all values must be
   `__FIRECRAWL_API_KEY__`, never a real key
5. `find profiles/ -name "*.env" -o -name "auth.*"` → must return nothing

## Railway Auto-Deploy

Push to `main` triggers auto-deploy. On next container boot, the entrypoint
syncs profiles into `/data/`. Existing `/data/profiles/` files are overwritten
on sync — ensure committed configs match what's currently running before pushing.

If auto-deploy doesn't trigger: Railway → service → CMD+K → Deploy Latest Commit.

## Pitfalls

### Missing build-time files after `git init` from container

`/opt/hermes-railway/` in the running container contains ONLY runtime artifacts
(`admin/`, `entrypoint.sh`, `skills/`). Build-time files — `Dockerfile`,
`railway.json`, `.env.example`, `docker-compose.yml` — exist in the protemplate
GitHub repo but were never copied into the Docker image. `git init` + `git add -A`
from the container will NOT include them.

**Without these files, a fresh Railway deploy from the fork will fail** — there's no
Dockerfile to build from and no `railway.json` to guide Railway's build system.

**The full missing-file list (5 files, not just 3):** `Dockerfile`, `railway.json`,
`.env.example`, `.gitignore`, `.dockerignore`. The `.gitignore` and `.dockerignore`
are excluded from the Docker image; without them, `git add` picks up build
artifacts and the Docker context gets bloated.

**Fix:** after `git init` and before pushing, fetch all 5 missing files from the
upstream raw URLs, patch the Dockerfile for profiles, then commit:

```bash
cd /opt/hermes-railway
BASE="https://raw.githubusercontent.com/protemplate/hermes-agent-railway/main"
curl -sL "$BASE/Dockerfile" -o Dockerfile
curl -sL "$BASE/railway.json" -o railway.json
curl -sL "$BASE/.env.example" -o .env.example
curl -sL "$BASE/.gitignore" -o .gitignore
curl -sL "$BASE/.dockerignore" -o .dockerignore

# ⚠️ Critical: the upstream Dockerfile only COPYs admin/, skills/, entrypoint.sh.
# Add the profiles/ COPY line so profile configs land in the image:
#   COPY profiles ./profiles
# Insert it between the skills and entrypoint COPY lines.
patch Dockerfile with:
  old: "COPY skills ./skills\nCOPY entrypoint.sh ./entrypoint.sh"
  new: "COPY skills ./skills\nCOPY profiles ./profiles\nCOPY entrypoint.sh ./entrypoint.sh"

git add -f Dockerfile railway.json .env.example .gitignore .dockerignore
git commit -m "Add build-time files from upstream protemplate, Dockerfile copies profiles/"
```

**Verification after fetch:**
```bash
ls -la /opt/hermes-railway/{Dockerfile,railway.json,.env.example,.gitignore,.dockerignore}
# All five must exist and be non-zero
grep "COPY profiles" /opt/hermes-railway/Dockerfile
# Must print: COPY profiles ./profiles
```

**`git add -f` may be needed** because Docker images sometimes include build
filenames in a root `.gitignore`. Regular `git add` can silently skip them.

### Partner deployment flow depends on these files

Your partner deploys by forking YOUR populated repo (with profiles, Dockerfile,
railway.json). They create a new Railway project, link to their fork, and Railway
reads `railway.json` to build from `Dockerfile`. On first boot, the entrypoint
syncs profiles from `/opt/hermes-railway/profiles/` into `/data/profiles/`.

If Dockerfile/railway.json are missing from your fork, the partner's deploy
fails. Verify your fork on GitHub has ALL of: `Dockerfile`, `railway.json`,
`.env.example`, `entrypoint.sh`, `admin/`, `skills/`, `profiles/`.
