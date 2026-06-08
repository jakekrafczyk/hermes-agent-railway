# Profile Distribution Sync: Partner Merge Strategies

How to share Hermes profile files via a shared GitHub repo, where both you and a
partner run separate Railway instances from the same repo. The partner needs to
receive automatic updates to shared files but keep their personalized SOUL.md,
AGENTS.md, and USER.md intact across every deploy.

## The Railway Entrypoint Problem

The Railway entrypoint (`entrypoint.sh`) already syncs profile files on every boot:

```bash
# Lines ~222-235 of entrypoint.sh
if [ -d "/opt/hermes-railway/profiles" ]; then
  for profile_dir in /opt/hermes-railway/profiles/*/; do
    if [ "${profile_name}" = "default" ]; then
      cp -R "${profile_dir}"/* "${HERMES_HOME}/"  # ← BLIND OVERWRITE
    fi
  done
fi
```

This copies everything from `profiles/default/` in the git repo directly to
`/data/` on every deploy. The Dockerfile copies the git repo into
`/opt/hermes-railway/`, so any file in the repo's `profiles/default/` lands on
both instances. Files are distributed via the git repo, NOT via `hermes profile
install` or `hermes profile update`.

**The consequence:** the partner's customized SOUL.md, AGENTS.md, and config.yaml
get wiped on every Railway deploy. The `local/` overlay pattern solves this by
running a merge script AFTER the entrypoint's `cp -R` sync.

## File Inventory

| File | Syncs on deploy? | Personalized? |
|------|-----------------|---------------|
| `SOUL.md` | ✅ (overwrites) | ✅ High |
| `AGENTS.md` | ✅ (overwrites) | ✅ High |
| `config.yaml` | ✅ (overwrites) | ⚠️ Model/provider/paths |
| `skills/` | ✅ | ❌ |
| `reference/` | ✅ | ❌ |
| `scripts/` | ✅ | ❌ |
| `plugins/` | ✅ (if in profiles/default/) | ❌ (manual install) |
| `.env` | ❌ (gitignored) | N/A (secrets) |
| `auth.json` | ❌ (gitignored) | N/A (secrets) |
| `state.db*` | ❌ (gitignored) | N/A (runtime) |
| `memories/` | ❌ (gitignored) | ❌ (auto-generated) |
| `local/` | ❌ (volume-only) | ✅ Partner overrides live here |

## Three Approaches

### Option 1: Exclude SOUL.md/AGENTS.md from Sync

Don't include SOUL.md/AGENTS.md in the repo's `profiles/default/` at all. These
files install once, never update. Partner merges changes manually.

| Pros | Cons |
|------|------|
| Zero scripts needed | Partner must manually merge every doctrine change |
| Cannot accidentally overwrite | Partner may miss important updates |

**Best if:** SOUL.md/AGENTS.md changes are rare (monthly or less).

### Option 2: `_templates/` Directory

Put canonical files in `profiles/default/_templates/` (synced every deploy).
Root-level files are the partner's personal copies (never in repo, live on
volume only). Partner diffs templates against their copies and merges manually.

| Pros | Cons |
|------|------|
| Partner sees exactly what changed via `diff` | Still manual merge |
| Canonical version always available | Two copies to reconcile |

**Best if:** Changes are moderate (weekly-ish) and partner wants change visibility.

### Option 3: `local/` Overlay — Recommended

`local/` lives ONLY on the persistent volume (`/data/local/`), never in the
repo. A merge script appended to the entrypoint runs after every `cp -R` sync,
applying the partner's `local/` overrides on top of the freshly-synced
distribution files.

**Repo structure** (`profiles/default/` — synced to `/data/` on every deploy):

```
profiles/default/
├── SOUL.md                 ← your canonical shared doctrine
├── AGENTS.md               ← your canonical shared config
├── config.yaml             ← shared base (overwritten on every deploy)
├── supermemory.json        ← shared memory settings
├── reference/              ← hermes_llms.txt, supermemory_llms.txt
├── scripts/
│   └── merge-local.sh      ← merges /data/local/ overrides post-sync
├── plugins/
│   └── supermemory_governed/  ← installed once, not overwritten
└── skills/                 ← all bundled skills
```

