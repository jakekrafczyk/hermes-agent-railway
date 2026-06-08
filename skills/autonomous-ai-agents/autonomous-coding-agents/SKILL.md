---
name: autonomous-coding-agents
description: Delegate coding tasks (features, PRs, refactoring) to external autonomous coding agent CLIs — Claude Code, Codex, and OpenCode. Covers one-shot execution, interactive TUI sessions, PR review, parallel worktrees, and monitoring.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
---

# Autonomous Coding Agents

Delegate coding work to external autonomous agent CLIs. All three tools follow the same orchestration pattern — terminal/PTY launch, progress monitoring, result extraction — with CLI-specific flags and gotchas.

## When to Use

- Building features or refactoring code
- PR reviews and batch issue fixing
- Long-running coding sessions with progress checks
- Parallel task execution in isolated worktrees

**Generic invocation pattern (all three):**
- **One-shot:** `terminal(command="<cli> exec/run 'task description'", workdir="~/project", timeout=<N>)`
- **Interactive:** `terminal(command="<cli>", workdir="~/project", background=true, pty=true)` then `process(action="submit", data="...")`
- **PR review:** `terminal(command="<cli> pr <N>" or "<cli> run 'Review PR vs main'")`

## Common Pitfalls (All Agents)

- All three need a git repo to operate (for code tasks); use `mktemp -d && git init` for scratch work
- PTY is required for interactive TUI sessions but NOT for one-shot mode (`-p`/`run`/`exec`)
- Clean up background tmux/PTY sessions after completion
- Monitor with `process(action="poll"|"log")`, don't kill prematurely
- Always set `workdir` to keep the agent focused on the right project
- Use `--max-turns` or equivalent in one-shot mode to prevent runaway loops

---

## Claude Code (Anthropic)

### Prerequisites

```bash
npm install -g @anthropic-ai/claude-code
claude  # first run: OAuth login
claude doctor  # verify health
```

### One-Shot (Print Mode) — PREFERRED

```bash
terminal(command="claude -p 'Add error handling to all API calls in src/' --allowedTools 'Read,Edit' --max-turns 10", workdir="~/project", timeout=120)
```

**Key flags:** `-p` (print mode, non-interactive), `--allowedTools`, `--max-turns`, `--output-format json`, `--fallback-model haiku`, `--bare` (CI mode, skips plugins/hooks).

### Interactive (PTY via tmux)

```bash
terminal(command="tmux new-session -d -s claude-session -x 140 -y 40 'claude'", timeout=10)
terminal(command="sleep 5 && tmux send-keys -t claude-session 'Refactor auth module' Enter", timeout=15)
terminal(command="sleep 15 && tmux capture-pane -t claude-session -p -S -50", timeout=5)
```

**Dialog handling:** On first launch, `Enter` accepts workspace trust. For `--dangerously-skip-permissions`, send `Down` then `Enter` (default is "No, exit"). Print mode skips dialogs entirely.

### PR Review

```bash
terminal(command="claude -p 'Review this PR thoroughly' --from-pr 42 --max-turns 10", workdir="~/project", timeout=120)
```

### Complete CLI Reference

See `references/claude-code-flags.md` for the full flag table (session, model, permissions, output, system prompt, debugging, MCP, agent teams).

### Sessions & Continuation

Resume via `claude -c` (most recent in directory) or `claude -r <id>`. Fork via `--fork-session`.

### MCP Integration

Add servers via `claude mcp add <name> -- <cmd>` or `--mcp-config <file>` in print mode.

---

## Codex (OpenAI)

```bash
npm install -g @openai/codex
```

### One-Shot

```bash
terminal(command="codex exec 'Add dark mode toggle to settings'", workdir="~/project", pty=true)
```

For scratch work (needs git repo):
```bash
terminal(command="cd $(mktemp -d) && git init && codex exec 'Build a snake game in Python'", pty=true)
```

### Key Flags

| Flag | Effect |
|------|--------|
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto` | Sandboxed but auto-approves file changes in workspace |
| `--yolo` | No sandbox, no approvals (fastest, most dangerous) |

### Background Mode

```bash
terminal(command="codex exec --full-auto 'Refactor the auth module'", workdir="~/project", background=true, pty=true)
process(action="poll", session_id="<id>")
process(action="submit", session_id="<id>", data="yes")  # answer questions
```

### PR Reviews

```bash
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && gh pr checkout 42 && codex review --base origin/main", pty=true)
```

### Parallel Issue Fixing with Worktrees

```bash
terminal(command="git worktree add -b fix/issue-78 /tmp/issue-78 main", workdir="~/project")
terminal(command="codex --yolo exec 'Fix issue #78'", workdir="/tmp/issue-78", background=true, pty=true)
```

### Rules

- Always use `pty=true` — Codex is an interactive TUI app
- Git repo required — `mktemp -d && git init` for scratch work
- Use `exec` for one-shots, `--full-auto` for building, background for long tasks

---

## OpenCode (Provider-Agnostic)

```bash
npm i -g opencode-ai@latest
# or: brew install anomalyco/tap/opencode
opencode auth list  # verify at least one provider configured
```

### One-Shot Tasks

```bash
terminal(command="opencode run 'Add retry logic to API calls and update tests'", workdir="~/project")
```

Attach context files: `opencode run 'Review config' -f config.yaml -f .env.example`

### Interactive (Background)

```bash
terminal(command="opencode", workdir="~/project", background=true, pty=true)
process(action="submit", session_id="<id>", data="Implement OAuth refresh flow")
process(action="poll", session_id="<id>")
# Exit: Ctrl+C (DO NOT use /exit — it opens an agent selector)
process(action="write", data="\x03")
```

### Key Flags

| Flag | Use |
|------|-----|
| `run 'prompt'` | One-shot execution and exit |
| `--continue` / `-c` | Continue last session |
| `--model provider/model` | Force specific model |
| `--thinking` | Show model thinking blocks |
| `--file <path>` / `-f` | Attach file(s) |

### PR Review

```bash
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

### Session & Cost Management

```bash
opencode session list
opencode stats --days 7 --models anthropic/claude-sonnet-4
```

### Verification

```bash
terminal(command="opencode run 'Respond with exactly: SMOKE_OK'")
# Expected output includes: SMOKE_OK
```

### Important: Binary Resolution

```bash
terminal(command="which -a opencode")  # check which binary resolves
terminal(command="opencode --version")
# Pin explicit path if needed:
terminal(command="$HOME/.opencode/bin/opencode run '...'", workdir="~/project", pty=true)
```

### Common Pitfalls

- `/exit` is NOT a valid command — it opens an agent selector. Use Ctrl+C.
- PATH mismatch can select wrong binary. Check with `which -a opencode`.
- Enter may need to be pressed twice in TUI (once to finalize text, once to send).
- `opencode run` does NOT need pty; interactive TUI does.
