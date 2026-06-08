# Multi-Profile Plugin Verification (2026-06-05)

When running a multi-profile Hermes deployment, verify the memory plugin is
actually installed for EVERY profile. A missing plugin is a silent failure —
auto-capture stops working but the agent gives no indication.

## Diagnostic

```bash
for p in default researcher code_architect; do
  h=/data/profiles/$p
  [ "$p" = "default" ] && h=/data
  echo "=== $p ==="
  HERMES_HOME=$h /opt/hermes/.venv/bin/hermes memory status | grep -E "Plugin:|Status:"
  ls "$h/plugins/supermemory_governed/__init__.py" 2>/dev/null || echo "  MISSING"
done
```

Expected output for every profile:
```
Plugin:    installed ✓
Status:    available ✓
```

## If "NOT installed" but plugin dir exists

The plugin directory exists but is empty. Hermes silently skips empty dirs.
Fix: `ln -s /data/plugins/supermemory_governed $HERMES_HOME/plugins/supermemory_governed`

## If "NOT installed" and plugin dir doesn't exist

The profile was never set up for this plugin. Create the symlink:
```bash
mkdir -p $HERMES_HOME/plugins
ln -s /data/plugins/supermemory_governed $HERMES_HOME/plugins/supermemory_governed
```

## Root cause (2026-06-05 code_architect)

The code_architect profile's `plugins/` directory was created during profile
setup but the `supermemory_governed` plugin files were never copied in. The
researcher profile had the plugin installed (copy or symlink), but code_architect
was missed. Auto-capture was silently dead for all code_architect sessions
until the plugin was installed.

## Relation to container architecture

After the 2026-06-05 container architecture redesign, all profiles share the
`voltaic` default container. The `SUPERMEMORY_CONTAINER_TAG` env var is no
longer needed. But the plugin itself must still be installed per-profile.
See `hermes-railway-setup` references/supermemory-client-container-architecture.md.