**Partner's volume** (`/data/local/` — NEVER in repo, NEVER overwritten):

```
/data/local/
├── SOUL.md                 ← partner's business context (appended)
├── AGENTS.md               ← partner's personal overrides (appended)
├── config.patch.yaml       ← partner's model/provider/path overrides (deep-merged)
└── USER.md                 ← partner's user profile facts
```

**merge-local.sh** (saved at `profiles/default/scripts/merge-local.sh`):

```bash
#!/bin/bash
# Merge partner's local/ overrides into distribution files.
# Runs AFTER entrypoint's cp -R sync on every Railway deploy.
# /data/local/ lives on the persistent volume — never in the git repo.

set -euo pipefail
LOCAL_DIR="${HERMES_HOME:-/data}/local"
[ -d "${LOCAL_DIR}" ] || exit 0
cd "${HERMES_HOME:-/data}"

# Append SOUL.md
if [ -f "${LOCAL_DIR}/SOUL.md" ] && [ -s "${LOCAL_DIR}/SOUL.md" ]; then
    printf '\n\n# Partner Business Context\n' >> SOUL.md
    cat "${LOCAL_DIR}/SOUL.md" >> SOUL.md
    echo "[merge-local] appended local/SOUL.md"
fi

# Append AGENTS.md
if [ -f "${LOCAL_DIR}/AGENTS.md" ] && [ -s "${LOCAL_DIR}/AGENTS.md" ]; then
    printf '\n\n# Partner Overrides\n' >> AGENTS.md
    cat "${LOCAL_DIR}/AGENTS.md" >> AGENTS.md
    echo "[merge-local] appended local/AGENTS.md"
fi

# Deep-merge config.yaml (partner overrides win)
if [ -f "${LOCAL_DIR}/config.patch.yaml" ] && [ -s "${LOCAL_DIR}/config.patch.yaml" ]; then
    python3 - <<PY
import yaml
with open('config.yaml') as f:
    base = yaml.safe_load(f) or {}
with open('${LOCAL_DIR}/config.patch.yaml') as f:
    patch = yaml.safe_load(f) or {}
def deep_merge(b, p):
    for k, v in p.items():
        if k in b and isinstance(b[k], dict) and isinstance(v, dict):
            deep_merge(b[k], v)
        else:
            b[k] = v
    return b
merged = deep_merge(base, patch)
with open('config.yaml', 'w') as f:
    yaml.safe_dump(merged, f, sort_keys=False)
PY
    echo "[merge-local] deep-merged local/config.patch.yaml"
fi
```

**Entrypoint modification** — add AFTER the existing profile sync block (after line ~235 of `entrypoint.sh`):

```bash
# Merge partner's local/ overrides into distribution files
if [ -f "${HERMES_HOME}/scripts/merge-local.sh" ]; then
  echo "Applying local overrides from ${HERMES_HOME}/local/..."
  bash "${HERMES_HOME}/scripts/merge-local.sh"
fi
```

| Pros | Cons |
|------|------|
| Fully automatic on every Railway deploy | merge-local.sh must be wired into entrypoint |
| Shared doctrine + personal context coexist | Ordering matters (shared then personal) |
| Partner never touches distribution files | config.patch.yaml deep merge requires yaml lib |
| Set once, works forever across all `git push` deploys | Script is a convention, not Hermes-built-in |

## Config.yaml: Overwrite, Then Merge

Unlike `hermes profile update` (which preserves config.yaml by default), the
Railway entrypoint's `cp -R` does a **blind overwrite**. This means:

- The partner's `config.yaml` is replaced with the repo version on EVERY deploy
- The `local/config.patch.yaml` deep-merge runs AFTER the overwrite
- Partner puts ONLY their differences in `config.patch.yaml` (model, provider, paths)
- Everything else comes from the shared repo config

Example `local/config.patch.yaml`:
```yaml
model:
  provider: nous
  default: anthropic/claude-sonnet-4
terminal:
  cwd: /data/partner-workspace
```

## Plugin Handling

Plugins at `/data/plugins/` are at the Hermes root level, not inside a profile
directory. They are NOT part of profile distributions and are NOT automatically
synced. For the `supermemory_governed` plugin:

