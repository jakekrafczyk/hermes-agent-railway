# sitecustomize.py override pattern

Runtime patch hook for baked, root-owned Hermes modules on the Railway image.

## Why this exists

The Railway image bakes Hermes at `/opt/hermes/` as root, including the venv
at `/opt/hermes/.venv/`. The `hermes` runtime user can't edit any of it. So
when a baked module ships with a stale pin, wrong default, or broken constant,
you have two options:

1. Rebuild the Docker image with a fix. Slow, requires CI cycle, leaves the
   stale pin landmine in upstream `/opt/hermes/tools/lazy_deps.py`.
2. Monkey-patch the module at import time from a writable directory. Fast,
   reversible (`rm` the override file), survives redeploys via the persistent
   `/opt/hermes-railway/` mount.

Use option 2 for surgical pin/constant fixes. Option 1 for anything structural.

## Mechanism

Python's `site` module auto-imports `sitecustomize` at every interpreter
startup, before any user code runs. It searches every entry on `sys.path` for
a file literally named `sitecustomize.py`. The Hermes Railway entrypoint puts
`/opt/hermes-railway/` first in `PYTHONPATH`:

```bash
# /opt/hermes-railway/entrypoint.sh
export PYTHONPATH="/opt/hermes-railway:/opt/hermes-webui:/opt/hermes:${PYTHONPATH:-}"
```

So `/opt/hermes-railway/sitecustomize.py` runs first in every Python process
Hermes spawns: the WebUI server, the agent, every subagent, every cron job.

This is the same mechanism that lets us drop the supermemory SDK directly into
`/opt/hermes-railway/supermemory/` and have it shadow anything in the venv.

## Canonical use: bump a stale LAZY_DEPS pin

The shipped example. `lazy_deps.py:87` pins `firecrawl-py==4.17.0`. The
Railway image bakes `firecrawl-py==4.27.1` into `/opt/hermes-railway/` (the
v4 SDK, API-compatible — `from firecrawl import Firecrawl` works identically).
But `_is_satisfied("firecrawl-py==4.17.0")` evaluates `Version("4.27.1") in
SpecifierSet("==4.17.0")` and returns False, triggering a downgrade-install
into the root-owned `/opt/hermes/.venv/site-packages/` which fails with
`Permission denied` and breaks `web_search` / `web_extract`.

### Template (full file)

`/opt/hermes-railway/sitecustomize.py`:

```python
"""Runtime patch for the Hermes baked image."""
from __future__ import annotations
import sys


def _patch_hermes_lazy_deps() -> None:
    try:
        from hermes.tools import lazy_deps  # type: ignore
    except Exception:
        try:
            # Fallback for the flat layout used in the Railway image.
            sys.path.insert(0, "/opt/hermes")
            from tools import lazy_deps  # type: ignore
        except Exception:
            return

    pins = getattr(lazy_deps, "LAZY_DEPS", None)
    if not isinstance(pins, dict):
        return

    overrides = {
        # firecrawl-py 4.27.1 is pre-baked in /opt/hermes-railway/.
        # The original pin (4.17.0) makes _is_satisfied() return False and
        # forces a downgrade-install into a root-owned venv.
        "search.firecrawl": ("firecrawl-py==4.27.1",),
    }
    for key, spec in overrides.items():
        if key in pins:
            pins[key] = spec


_patch_hermes_lazy_deps()
```

### Verification

Run this and confirm all three lines are correct:

```bash
/opt/hermes/.venv/bin/python -c "
import sys
print('sitecustomize loaded:', 'sitecustomize' in sys.modules)
from tools import lazy_deps
print('pin now:', lazy_deps.LAZY_DEPS['search.firecrawl'])
print('_is_satisfied check:', lazy_deps._is_satisfied('firecrawl-py==4.27.1'))
"
```

Expected:
```
sitecustomize loaded: True
pin now: ('firecrawl-py==4.27.1',)
_is_satisfied check: True
```

Any False on the third line means the pin override didn't land — check that
the override key in `overrides` matches the exact LAZY_DEPS key and that
`sys.path` puts `/opt/hermes-railway/` before any other sitecustomize source.

## How to extend it

`sitecustomize.py` is the override surface; add a new `_patch_<area>()`
function per concern and call it from module scope. Keep each patch:

- **Idempotent** — if the target module/dict isn't shaped as expected, return
  silently. Never raise; sitecustomize crashes affect every Python process.
- **Narrow** — patch one key/constant at a time. Don't replace whole
  functions unless the upstream behavior is fundamentally broken.
- **Commented** — every patch needs the why-this-exists context inline,
  because no one reading `/opt/hermes/` will know this file exists.
- **Reversible** — `rm /opt/hermes-railway/sitecustomize.py` restores stock
  behavior immediately. Don't add anything that writes side effects.

## When NOT to use this

- **Adding a Python package** — copy the install into `/opt/hermes-railway/`
  directly (already documented in SKILL.md's "Installing Python Packages"
  section). sitecustomize is for behavior overrides, not dep installs.
- **Changing memory provider behavior** — use the governed-plugin pattern
  (`references/governed-memory-plugin.md`). Plugins have a cleaner extension
  surface than monkey-patching.
- **Adding tools or platforms** — use the proper plugin system. Don't try to
  inject tools via sitecustomize; the tool registry runs after sitecustomize
  and there's no clean hook in.
- **Anything that future Hermes upgrades will fix upstream** — file the issue
  and Dockerfile-patch it instead. sitecustomize accumulates technical debt
  fast if you let it become the default.

## Pitfalls

- **Don't import heavy modules at sitecustomize top level.** It runs in every
  Python process including short-lived subprocesses (e.g. `hermes config get`).
  Use lazy imports inside the patch functions. The template above does this.
- **Don't write to disk from sitecustomize.** Log to stderr if you must, but
  side effects from this file run hundreds of times a day on a busy agent.
- **The patch must survive being shadowed.** If a future Hermes upgrade
  vendors `lazy_deps.py` into a different module path, the import will fail
  and the patch silently no-ops. Add a verification step to
  `hermes-system-check` if this becomes load-bearing.
- **Don't catalog "tool X is broken" anywhere as a result of a lazy-install
  permission error.** The fix is always a writable override path. Capture
  the fix; never the negative claim.

## Related

- `references/governed-memory-plugin.md` — cleaner pattern for plugin-shaped
  behavior overrides (memory caps, container scoping).
- "Installing Python Packages" in SKILL.md — the copy-to-hermes-railway
  workaround for adding deps, which uses the same writable directory.
