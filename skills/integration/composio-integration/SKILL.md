---
name: composio-integration
description: Set up and manage Composio MCP integration for Hermes — connecting social media platforms (Facebook, X/Twitter, LinkedIn, Instagram, TikTok, YouTube) to agent profiles for posting, analytics, and engagement.
triggers:
  - User asks to connect a social platform (Facebook, X, LinkedIn, etc.) through Composio
  - User mentions "Composio setup" or "composio.dev"
  - Configuring MCP servers for Composio in Hermes profiles
  - Diagnosing why Composio MCP tools aren't appearing
  - Multi-client agency Composio account architecture
---

# Composio Integration for Hermes

Connect social media platforms to Hermes agent profiles via Composio's Tool Router MCP.
Covers setup, platform-specific quirks, pricing tiers, multi-client isolation, and tool discovery.

## Integration Methods

### Method A: Composio Connect MCP (Profile-Level)

Add to a Hermes profile's `config.yaml`:

```yaml
mcp_servers:
  composio:
    url: "https://connect.composio.dev/mcp"
    auth: oauth          # REQUIRED — tells Hermes to initiate OAuth flow
    # No auth headers — OAuth handshake uses this auth field, not static headers
    timeout: 180
    connect_timeout: 60
    supports_parallel_tool_calls: false
    tools:
      include: []
      exclude:
        - TWITTER_DELETE_TWEET
        - YOUTUBE_DELETE_VIDEO
        - FACEBOOK_DELETE_POST
```

**Key points:**
- URL is `https://connect.composio.dev/mcp` — the Hermes-specific endpoint from composio.dev/hermes
- **`auth: oauth` is REQUIRED** — without it, Hermes doesn't know to initiate OAuth and will send plain unauthenticated requests (result: 401). This is NOT the same as adding auth headers — it's a flag that tells Hermes which protocol to use.
- **No static auth headers** — the OAuth handshake is dynamic (per composio.dev/hermes instructions). Do NOT add `headers.x-api-key` or `Authorization` headers.
- After config change, `hermes mcp login composio` triggers the OAuth flow, then tools appear as `mcp_composio_*`
- Destructive tools should be excluded by default

### Method B: Composio Connect CLI (System-Level)

```bash
curl -fsSL https://composio.dev/install | bash
```

Then tell the agent "Connect to Composio." Hermes prompts for authentication. The CLI
auto-handles config injection.

### Method C: API Key Auth (REQUIRED for Railway / Containerized Deployments)

**Why this method exists:** Method A's OAuth PKCE flow redirects to `127.0.0.1:<port>/callback`.
On Railway and other containerized deployments, the browser and the Hermes CLI run in
**different containers** — the redirect goes to the browser container's localhost, which
cannot reach the Hermes container. OAuth PKCE is fundamentally broken in this architecture.

**When to use:** Railway, Kubernetes, Docker Compose, or any deployment where Hermes and
the browser are in separate containers or network namespaces.