1. Include it in the repo: `profiles/default/plugins/supermemory_governed/`
2. The entrypoint's `cp -R` syncs it to `/data/plugins/` on every deploy
3. Python dependency installed ONCE per deployment: `pip install supermemory` → copy to `/opt/hermes-railway/`

The plugin at `/data/plugins/` persists between deploys on the volume, but
including it in the repo guarantees new deployments can bootstrap.

## Partner One-Time Setup (5 minutes)

```bash
# 1. Create local/ directory on the persistent volume
mkdir -p /data/local/

# 2. Move partner's business-specific content from current /data/SOUL.md
#    into /data/local/SOUL.md. ONLY business context — company, clients,
#    domain knowledge, role preferences. Do NOT include shared doctrine.

# 3. Create config overrides (only what differs from shared config)
cat > /data/local/config.patch.yaml <<'EOF'
model:
  provider: nous
  default: <partner's-model>
EOF

# 4. Validate the merge works
bash /data/scripts/merge-local.sh
head -30 /data/SOUL.md      # should show shared doctrine
tail -10 /data/SOUL.md       # should show partner's business context
grep "provider:" /data/config.yaml  # should show partner's provider

# 5. Restart Hermes (or wait for next Railway deploy)
```

## Partner Validation Checklist

After setup, verify on the partner's instance:

```bash
# A. Confirm local/ exists with content
ls -la /data/local/SOUL.md /data/local/config.patch.yaml

# B. Dry-run the merge
bash /data/scripts/merge-local.sh

# C. Verify SOUL.md has both sections
grep -c "Partner Business Context" /data/SOUL.md  # expect: 1
wc -l /data/SOUL.md  # should be > repo SOUL.md line count

# D. Verify config merge
python3 -c "import yaml; print(yaml.safe_load(open('/data/config.yaml')).get('model',{}).get('provider'))"
# Should show partner's provider, not the repo default

# E. One-shot Hermes test
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes -z "What is your role and who are your clients?"
# Should mention both shared doctrine AND partner's business context
```

## Pre-Setup Diagnostic: `terminal.cwd` Misconfiguration

The most common cause of "partner's files are missing from /data/" is a
misconfigured `terminal.cwd` in `config.yaml`. If set to `/data/workspace`,
Hermes writes SOUL.md, AGENTS.md, and other working files there instead of to
`/data/`. The entrypoint syncs `profiles/default/*` → `/data/`, but Hermes
never reads those files because it's looking in the workspace.

