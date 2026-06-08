# Composio MCP: General Docs vs. Hermes Integration Page

**Date observed:** 2026-06-01  
**Lesson:** Always check for Hermes-specific integration pages before implementing from general SDK docs.

## The Mismatch

| Source | Endpoint | Auth | Config Complexity |
|---|---|---|---|
| **General MCP docs** (docs.composio.dev) | `backend.composio.dev/v3/mcp/<ID>?user_id=<ID>` | `x-api-key` header + `COMPOSIO_API_KEY` env var | SDK URL generation, API key management, per-user session creation |
| **Hermes integration page** (composio.dev/hermes) | `connect.composio.dev/mcp` | **None** — OAuth auto-negotiated | Zero-config, one-line URL |

## What Happened

1. Researcher scraped Composio's general docs, GitHub, pricing pages → found the SDK-based MCP setup
2. Code_architect implemented that config: SDK-generated URL, API key header, env variable placeholder
3. User provided the Hermes-specific setup page (`composio.dev/hermes`) → revealed a completely different (simpler) endpoint
4. Had to surgically patch config.yaml and .env to switch endpoints

## Correct Workflow

When integrating any external service:

1. Delegate to researcher: "Research `<service>` integration, including any Hermes-specific setup pages"
2. When researcher returns: **explicitly search** for `<service>.com/hermes`, `<service>.com/integrations/hermes-agent`, or similar
3. If a Hermes-specific page exists, **prefer it** over the general docs — they are often simpler
4. Implement from the Hermes page; cite general docs only for reference/fallback

## Hermes MCP Config Block (Correct — from composio.dev/hermes)

```yaml
mcp_servers:
  composio:
    url: "https://connect.composio.dev/mcp"
    # No auth headers — OAuth auto-negotiated via Composio Hermes integration
    timeout: 180
    connect_timeout: 60
    supports_parallel_tool_calls: false
    tools:
      include: []
      exclude:
        - "TWITTER_DELETE_TWEET"
        - "YOUTUBE_DELETE_VIDEO"
        - "FACEBOOK_DELETE_POST"
```

## User Flow After Config

1. User creates account at dashboard.composio.dev
2. User connects apps (Twitter/X, LinkedIn, etc.) via OAuth in dashboard
3. Profile auto-discovers tools through the `connect.composio.dev/mcp` endpoint
4. No API key exchange needed between user and profile
