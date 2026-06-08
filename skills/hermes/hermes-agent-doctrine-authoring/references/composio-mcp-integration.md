# Composio MCP Integration for Hermes Profiles

Condensed from full research at `/data/workspace/triage/inbox/task_8f3a1b7c.md` (2026-06-01).
Use this as the authoritative reference when wiring Composio MCP into any Hermes profile.

## MCP Config Block (HTTP Tool Router)

Composio uses HTTP-based MCP (not subprocess). Two auth models exist:

- **OAuth PKCE:** `https://connect.composio.dev/mcp` with `auth: oauth` in config. Works on
  local/single-machine setups where the browser and Hermes share a localhost.
- **API key:** `https://backend.composio.dev/v3/mcp/<UUID>?user_id=<ID>` with `x-api-key` header.
  **Required for Railway, Kubernetes, Docker Compose, or any containerized deployment** where
  the browser and Hermes CLI are in separate containers (OAuth's 127.0.0.1 callback can't cross).

```yaml
# OAuth PKCE (local/single-machine only — does NOT work on Railway):
mcp_servers:
  composio:
    url: "https://connect.composio.dev/mcp"
    auth: oauth
    timeout: 180
    ...

# API key (Railway / containerized — the production path):
mcp_servers:
  composio:
    url: "https://backend.composio.dev/v3/mcp/<SERVER_ID>?user_id=<user_id>"
    headers:
      x-api-key: "${COMPOSIO_API_KEY}"
    timeout: 180
    connect_timeout: 60
    supports_parallel_tool_calls: false
    tools:
      include: []
      exclude:
        - "FACEBOOK_DELETE_POST"
```

**Railway/containerized deployments MUST use the API key path.** OAuth PKCE redirects to
`127.0.0.1:<port>` which is unreachable across containers. See `composio-integration` skill
Method C and `references/railway-api-key-setup.md` for the full recipe.

**Tool naming:** Hermes prefixes MCP tools as `mcp_composio_TWITTER_CREATE_A_POST`.

**URL generation** (one-time, via SDK):
```python
from composio import Composio
composio = Composio(api_key="your-key")
session = composio.create(
    user_id="social-media-agent",
    toolkits=["twitter", "linkedin", "instagram", "facebook", "tiktok", "youtube"]
)
print(session.mcp.url)
# → https://backend.composio.dev/v3/mcp/550e8400-...?user_id=social-media-agent
```

**Critical:** The MCP URL includes `user_id` as a query parameter — this scopes all connected accounts.
Multi-client agencies need either separate MCP URLs per client or dynamic URL generation.

## Required .env Variables

| Variable | Required | Source |
|---|---|---|
| `COMPOSIO_API_KEY` | **Yes** | https://dashboard.composio.dev |
| Platform OAuth credentials | Optional | Only if using custom developer apps instead of Composio's built-in OAuth |

Composio provides built-in OAuth apps for Twitter, LinkedIn, Facebook, Instagram, YouTube.
You can start immediately with just `COMPOSIO_API_KEY`. TikTok **requires** own developer credentials.

## Platform Tool Inventory

| Platform | Tools | Auth | Notes |
|---|---|---|---|
| Twitter/X | 78 | OAuth2 (built-in available) | Posts, search, DMs, analytics, lists, media |
| YouTube | 47 | OAuth2 (built-in available) | Videos, playlists, comments, analytics, live chat |
| Facebook | 39 | OAuth2 (built-in available) | **Pages only** — not personal profiles |
| Instagram | 29 | OAuth2 (built-in available) | Requires Business/Creator account linked to Facebook Page |
| LinkedIn | 22 | OAuth2 (built-in available) | Posts, articles, company info, ad targeting |
| TikTok | 10 | OAuth2 (**no built-in app**) | Video upload, user stats, requires own developer credentials |

**Not available:** Reddit, Threads, Pinterest, Snapchat, Mastodon/Bluesky.

## Authentication Model

Composio uses **Managed OAuth2**: connect accounts in the dashboard → Composio stores tokens,
auto-refreshes before expiry, injects per-`user_id` at tool call time.

Per-platform built-in app availability:
- Twitter, LinkedIn, Instagram, Facebook, YouTube: built-in OAuth apps available (start immediately)
- TikTok: **must** provide own developer credentials

For production: configure your own OAuth apps for rate limit control and branding.

## Pricing (June 2026)

| Tier | Monthly | Tool Calls | Overage |
|---|---|---|---|
| Free | $0 | 20,000 | Hard cap |
| Pro | $29 | 200,000 | $0.299/1K |
| Business | $229 | 2,000,000 | $0.249/1K |
| Enterprise | Custom | Custom | Negotiated |

**Agency estimate:** ~610 tool calls/client/month (3 posts/day × 3 platforms + analytics + engagement).
Free tier supports ~30 clients at basic usage. Pro needed for 50+.

## Gotchas

1. **Rube MCP is deprecated.** Use Tool Router (`backend.composio.dev/v3/mcp/...`), not `mcp.composio.dev`.
2. **MCP API key mandatory** for orgs created after March 2026.
3. **Link auth migration by July 2026:** switch to `POST /api/v3/connected_accounts/link`.
4. **Facebook = Pages only.** Cannot post to personal timelines.
5. **Instagram = Business/Creator only.** Personal profiles not supported.
6. **Tool Router URL is dynamic** — generated at SDK call time. Hardcode once or script the update.
7. **Session is per-user.** `composio.create()` returns new session each call.
8. **Preloaded tools <20 recommended** for context efficiency. Social toolkits expose 117+ tools — use `tools.include` filtering.
9. **`user_id` is the multi-client isolation boundary.** One MCP URL = one set of connected accounts.
10. **Rate limits:** platform-level limits still apply (Twitter: 50 tweets/24h free tier, Instagram: 25 posts/24h Business).
11. **Video uploads need higher timeout.** Set `timeout: 180-300` for TikTok/YouTube video operations.
12. **Observability:** audit logs via `POST /api/v3.1/logs/tool_execution` and usage summaries at org/project level.

## Multi-Client Agency Pattern

For multi-client isolation:
- **Option A:** Separate Hermes profiles per client, each with different MCP URL + `user_id`
- **Option B (current):** Single profile, dynamic MCP URL switching based on `active_client.yaml`
- Composio's `user_id` parameter scopes connected accounts — use `client-<name>` convention
- All clients share the same project quota (no per-client billing on Free/Pro/Business)