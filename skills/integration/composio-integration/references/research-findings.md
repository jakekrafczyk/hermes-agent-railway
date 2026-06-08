# Composio MCP Integration — Full Research Dump

> Source: `/data/workspace/triage/inbox/task_8f3a1b7c.md` (researcher findings, June 2026)
> Confidence: high | Sources: 15 URLs | Word count: 3,200

## 1. MCP Server Config Block for Hermes config.yaml

Composio uses **Tool Router** — a single HTTP MCP endpoint that dynamically discovers
tools across all connected toolkits. The Hermes-specific simplified endpoint is
`https://connect.composio.dev/mcp` (no auth headers, OAuth auto-negotiated).

For the generic SDK endpoint (not recommended for Hermes), generation via Python:

```python
from composio import Composio

composio = Composio(api_key="your-composio-api-key")
session = composio.create(
    user_id="social-media-agent",
    toolkits=["twitter", "linkedin", "instagram", "facebook", "tiktok", "youtube"]
)
print(session.mcp.url)
# Output: https://backend.composio.dev/v3/mcp/550e8400-e29b-41d4-a716-446655440000?user_id=social-media-agent
```

**Hermes MCP config fields (official reference):**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `url` | string | Yes (HTTP) | Remote MCP endpoint |
| `headers` | dict | No | HTTP headers per request |
| `timeout` | int | No | Per-tool-call timeout (default 120s, increase for video uploads) |
| `connect_timeout` | int | No | Initial connection timeout (default 60s) |
| `tools.include` | list | No | Whitelist specific tools |
| `tools.exclude` | list | No | Blacklist dangerous tools |
| `supports_parallel_tool_calls` | bool | No | Allow concurrent execution |

> **Tool naming:** Hermes prefixes MCP tools as `mcp_<server_name>_<tool_name>`.
> So a Composio Twitter post tool appears as `mcp_composio_TWITTER_CREATE_A_POST`.

## 2. Required .env Variables

### Mandatory
| Variable | Example Value | Description |
|----------|--------------|-------------|
| `COMPOSIO_API_KEY` | `comp_abc123xyz...` | Composio project API key from dashboard. Required for generic SDK endpoint only — NOT needed for `connect.composio.dev/mcp`. |

### Optional (per-platform OAuth, only if using custom apps)

Composio provides built-in OAuth apps for most platforms. Use these immediately
with no additional .env variables. For production or custom apps:

| Variable | Platform | When Needed |
|----------|----------|-------------|
| `TWITTER_CLIENT_ID` / `TWITTER_CLIENT_SECRET` | X/Twitter | Custom developer app (recommended for production) |
| `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET` | LinkedIn | Custom developer app |
| `INSTAGRAM_CLIENT_ID` / `INSTAGRAM_CLIENT_SECRET` | Instagram | Custom Meta developer app |
| `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET` | Facebook | Custom Meta app |
| `TIKTOK_CLIENT_KEY` / `TIKTOK_CLIENT_SECRET` | TikTok | **Required** — no default app |
| `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET` | YouTube | Custom Google Cloud project |

## 3. Social Platform Tool Inventory

| Platform | Tools | Auth | Key Actions |
|----------|-------|------|-------------|
| **Twitter/X** | 78 | OAuth2 | Create/delete posts, search, timeline, DMs, user lookup, followers, analytics, lists, media upload, spaces |
| **Instagram** | 29 | OAuth2 | Create media (carousel, photo, video, reel), comment CRUD, DMs, insights, story management, mentions |
| **Facebook** | 39 | OAuth2 | **Pages only**: posts (text, photo, video, album), comments, Messenger, page management, insights, reactions |
| **LinkedIn** | 22 | OAuth2 | Articles/posts, comments, profile lookup, company info, org page stats, ad targeting |
| **TikTok** | 10 | OAuth2 | Upload video (single + batch), photo post (1-35 images), list videos, user stats, marketing API |
| **YouTube** | 47 | OAuth2 | Upload/delete videos, playlist CRUD, comments, analytics, captions, live chat, super chat |

