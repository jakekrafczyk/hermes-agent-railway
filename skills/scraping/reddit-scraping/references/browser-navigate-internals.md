# How `browser_navigate` Works Under the Hood

Source: `/opt/hermes/tools/browser_tool.py` (3,796 lines). This reference
covers the internals relevant to scraping — security layers that might
block you, auto-snapshot behavior you can rely on, and session isolation.

## Security Layers (executed in order, pre-navigation)

1. **Secret exfiltration guard** — regex-scans raw AND URL-decoded URLs for
   API key patterns. Blocks immediately if found.

2. **SSRF protection** — blocks private/internal addresses (RFC 1918,
   loopback, link-local, CGNAT 100.64.0.0/10). Skipped for local backends
   (headless Chromium without cloud provider). Always blocks cloud metadata
   endpoints (169.254.169.254) regardless.

3. **Website policy check** — calls `check_website_access(url)` against
   configurable blocklists.

4. **Post-redirect SSRF re-check** — if the browser followed a redirect to a
   private address, navigates to `about:blank` and blocks the result.

5. **Bot detection scan** — scans the page title for patterns like
   "access denied", "captcha", "cloudflare", "just a moment", etc. Emits a
   `bot_detection_warning` field in the response if triggered.

## Backend Routing

The tool auto-selects a backend in this priority order:

| Priority | Backend | Trigger |
|----------|---------|---------|
| 1 | **Camofox** | `CAMOFOX_URL` env var set — REST API to anti-detection browser |
| 2 | **CDP override** | `BROWSER_CDP_URL` or `browser.cdp_url` config — direct Chrome DevTools Protocol |
| 3 | **Cloud provider** | Browserbase, Browser Use, or Firecrawl plugin detected |
| 4 | **Local Chromium** | Headless, via `agent-browser` CLI |

**Hybrid routing**: when a cloud provider is active but the URL resolves to
a private address, the tool auto-spawns a local Chromium sidecar (keyed as
`task_id::local`) while keeping the cloud session alive for public URLs.
Controlled by `browser.auto_local_for_private_urls` (default: true).

## Auto-Snapshot

After every successful `browser_navigate`, the tool **automatically** runs
`agent-browser snapshot -c` (compact mode) and includes the accessibility
tree in the response under the `snapshot` field. This means:

- You do NOT need a separate `browser_snapshot` call after navigation.
- The snapshot uses ARIA accessibility tree format with `@e1`, `@e5`, etc.
  ref IDs for interactive elements.
- Snapshots over ~8,000 characters are truncated (LLM-summarized on full
  `browser_snapshot` calls, but NOT on the auto-snapshot from navigate).

The auto-snapshot appears in the response as:
```json
{
  "success": true,
  "url": "...",
  "title": "...",
  "snapshot": "- list:\n  - listitem:\n    - link ... [@e1]",
  "element_count": 42
}
```

## Session Isolation

Sessions are isolated by `task_id`. Each `task_id` gets its own browser
context (separate cookies, localStorage, etc.). The `_last_active_session_key`
dict tracks which session key (`task_id` or `task_id::local`) served the
last navigation, so `browser_snapshot`, `browser_click`, `browser_console`,
etc. automatically hit the right session.

## Stealth Features

On the first navigation for a session, the response includes:
- `stealth_features`: array of active features (e.g., `["proxies", "advanced_stealth"]`)
- `stealth_warning`: emitted when residential proxies are NOT active

These are relevant when scraping sites with aggressive bot detection.

## Command Timeout

Default 30s, configurable via `browser.command_timeout` in `config.yaml`.
Navigations get a floor of 60s. The config value is cached for the process
lifetime.

## `browser_console` with Expression

The `expression` parameter of `browser_console` evaluates JavaScript in
the page context (like DevTools console) and returns the serialized result.
This is what the reddit-scraping skill uses to run DOM extraction queries.
It uses `agent-browser eval` under the hood for local/cloud backends, or
the Camofox REST API `POST /eval` for Camofox mode.