**Prerequisites:** A `COMPOSIO_API_KEY` from [dashboard.composio.dev](https://dashboard.composio.dev).
Keys start with `comp_` (older orgs may have `ak_` prefix).

**Step 1 — Store the API key in the profile's `.env`:**
```bash
echo 'COMPOSIO_API_KEY=<your-key>' >> /data/profiles/<profile>/.env
```

**Step 2 — Check existing connected accounts:**
```bash
curl -sS -H "x-api-key: <key>" "https://backend.composio.dev/api/v3.1/connected_accounts" | python3 -m json.tool
```
Look for the `auth_config.id` field (e.g., `ac_PnCX5QyWIpWq`) for each connected platform.

**Step 3 — Create an MCP server via API:**
```bash
curl -sS -X POST "https://backend.composio.dev/api/v3.1/mcp/servers" \
  -H "x-api-key: <key>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Hermes Social Media", "auth_config_ids": ["ac_..."], "managed_auth_via_composio": true}'
```
Response includes `mcp_url` (e.g., `https://backend.composio.dev/v3/mcp/<UUID>`).

**Step 4 — Get the `user_id` from the connected account:**
The `user_id` field in the connected account response (e.g., `jake1`) must be appended
as a query parameter: `?user_id=jake1`.

**Step 5 — Update the profile's `config.yaml`:**
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
Note: `auth: oauth` is NOT used here — the `headers.x-api-key` replaces OAuth entirely.

**Step 6 — Verify:**
```bash
HERMES_HOME=/data/profiles/<profile> /opt/hermes/.venv/bin/hermes mcp test composio
# Expected: ✓ Connected, N tools discovered
```

Full API workflow documented in `references/railway-api-key-setup.md`.

## Connection Flow

1. Config is set with `auth: oauth` (Method A or B above)
2. Run `hermes mcp login composio` to trigger the OAuth handshake
3. MCP server connects → `mcp_composio_*` tools appear
4. User goes to [dashboard.composio.dev](https://dashboard.composio.dev)
5. "Connect App" → select platform → OAuth flow → authorize
6. Tools become usable (draft posts, pull analytics, etc.)

## Tool Discovery

Once the MCP server is connected, use `mcp_composio_SEARCH_COMPOSIO_TOOLS` to find
tools for a specific platform. Tools are prefixed as `mcp_composio_<PLATFORM>_<ACTION>`.

To keep context manageable, use `tools.include` in the config to whitelist only needed
tools — social media toolkits can expose 70+ tools per platform.

## Direct MCP Tool Calls via Terminal

When `defer_loading: true` prevents tools from appearing, or when scripting/testing,
call Composio's MCP endpoint directly with curl. Full patterns in `references/direct-tool-calls.md`.

**Critical transport quirks:**
- The base URL redirects (307) to `/mcp` subpath — tool calls MUST go to
  `https://backend.composio.dev/v3/mcp/<UUID>/mcp?user_id=<ID>`
- `Accept` header MUST include BOTH `application/json` AND `text/event-stream` — otherwise 400
- POST-only transport — GET/SSE is not supported (returns 405)
- Responses are SSE-wrapped: `event: message\ndata: <json>`
- The actual tool result is DOUBLE-encoded JSON inside `result.content[0].text`

**Tool call pattern:**
```bash
curl -sS -X POST \
  "https://backend.composio.dev/v3/mcp/<UUID>/mcp?user_id=<ID>" \
  -H "x-api-key: ${COMPOSIO_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

Use `tools/call` method with `name` and `arguments` to execute actions.
Facebook `GET_PAGE_POSTS` returns cursor-based pagination — pass `after` from
`data.paging.cursors.after` to fetch subsequent pages.

## Platform-Specific Notes

| Platform | Tools | Accounts | Key Limitation |
|---|---|---|---|
| Facebook | 39 | Pages only | Cannot post to personal profiles |
| X/Twitter | 78 | Any account | Free tier has strict rate limits |
| Instagram | 29 | Business/Creator | Must be linked to a Facebook Page |
| LinkedIn | 22 | Pages & profiles | Requires Marketing API scopes |
| TikTok | 10 | Business accounts | **Requires own developer credentials** |
| YouTube | 47 | Channels | Requires Google Cloud OAuth |

TikTok is the only major platform that **requires** your own developer credentials —
Composio does not provide a built-in OAuth app for it.

## Design/Creative Toolkits

Beyond social media posting, Composio offers design and content creation toolkits.
These are **template-based or AI-assisted**, not raw AI generation (no Midjourney/DALL-E/Stable Diffusion).

| Toolkit | Capability | Best Use Case | Content Type |
|---|---|---|---|
| **HeyGen** | AI avatar video generation; 120+ avatars; lip-sync; video translation | Marketing explainers, UGC-style ads, consistent brand spokesperson | Video (avatar) |
| **Bannerbear** | Template-based image/video rendering; API-driven creative automation | Branded social graphics from data; auto-generate post images from templates. **Primary use: automated text overlay on images for social posts.** Create a brand template once, then Hermes sends JSON (photo_url, headline, body, logo) → Bannerbear renders final branded image. Ideal for the \"photo + educational text\" social image post pipeline. | Image, Video |
| **Placid** | Branded image/PDF generation from templates; dynamic content insertion | Consistent brand graphics at scale; PDF generation | Image, PDF |
| **Abyssale** | Creative automation for images/videos/GIFs/PDFs; multi-format rendering | Multi-format campaign asset generation from single template | Image, Video, GIF, PDF |
| **Pictory** | AI video creation from scripts/articles; stock footage integration | Text-to-video; blog-to-video; educational explainers | Video |

**Key distinction:** These toolkits automate **production** (fill templates, render variants, generate from scripts). They do NOT generate novel photorealistic visuals. For raw AI image/video generation, use Hermes `image_generate` (FAL.ai with 11 models) and `video_generate` (xAI Grok Imagine, FAL Veo 3.1 — `video_gen` toolset, disabled by default). See `social-visual-content` skill for the full automated content creation pipeline.

## Multi-Client Agency Isolation

Composio scopes connected accounts by `user_id`. For agency use with multiple
clients, a single MCP URL per profile means one set of connected accounts.

**Recommended:** Create separate Hermes profiles per client, each with its own
Composio config/`user_id` and connected accounts.

## Composio as Sandboxed Capability Layer

Composio MCP tools provide external service access (social posting, analytics, content creation)
without exposing the local filesystem. This makes Composio the natural "creation path" for
restricted profiles — non-technical partners, clients, or team members who need to publish
content and check analytics but shouldn't be able to write files or run terminal commands.

**Pattern:** Disable `terminal` and other dangerous toolsets on the partner's profile, keep
`file` (for read-only context via SOUL.md + approvals.mode: always), and add Composio MCP
as the sole content-creation pathway. The partner can post to social, generate videos via
HeyGen, render graphics via Bannerbear, and check analytics — all through Composio's API,
never touching the server filesystem.

**Key config:** Each restricted profile needs its own Composio `user_id` and connected
accounts. Never share an MCP URL or API key across deployments. See `hermes-railway-setup`
skill → `references/restricted-profile-security.md` for the full recipe.

## Tool Call Pricing (June 2026)

| Tier | Calls/Month | Cost |
|---|---|---|
| Free | 20,000 | $0 |
| Pro | 200,000 | $29/mo |
| Business | 2,000,000 | $229/mo |

Estimate ~610 tool calls/client/month for moderate posting + analytics use.
Boutique agencies (5 clients) fit the free tier. Scale up from there.

## Pitfalls

- **`auth: oauth` is MISSING from config → 401 and no tools.** The composio.dev/hermes page says "Do not add any authentication headers — OAuth will be used automatically." This is true for *headers*, but Hermes still needs `auth: oauth` in the config block to know to initiate the OAuth handshake. Without it, `hermes mcp test composio` returns 401, and `hermes mcp login composio` says "Server 'composio' is not configured for OAuth (auth=None)". **Fix:** add `auth: oauth` to the `mcp_servers.composio` block, then run `hermes mcp login composio`.
- **Diagnostic: `hermes mcp login <name>` reveals missing auth config.** If it says "not configured for OAuth (auth=None)", the `auth: oauth` field is missing. If it succeeds, OAuth is configured and the flow begins.
- **Config is correct (including `auth: oauth`) but tools don't appear** → run `hermes mcp login composio` to trigger the OAuth flow. MCP servers connect at profile boot time, not on config file write.
- **OAuth PKCE fails on Railway / containerized deployments — use Method C instead.** The `hermes mcp login composio` flow redirects to `127.0.0.1:<port>/callback`. On Railway, the browser and Hermes CLI are in separate containers — the callback reaches the browser container's localhost, not Hermes'. This causes an indefinite hang/timout. **Fix:** use Method C (API key auth with `backend.composio.dev` endpoint). Do NOT attempt OAuth on Railway.
- **Direct MCP calls: URL must include `/mcp` subpath.** The config URL (`.../v3/mcp/<UUID>?user_id=X`) 307-redirects to `.../v3/mcp/<UUID>/mcp?user_id=X`. When calling tools via curl, you MUST post to the `/mcp` subpath directly — the 307 POST→GET behavior drops the body. **Fix:** append `/mcp` before `?user_id=`.
- **Direct MCP calls: dual Accept header required.** The endpoint requires `Accept: application/json, text/event-stream` — BOTH, not either. Missing one yields 400 "Not Acceptable."
- **Direct MCP calls: POST-only, not SSE streaming.** GET returns 405. No SSE handshake needed — just POST each tool call as a stateless JSON-RPC request. Response is SSE-wrapped with `event: message`.
- **Tool responses are double-encoded JSON.** The SSE `data` field is JSON, and `result.content[0].text` is a JSON string of the actual result. Parse twice or use the snippet in `references/direct-tool-calls.md`.
- **MCP server UUID + `user_id` must be exact.** The `mcp_url` from the API response lacks `?user_id=...` — you must append it from the connected account's `user_id` field. Missing or wrong `user_id` → tools appear but operate on the wrong account or return errors.
- **`connect.composio.dev/mcp` vs `backend.composio.dev/v3/mcp/...`** — the former is the Hermes-specific simplified endpoint (requires `auth: oauth`, no API key header). The latter is the generic SDK endpoint (requires `x-api-key` header, no `auth: oauth` field). Use the former for Hermes profiles.
- **Facebook = Pages only.** The toolkit cannot post to personal Facebook timelines. Read posts on pages you DON'T manage is also not possible through Composio — use the researcher profile (Camofox/Firecrawl) for public page scraping.
- **Instagram requires Business/Creator account** linked to a Facebook Page.
- **No Reddit or Threads toolkits** as of June 2026. Check composio.dev for updates.
- **Tool timeout for video uploads** — increase `timeout` to 180-300s for
  TikTok/YouTube video operations.
- **Rate limits are platform-level** — Composio handles retries but cannot
  bypass Twitter's 50 tweets/24h free-tier limit or Instagram's 25 posts/24h.

## References

- `references/research-findings.md` — Full researcher dump: auth models, pricing
  tiers, tool inventory, multi-client strategies, gotchas catalog
- `references/hermes-setup-instructions.md` — Verbatim instructions from
  composio.dev/hermes for AI agents
- `references/railway-api-key-setup.md` — Full recipe for API key auth on
  Railway and containerized deployments where OAuth PKCE cannot work
- `references/direct-tool-calls.md` — How to call MCP tools directly via curl:
  transport quirks, tool discovery, parsing double-encoded responses, pagination
- `templates/composio-agents-section.md` — AGENTS.md template for profiles
  with Composio MCP tools: MCP vs native paths, SEARCH_TOOLS discovery
  protocol, common pitfalls. Copy into any profile's AGENTS.md to prevent
  trial-and-error on tool selection.
