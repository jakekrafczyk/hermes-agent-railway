#!/bin/bash
# merge-local.sh — Applies partner's /data/local/ overrides on top of distribution files.
# Runs after entrypoint syncs profiles/default/* → /data/.
# /data/local/ is NEVER in the git repo — partner-owned, survives redeploys.
#
# Two modes:
#   REPLACE — local/SOUL.md, local/AGENTS.md, local/USER.md
#     Partner's full custom file replaces the distribution version entirely.
#     Use when partner has a different agent identity from the distribution.
#   MERGE   — local/config.patch.yaml
#     Deep-merged into config.yaml. Partner keeps only their overrides (model, 
#     provider, container_tag, cwd) while inheriting all shared settings.
#   APPEND  — local/SOUL.append.md, local/AGENTS.append.md
#     If these exist AND the replacement files don't, content is appended.
#     Use when partner wants to keep shared doctrine + add personal notes.

set -euo pipefail
LOCAL_DIR="${HERMES_HOME:-/data}/local"

if [ ! -d "$LOCAL_DIR" ]; then
  echo "[merge-local] No /data/local/ directory — skipping overlay"
  exit 0
fi

echo "[merge-local] Applying local overrides from $LOCAL_DIR ..."

# --- SOUL.md: REPLACE if local/SOUL.md exists ---
if [ -f "$LOCAL_DIR/SOUL.md" ]; then
  cp "$LOCAL_DIR/SOUL.md" "$HERMES_HOME/SOUL.md"
  echo "[merge-local] ✓ Replaced SOUL.md with local/SOUL.md ($(wc -c < "$HERMES_HOME/SOUL.md") bytes)"
elif [ -f "$LOCAL_DIR/SOUL.append.md" ]; then
  echo "" >> "$HERMES_HOME/SOUL.md"
  echo "<!-- BEGIN LOCAL APPEND -->" >> "$HERMES_HOME/SOUL.md"
  cat "$LOCAL_DIR/SOUL.append.md" >> "$HERMES_HOME/SOUL.md"
  echo "<!-- END LOCAL APPEND -->" >> "$HERMES_HOME/SOUL.md"
  echo "[merge-local] ✓ Appended local/SOUL.append.md to SOUL.md"
else
  echo "[merge-local] - SOUL.md: no local override (using distribution version)"
fi

# --- AGENTS.md: REPLACE if local/AGENTS.md exists ---
if [ -f "$LOCAL_DIR/AGENTS.md" ]; then
  cp "$LOCAL_DIR/AGENTS.md" "$HERMES_HOME/AGENTS.md"
  echo "[merge-local] ✓ Replaced AGENTS.md with local/AGENTS.md ($(wc -c < "$HERMES_HOME/AGENTS.md") bytes)"
elif [ -f "$LOCAL_DIR/AGENTS.append.md" ]; then
  echo "" >> "$HERMES_HOME/AGENTS.md"
  echo "<!-- BEGIN LOCAL APPEND -->" >> "$HERMES_HOME/AGENTS.md"
  cat "$LOCAL_DIR/AGENTS.append.md" >> "$HERMES_HOME/AGENTS.md"
  echo "<!-- END LOCAL APPEND -->" >> "$HERMES_HOME/AGENTS.md"
  echo "[merge-local] ✓ Appended local/AGENTS.append.md to AGENTS.md"
else
  echo "[merge-local] - AGENTS.md: no local override (using distribution version)"
fi

# --- USER.md: REPLACE if local/USER.md exists ---
if [ -f "$LOCAL_DIR/USER.md" ]; then
  cp "$LOCAL_DIR/USER.md" "$HERMES_HOME/USER.md"
  echo "[merge-local] ✓ Restored local/USER.md ($(wc -c < "$HERMES_HOME/USER.md") bytes)"
fi

# --- config.yaml: deep-merge partner's overrides ---
if [ -f "$LOCAL_DIR/config.patch.yaml" ]; then
  python3 -c "
import yaml, sys
from pathlib import Path

here = Path('$HERMES_HOME')
cfg_path = here / 'config.yaml'
patch_path = Path('$LOCAL_DIR') / 'config.patch.yaml'

try:
    cfg = yaml.safe_load(cfg_path.read_text()) or {}
except Exception:
    print('[merge-local] WARNING: could not parse config.yaml — skipping config merge', file=sys.stderr)
    sys.exit(0)

try:
    patch = yaml.safe_load(patch_path.read_text()) or {}
except Exception:
    print('[merge-local] could not parse config.patch.yaml — skipping', file=sys.stderr)
    sys.exit(0)

def deep_merge(base, overlay):
    for key, val in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(val, dict):
            deep_merge(base[key], val)
        else:
            base[key] = val

deep_merge(cfg, patch)
yaml.safe_dump(cfg, cfg_path.open('w'), sort_keys=False)
print('[merge-local] ✓ Merged local/config.patch.yaml into config.yaml')
" 2>&1
fi

echo "[merge-local] Done."