### Platforms NOT directly supported via Composio social toolkits
- **Reddit** — Listed in enterprise integrations but no dedicated toolkit page
- **Threads** — Not listed
- **Pinterest** — Not listed
- **Snapchat** — Not listed
- **Mastodon/Bluesky** — Not listed

## 4. Authentication Model per Platform

**Primary Model: Composio Managed OAuth2**

1. In Composio dashboard, add a connected account for each platform
2. Composio initiates OAuth2 flow → user grants permissions
3. Composio stores tokens, handles automatic refresh/rotation
4. At tool call time, Composio injects correct token per `user_id`
5. Tokens scoped per connected account + user combination

**Per-Platform Default App Availability:**

| Platform | Default App Available | Requires Own Credentials |
|----------|----------------------|--------------------------|
| Twitter/X | Yes | Optional, recommended for production |
| LinkedIn | Yes | Optional |
| Instagram | Yes | Optional |
| Facebook | Yes | Optional |
| TikTok | **No** | **Required** |
| YouTube | Yes | Optional |

## 5. Pricing/Tier Constraints for Multi-Client Agency Use

| Tier | Monthly Cost | Tool Calls/Month | Overage Rate |
|------|-------------|-------------------|--------------|
| Free | $0 | 20,000 | N/A (hard cap) |
| Pro | $29 | 200,000 | $0.299/1K calls |
| Business | $229 | 2,000,000 | $0.249/1K calls |
| Enterprise | Custom | Custom | Negotiated |

**Agency Sizing (est. ~610 tool calls/client/month):**

| Agency Size | Clients | Est. Monthly Calls | Required Tier |
|-------------|---------|-------------------|---------------|
| Boutique | 5 | ~3,050 | Free (20K) |
| Small | 20 | ~12,200 | Free |
| Mid-size | 50 | ~30,500 | Pro (200K) |
| Large | 100 | ~61,000 | Pro |
| Enterprise | 200+ | 122,000+ | Business (2M) |

## 6. Gotchas and Limitations

### Breaking Changes and Deprecations
1. **Rube MCP is deprecated.** Replaced by Tool Router.
2. **`mcp.composio.dev` fully deprecated.** Use `backend.composio.dev/v3/mcp/...`.
3. **Link auth migration (July 2026).** Old `POST /api/v3/connected_accounts` retiring.
4. **MCP API key mandatory** for new orgs after March 2026 (generic endpoint only).

### Functional Limitations
5. **Facebook = Pages only.** Cannot post to personal profiles.
6. **TikTok requires own credentials.** No built-in OAuth app.
7. **Instagram requires Business/Creator account** linked to a Facebook Page.
8. **No Reddit or Threads toolkit** as of June 2026.

### Tool Router / Session Gotchas
9. **Session is per-user.** `composio.create()` returns new session each call. Use `composio.use(sessionId)` to reuse.
10. **Preloaded tools <20 recommended** for context efficiency. Social toolkits can expose 117+ tools.
11. **Tool Router URL is dynamic.** Generated at SDK call time.

### Hermes-Specific Gotchas
12. **Profile isolation.** Each Hermes profile has its own `config.yaml` and `.env`.
13. **Environment variable filtering.** Hermes only passes limited env vars to MCP subprocesses. For HTTP MCP, set auth in `headers`.
14. **Tool timeout.** Default 120s too short for video uploads. Increase to 180-300s.
15. **Rate limits are platform-level.** Composio retries but cannot bypass limits.

## 7. Recommendations for Hermes Social Media Profile

1. Use `https://connect.composio.dev/mcp` — the Hermes-specific simplified endpoint
2. No auth headers needed — OAuth auto-negotiated
3. In the Hermes profile config, use `tools.include` to whitelist only needed actions
4. Start with Composio's built-in OAuth apps, migrate to custom OAuth for production
5. Monitor tool call usage in first month to right-size pricing tier
6. For multi-client isolation: separate Hermes profiles per client with distinct `user_id` values
