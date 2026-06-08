# Claude Code CLI Flags Reference

## Session & Environment
| Flag | Effect |
|------|--------|
| `-p, --print` | Non-interactive one-shot mode (exits when done) |
| `-c, --continue` | Resume most recent conversation in current directory |
| `-r, --resume <id>` | Resume specific session by ID or name |
| `--fork-session` | When resuming, create new session ID |
| `--session-id <uuid>` | Use a specific UUID for the conversation |
| `--no-session-persistence` | Don't save session to disk (print mode only) |
| `--add-dir <paths...>` | Grant Claude access to additional working directories |
| `-w, --worktree [name]` | Run in isolated git worktree |
| `--tmux` | Create a tmux session for the worktree |
| `--from-pr [number]` | Resume session linked to a GitHub PR |
| `--ide` | Auto-connect to a valid IDE on startup |

## Model & Performance
| Flag | Effect |
|------|--------|
| `--model <alias>` | Model: sonnet, opus, haiku, or full name |
| `--effort <level>` | Reasoning depth: low, medium, high, max, auto |
| `--max-turns <n>` | Limit agentic loops (print mode only) |
| `--max-budget-usd <n>` | Cap API spend in dollars (print mode only) |
| `--fallback-model <model>` | Auto-fallback when default overloaded (print mode only) |

## Permission & Safety
| Flag | Effect |
|------|--------|
| `--dangerously-skip-permissions` | Auto-approve ALL tool use |
| `--permission-mode <mode>` | default, acceptEdits, plan, auto, dontAsk, bypassPermissions |
| `--allowedTools <tools...>` | Whitelist specific tools |
| `--disallowedTools <tools...>` | Blacklist specific tools |

## Output & Input Format
| Flag | Effect |
|------|--------|
| `--output-format <fmt>` | text, json, stream-json |
| `--json-schema <schema>` | Force structured JSON output matching a schema |
| `--verbose` | Full turn-by-turn output |
| `--include-partial-messages` | Include partial message chunks (stream-json + print) |

## System Prompt & Context
| Flag | Effect |
|------|--------|
| `--append-system-prompt <text>` | Add to default system prompt |
| `--bare` | Skip hooks, plugins, MCP discovery, OAuth (fastest startup) |
| `--agents '<json>'` | Define custom subagents dynamically as JSON |
| `--mcp-config <path>` | Load MCP servers from JSON file |

## Debugging
| Flag | Effect |
|------|--------|
| `-d, --debug [filter]` | Enable debug logging with optional category filter |
| `--debug-file <path>` | Write debug logs to file |

## Tool Name Syntax (--allowedTools / --disallowedTools)
```
Read                    — All file reading
Edit                    — File editing (existing files)
Write                   — File creation (new files)
Bash                    — All shell commands
Bash(git *)             — Only git commands
WebSearch               — Web search capability
WebFetch                — Web page fetching
mcp__<server>__<tool>   — Specific MCP tool
```

## Settings Hierarchy (highest to lowest priority)
1. CLI flags — override everything
2. Local project: `.claude/settings.local.json` (personal, gitignored)
3. Project: `.claude/settings.json` (shared, git-tracked)
4. User: `~/.claude/settings.json` (global)