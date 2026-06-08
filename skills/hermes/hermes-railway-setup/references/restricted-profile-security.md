# Restricted Profile Security — Full Recipe

How to configure a Hermes profile for a non-technical user (business partner, client, team member)
who needs Hermes capabilities without filesystem/codebase access.

## Threat Model

Non-technical user in WebUI → same tool access as any profile → model can call `write_file`,
`patch`, `terminal` → can corrupt configs, delete files, break orchestration system.

## Toolset Decision Matrix

| Toolset | Disable? | Rationale |
|---------|----------|-----------|
| `terminal` | ✅ DISABLE | Biggest blast radius — arbitrary shell, `rm -rf`, config edits |
| `computer_use` | ✅ DISABLE | Screen control — not needed for marketing use case |
| `kanban` | ✅ DISABLE | Internal multi-profile coordination — agency-only |
| `discord` / `discord_admin` | ✅ DISABLE | Agency communications |
| `spotify` / `feishu_doc` / `feishu_drive` / `homeassistant` / `yuanbao` | ✅ DISABLE | Irrelevant to partner |
| `file` | ❌ KEEP | Bundled read+write. `read_file`/`search_files` essential for context. Writes blocked via SOUL.md + approvals |
| `web` | ❌ KEEP | `web_search`, `web_extract` — core research capability |
| `browser` | ❌ KEEP | Browse pages, navigate |
| `vision` | ❌ KEEP | Image analysis |
| `image_gen` | ❌ KEEP | Content creation |
| `session_search` | ❌ KEEP | Own conversation history |
| `memory` | ❌ KEEP | Own supermemory container |
| `skills` | ❌ KEEP | Read/use skills |
| `todo` | ❌ KEEP | Task tracking |
| `tts` | ❌ KEEP | Text-to-speech |
| `cronjob` | ❌ KEEP | Scheduled tasks |
| `video` | ❌ KEEP | Video playback |

## Config Template

```yaml
# /data/profiles/<partner>/config.yaml
agent:
  disabled_toolsets:
    - terminal
    - computer_use
    - kanban
    - discord
    - discord_admin
    - spotify
    - feishu_doc
    - feishu_drive
    - homeassistant
    - yuanbao

approvals:
  mode: always   # every tool call requires confirmation click

mcp_servers:
  composio:
    url: "https://backend.composio.dev/v3/mcp/<UUID>?user_id=<PARTNER_USER_ID>"
    headers:
      x-api-key: "${COMPOSIO_API_KEY}"
    timeout: 180
    connect_timeout: 60
    supports_parallel_tool_calls: false
    tools:
      include: []
      exclude:
        - FACEBOOK_DELETE_POST
        - TWITTER_DELETE_TWEET
        - YOUTUBE_DELETE_VIDEO
        - INSTAGRAM_DELETE_MEDIA
        - LINKEDIN_DELETE_POST
```

## SOUL.md Template

```markdown
# <Partner Name> — Marketing Assistant

You are a marketing assistant. Help with social media, analytics, content creation, and research.

## HARD RULES — NEVER VIOLATE

1. NEVER call `write_file`, `patch`, or `terminal`. These tools are FORBIDDEN.
2. NEVER create, modify, or delete files on the local filesystem.
3. NEVER run shell commands.
4. You may ONLY use `read_file` and `search_files` for reading context.
5. For content creation, publishing, and analytics — use Composio MCP tools.
6. For web research — use `web_search`, `web_extract`, or `browser`.

## Memory

You have your own memory space. Store useful facts about the partner's business, preferences,
and campaign history. Never access or reference other users' memory containers.
```

## Approvals Mode Trade-off

| Mode | Behavior | Best for |
|------|----------|----------|
| `always` | Every tool call needs a confirmation click | Non-technical users who can't evaluate tool calls |
| `auto` | Model decides when to ask | Technical users; relies on SOUL.md to prevent bad calls |

For non-technical partners: use `always`. They won't know when to say no otherwise. The UX
friction (confirming reads too) is a feature, not a bug — it keeps them engaged with what
the model is doing.

## Pitfalls

- **`file` toolset is all-or-nothing.** `read_file`, `write_file`, `patch`, `search_files`
  are bundled. Disabling `file` kills read access too. Keep it enabled; rely on SOUL.md +
  approvals to block writes.
- **SOUL.md is soft protection.** The model can ignore system prompt instructions. Always pair
  with `approvals.mode: always` as the hard backstop.
- **`approvals.mode: always` applies to ALL tools** including safe reads. Partner will need to
  click confirm on every `web_search`, `read_file`, etc. This is intentional for non-technical
  users.
- **Partner's Composio setup is independent.** They need their own Composio account, their own
  API key, their own connected accounts. Never share your Composio MCP URL or API key.
- **Memory isolation requires separate container tag.** Set `SUPERMEMORY_CONTAINER_TAG` in the
  partner's profile `.env` file. Without this, their memories mix with yours in the default
  container.
- **Cron jobs run unattended.** If the partner's profile has `cronjob` enabled, scheduled jobs
  run without the approval gate (no user present to click confirm). Consider whether the
  partner actually needs cron — if they do, ensure cron prompts explicitly forbid writes.
