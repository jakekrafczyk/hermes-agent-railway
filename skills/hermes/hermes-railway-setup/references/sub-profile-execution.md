# Sub-Profile Execution Testing Protocol

## Purpose

After editing a profile's `config.yaml`, `.env`, or doctrine files, verify
the change works by running the profile from the current session. This lets
the code_architect test researcher/orchestrator changes without switching
profiles manually.

## The Three-Step Verification

Run after ANY change to a profile's configuration:

```
1. Boot test     → hermes profile         (confirms config parses, model loads)
2. Memory test   → hermes memory status   (confirms provider connects)
3. Tool test     → hermes -z "..."        (confirms primary tool works end-to-end)
```

## Commands

### Test a Profile Boots Correctly
```bash
HERMES_HOME=/data/profiles/<name> /opt/hermes/.venv/bin/hermes profile
```

Expected output: `Active profile: <name>`, `Model: <model> (provider)`, `Skills: N installed`.

### Verify Config Parsing
```bash
HERMES_HOME=/data/profiles/<name> /opt/hermes/.venv/bin/hermes config get model.default
HERMES_HOME=/data/profiles/<name> /opt/hermes/.venv/bin/hermes config get memory.provider
```

### Verify Environment Variables
```bash
# Can't read_file .env directly (Hermes blocks it) — use grep
grep -c "OPENROUTER_API_KEY\|FIRECRAWL_API_KEY\|CAMOFOX_URL" /data/profiles/<name>/.env
# Expected count varies by profile — check against expected vars
```

### Verify Memory Provider
```bash
HERMES_HOME=/data/profiles/<name> /opt/hermes/.venv/bin/hermes memory status
# Expected: Plugin: installed ✓, Status: available ✓
```

### One-Shot Functional Test
```bash
# Researcher: test Firecrawl scrape
HERMES_HOME=/data/profiles/researcher /opt/hermes/.venv/bin/hermes -z \
  "use firecrawl_scrape with url=https://example.com and formats=['markdown']. Return only the page title."

# Orchestrator: test inbox processing
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes -z \
  "check /data/workspace/triage/inbox/ for task_*.md files. Report what you find."
```

## Profile-Specific Test Recipes

### Researcher Profile
```bash
# 1. Boot
HERMES_HOME=/data/profiles/researcher /opt/hermes/.venv/bin/hermes profile
# 2. Memory
HERMES_HOME=/data/profiles/researcher /opt/hermes/.venv/bin/hermes memory status
# 3. Scrape
HERMES_HOME=/data/profiles/researcher /opt/hermes/.venv/bin/hermes -z \
  "scrape https://example.com and return the page title only"
```

### Orchestrator (Default) Profile
```bash
# 1. Boot
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes profile
# 2. Memory
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes memory status
# 3. Inbox check
HERMES_HOME=/data /opt/hermes/.venv/bin/hermes -z \
  "check /data/workspace/triage/inbox/ for task files. Report count and output_types."
```

## Pitfalls

- **`HERMES_HOME` must be set explicitly.** Without it, `hermes` uses the
  default profile (`/data`). The code_architect's own `HERMES_HOME` is
  `/data/profiles/code_architect/` — commands run without the override test
  the code_architect profile, not the target.

- **One-shot tests use the target profile's model, not the current profile's.**
  The `-z` flag runs a complete session under the target profile's config —
  model, tools, memory provider, everything. Verify you're not burning
  credits on the wrong model before running large tests.

- **`.env` values are read, not inherited.** The target profile's `.env` must
  contain ALL required keys independently. A key present in `/data/.env` is
  NOT visible when running under `/data/profiles/researcher/`.

- **WebUI sessions read `.env` once at conversation start.** If you're testing
  via the WebUI (not CLI `-z`), env var changes take effect on the *next new
  conversation*, not the current one. CLI `hermes -z` always reads fresh.
