# Cross-Profile Memory Audit

When auto-capture isn't working across profiles on a Railway multi-profile deployment,
run this systematic audit. It catches missing symlinks, stale copies, missing runtime
config, and SDK import failures in one pass.

## Quick Audit (all profiles at once)

```bash
for d in /data /data/profiles/*/; do
  name=$(basename $d)
  echo "=== $name ==="
  HERMES_HOME=$d /opt/hermes/.venv/bin/hermes memory status 2>&1 | grep -E "Provider:|Status:|active"
  plugin_path="${d}plugins/supermemory_governed"
  if [ -L "$plugin_path" ]; then
    echo "Plugin: symlink → $(readlink $plugin_path)"
  elif [ -d "$plugin_path" ]; then
    echo "Plugin: directory copy (stale)"
  else
    echo "Plugin: NOT FOUND"
  fi
  json="${d}supermemory.json"
  if [ -f "$json" ]; then
    grep -q '"auto_capture": true' "$json" && echo "auto_capture: ON" || echo "auto_capture: OFF"
  else
    echo "auto_capture: no supermemory.json (using plugin defaults)"
  fi
  echo ""
done
```

## Audit Checklist

For each profile, verify:

| Check | Expected | Fix if wrong |
|---|---|---|
| `hermes memory status` shows `available ✓` | Plugin loads + SDK imports | Copy SDK to `/opt/hermes-railway/` |
| Plugin at `$HERMES_HOME/plugins/<name>/` is a symlink | `lrwxrwxrwx → /data/plugins/<name>` | `rm -rf` stale copy, `ln -s` to canonical |
| `supermemory.json` exists | File present with `auto_capture: true` | Create with `write_file` (template below) |
| `api_base` is v4 (cosmetic) | `grep api.supermemory.ai` shows `/v4` | `execute_code` to patch protected config |

## Profile Inventory (verified 2026-06-07)

| Profile | Provider | Plugin source | supermemory.json |
|---|---|---|---|
| default (`/data/`) | `supermemory` | canonical copy at `/data/plugins/` | `/data/supermemory.json` |
| code_architect | `supermemory_governed` | symlink → `/data/plugins/supermemory_governed` | `/data/profiles/code_architect/supermemory.json` |
| researcher | `supermemory` | symlink → `/data/plugins/supermemory_governed` | `/data/profiles/researcher/supermemory.json` |
| social_media | `supermemory_governed` | symlink → `/data/plugins/supermemory_governed` | `/data/profiles/social_media/supermemory.json` |

## Canonical `supermemory.json`

```json
{
  "auto_capture": true,
  "auto_recall": false,
  "container_tag": "voltaic",
  "max_recall_results": 3,
  "search_mode": "hybrid"
}
```

Additional keys for multi-container profiles: `enable_custom_container_tags`, `custom_containers`, `custom_container_instructions`. See `hermes-railway-setup` → `references/supermemory-multi-container.md`.

## Pitfalls

- **Directory copy ≠ symlink**: A profile with a stale directory copy will work temporarily but diverge from the canonical plugin over time. Always symlink unless the profile IS the canonical source (`/data/plugins/`).
- **Missing `supermemory.json` is silent**: The plugin falls back to defaults — no error, no warning. Auto-capture may still work but you have no explicit control. Always create the file for every profile.
- **api_base config key is vestigial**: The SDK v3.42 hardcodes `https://api.supermemory.ai`. Changing config.yaml's `api_base` has no runtime effect on the current SDK version. Fix it for hygiene only — the SDK import is the real fix.
- **`hermes memory status` can say `available ✓` even with no `supermemory.json`**: Available means the plugin loaded + SDK imported + API key present. Runtime settings (auto_capture, container_tag) come from the JSON file, not from availability status.
