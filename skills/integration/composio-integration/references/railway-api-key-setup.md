# Composio API Key Setup for Railway / Containerized Deployments

Full recipe for setting up Composio MCP on Railway where OAuth PKCE cannot work
(127.0.0.1 redirect unreachable across containers).

## Why OAuth PKCE Fails on Railway

```
Browser (Camofox container)           Hermes CLI (hermes container)
        │                                      │
        ├─ Sign in + approve ─────────────────►│
        │                                      │
        ◄── Redirect to 127.0.0.1:34073 ──────┤  ← DEAD END
        │   (goes to Camofox localhost,        │
        │    not Hermes container localhost)    │
```

The `hermes mcp login composio` command starts a local HTTP server on the Hermes container
to receive the OAuth callback. The browser opens the authorization URL, the user approves,
and Composio redirects to `127.0.0.1:<port>`. But `127.0.0.1` in the browser container is
a different machine than `127.0.0.1` in the Hermes container. The callback never reaches
`hermes mcp login`.

## Solution: API Key Auth via Backend Endpoint

Skip OAuth entirely. Use the Composio API to create an MCP server and configure Hermes
with the resulting URL + `x-api-key` header.

### Prerequisites

- `COMPOSIO_API_KEY` from [dashboard.composio.dev](https://dashboard.composio.dev)
  (starts with `comp_`; older orgs may have `ak_` prefix)
- At least one connected account already set up in the Composio dashboard
  (the user connects Facebook/X/Twitter/etc. through the dashboard UI)

### Step 1: Store API Key

```bash
echo 'COMPOSIO_API_KEY=<key>' >> /data/profiles/<profile>/.env
```

### Step 2: List Connected Accounts

```bash
curl -sS -H "x-api-key: <key>" \
  "https://backend.composio.dev/api/v3.1/connected_accounts" | python3 -m json.tool
```

From the response, extract:
- `auth_config.id` — the auth config ID (e.g., `ac_PnCX5QyWIpWq`)
- `user_id` — the user identifier (e.g., `jake1`)
- `toolkit.slug` — the platform (e.g., `facebook`)

### Step 3: Create MCP Server

```bash
curl -sS -X POST "https://backend.composio.dev/api/v3.1/mcp/servers" \
  -H "x-api-key: <key>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hermes Social Media",
    "auth_config_ids": ["ac_<id>"],
    "managed_auth_via_composio": true
  }' | python3 -m json.tool
```

Response contains:
- `id` — the MCP server UUID
- `mcp_url` — the base URL (e.g., `https://backend.composio.dev/v3/mcp/<UUID>`)
- `allowed_tools` — all available tools for the connected platform(s)

### Step 4: Build the Full URL

Append `?user_id=<user_id>` to the `mcp_url`:

```
https://backend.composio.dev/v3/mcp/<UUID>?user_id=jake1
```

### Step 5: Update Hermes Config

```yaml
mcp_servers:
  composio:
    url: "https://backend.composio.dev/v3/mcp/<UUID>?user_id=<user_id>"
    headers:
      x-api-key: "${COMPOSIO_API_KEY}"
    timeout: 180
    connect_timeout: 60
    supports_parallel_tool_calls: false
    tools:
      include: []
      exclude:
        - FACEBOOK_DELETE_POST
```

### Step 6: Verify

```bash
HERMES_HOME=/data/profiles/<profile> /opt/hermes/.venv/bin/hermes mcp test composio
# Expected: ✓ Connected, N tools discovered

# Quick functional test
HERMES_HOME=/data/profiles/<profile> /opt/hermes/.venv/bin/hermes -z \
  "Can you see mcp_composio_FACEBOOK_CREATE_POST in your tools? Answer yes/no."
```

## Verified Configuration (June 2026)

| Field | Value |
|---|---|
| MCP UUID | `11d9293f-c5f6-42a8-8805-fce788e1e224` |
| User ID | `jake1` |
| Connected account | `ca_4Qz0bQA_VvQu` (facebook_codman-wallon) |
| Auth config | `ac_PnCX5QyWIpWq` (Facebook, OAuth2, Composio-managed) |
| Tools | 39 Facebook tools, 38 after excluding FACEBOOK_DELETE_POST |
| Profile | `/data/profiles/social_media/` |

## API Endpoints Used

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `GET /api/v3.1/connected_accounts` | List connected platform accounts |
| POST | `POST /api/v3.1/mcp/servers` | Create a new MCP server |
| GET | `GET /api/v3.1/mcp/servers` | List existing MCP servers |

## Pitfalls

- **`connect.composio.dev/mcp` does NOT accept API keys.** It only supports OAuth PKCE.
  If you add `headers.x-api-key` to this URL, you'll still get 401. Use the
  `backend.composio.dev/v3/mcp/<UUID>` endpoint instead.
- **`user_id` is required in the URL.** The `mcp_url` from the API response does NOT
  include `?user_id=...`. You must append it from the connected account response.
- **Separate MCP servers per client.** For multi-client agency use, create separate
  MCP servers with different `user_id` values and connected accounts.
- **Exclude destructive tools.** `FACEBOOK_DELETE_POST`, `TWITTER_DELETE_TWEET`,
  `YOUTUBE_DELETE_VIDEO` should be excluded in the config's `tools.exclude` list.