**Symptoms:**
- `/data/SOUL.md` is a 536-byte stock default (not partner's custom version)
- `/data/AGENTS.md` is missing entirely
- Partner's real SOUL.md (8K+), AGENTS.md (20K+), and USER.md (18K+) are in `/data/workspace/`
- `config.yaml` shows: `terminal:\n  cwd: /data/workspace`

**Fix (run on partner's instance):**
```bash
# 1. Fix the cwd so future sessions use /data
sed -i 's|cwd: /data/workspace|cwd: /data|' /data/config.yaml
echo "Fixed: $(grep 'cwd:' /data/config.yaml)"

# 2. Move the partner's real files from workspace to /data
cp /data/workspace/SOUL.md /data/SOUL.md
cp /data/workspace/AGENTS.md /data/AGENTS.md
echo "Moved: SOUL.md ($(wc -c < /data/SOUL.md) bytes), AGENTS.md ($(wc -c < /data/AGENTS.md) bytes)"
```

After this fix, proceed to the one-time setup below. The partner's files are now
at the correct paths for the entrypoint sync to merge against.

## Partner Assessment Script (Phase 1 — Read-Only)

Before ANY changes on the partner's instance, run this read-only snapshot to
back up their current customized files. Run directly on the partner's Railway
instance (SSH or Railway dashboard terminal):

```bash
# === Create timestamped backup ===
mkdir -p /data/setup_backup/$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=$(ls -td /data/setup_backup/*/ | head -1)
echo "Backup dir: $BACKUP_DIR"

# === Snapshot all customizable files ===
for f in SOUL.md AGENTS.md config.yaml supermemory.json; do
  if [ -f "/data/$f" ]; then
    cp /data/$f "$BACKUP_DIR/$f"
    echo "Saved: $f ($(wc -c < /data/$f) bytes)"
  else
    echo "MISSING: $f"
  fi
done

# === Snapshot env vars (masked) ===
env | sort > "$BACKUP_DIR/environment.txt"

# === Full inventory ===
echo "" && echo "=== PLUGINS ===" && ls /data/plugins/ 2>/dev/null || echo "none"
echo "=== SCRIPTS ===" && ls /data/scripts/ 2>/dev/null || echo "none"
echo "=== REFERENCE ===" && ls /data/system/reference/ 2>/dev/null || echo "none"
echo "=== PROFILES ===" && ls -d /data/profiles/*/ 2>/dev/null || echo "none"
echo "=== LOCAL DIR ===" && ls -la /data/local/ 2>/dev/null || echo "none"
echo "=== SKILLS ===" && ls /data/skills/ 2>/dev/null | head -10

# === Show next N lines of SOUL.md and AGENTS.md (helps identify partner's sections) ===
head -100 /data/SOUL.md
head -100 /data/AGENTS.md

# === Show config differences (model, provider, cwd, timezone) ===
grep -E "^\s+(default|provider):|cwd:|timezone:" /data/config.yaml

echo "" && echo "=== ASSESSMENT COMPLETE ==="
echo "Backup at: $BACKUP_DIR"
```

Review the output to identify which parts of SOUL.md/AGENTS.md are the partner's
business-specific additions (company, clients, domain) vs shared doctrine from
the last deploy.

## Execution Order (Author → Partner)

1. **Author:** Restructure repo with `merge-local.sh` in `profiles/default/scripts/`
2. **Author:** Modify `entrypoint.sh` to call `merge-local.sh` after profile sync
3. **Author:** Push to GitHub → Railway auto-deploys on author's instance
4. **Partner:** Run Partner Assessment Script (above) to back up current state
5. **Partner:** Create `/data/local/` directory with their overrides (one-time)
6. **Partner:** Run validation checklist above
7. **Both:** Every future `git push` deploys to both instances. Partner's `local/`
   overrides are automatically applied after each sync.

## Pitfalls

- **`terminal.cwd: /data/workspace` is a silent killer.** If the partner's
  config.yaml has the workspace directory as the terminal cwd, Hermes writes
  SOUL.md/AGENTS.md/USER.md to `/data/workspace/` instead of `/data/`. The
  entrypoint sync overwrites `/data/SOUL.md` with a 536-byte stock default, but
  Hermes never reads it — it's reading the real files from `/data/workspace/`.
  Always check `grep 'cwd:' /data/config.yaml` before doing anything else on a
  partner's instance. If it says `/data/workspace`, fix it first (see
  Pre-Setup Diagnostic above), THEN proceed with the local/ overlay setup.

- **The entrypoint does a blind `cp -R`.** Any file in `profiles/default/` WILL
  overwrite `/data/` on every deploy. Never put partner-specific files in the repo.
- **`local/` is volume-only.** It must be created directly on the partner's
  Railway instance, not in the git repo.
- **Config.yaml ordering matters.** The merge script deep-merges AFTER the
  overwrite. Partner overrides in `config.patch.yaml` always win.
- **SOUL.md ordering matters.** Shared doctrine comes first, partner business
  context is appended after a `# Partner Business Context` header.
- **Plugin Python deps are manual.** `pip_dependencies` in `plugin.yaml` won't
  auto-install on Railway. Use the copy-to-hermes-railway workaround.
- **AGENTS.md vs AGENTS.md path.** The default/orchestrator profile's files live
  at `/data/` (not `/data/profiles/default/`). The entrypoint syncs
  `profiles/default/*` directly to `/data/`. Named profiles sync to
  `/data/profiles/<name>/`.
- **Railway SSH from one container to another requires auth.** Railway CLI
  (`railway ssh`) needs `RAILWAY_TOKEN` or a prior `railway login`. In a
  Railway container, this token is NOT automatically available (unlike
  `RAILWAY_PROJECT_ID` and other env vars). Private networking
  (`<service>.railway.internal`) only works if you know the exact service
  name — it won't match service UUIDs. To SSH into a partner's service, either:
  (a) have the partner paste commands directly into their Railway dashboard
  terminal, or (b) authenticate the Railway CLI with a token from the Railway
  dashboard (Team Settings → API Tokens).
