# Railway CLI Binary Paths

On Railway deployments (protemplate/hermes-agent-railway), the Hermes CLI
binary is NOT at `/opt/hermes/hermes` — that entrypoint fails with
`ModuleNotFoundError: No module named 'yaml'` because it runs outside the
venv.

## Working Path

```
/opt/hermes/.venv/bin/hermes
```

This is the venv-wrapped binary with all dependencies available.

## Verification

```bash
/opt/hermes/.venv/bin/hermes curator status   # smoke test
/opt/hermes/.venv/bin/hermes profile list     # another check
```

## Pitfall

Do NOT use `which hermes` or `hermes` bare — the PATH may not include the
venv bin. Always use the full path. This applies to cron scripts,
background processes, and any subprocess that needs the CLI.

## Profiles Share Skills

All Railway profiles (default, code_architect, researcher, social_media)
share `/data/skills/` — there are no per-profile skills directories.
Running `hermes curator run` once from default covers all profiles.
