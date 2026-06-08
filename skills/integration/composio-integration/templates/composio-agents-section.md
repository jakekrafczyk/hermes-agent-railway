# Composio MCP Operations

Your Facebook tools are available as `mcp_composio_FACEBOOK_*`. There are two calling paths:

- **MCP (direct):** `mcp_composio_FACEBOOK_CREATE_POST(page_id=..., message=...)` — typed parameters, best for known tools
- **Native (router):** `mcp_composio_COMPOSIO_EXECUTE_TOOL(action="FACEBOOK_CREATE_POST", params={...})` — one function, pass tool name as string

Prefer MCP for routine operations (typed parameters catch errors early). Use native only when
the tool list is too large for context or when calling tools you haven't preloaded.

## Discovery (No Trial-and-Error)

**Full tool reference:** https://docs.composio.dev/toolkits/composio — 24 Composio meta-tools
plus per-platform toolkits with parameter schemas.

Before any platform action:
1. `mcp_composio_COMPOSIO_SEARCH_TOOLS` — describe what you want in plain English, get exact tool name
2. `mcp_composio_COMPOSIO_GET_TOOL_SCHEMAS` — get required parameters for that tool
3. Only then call the platform tool

## Common Pitfalls

- **Page IDs are numeric strings** (e.g., "123456789"), not names. Use `FACEBOOK_LIST_MANAGED_PAGES` to get them.
- **Image URLs must be HTTPS.** Local file paths fail. Use `FACEBOOK_UPLOAD_PHOTOS_BATCH` for direct upload.
- **`FACEBOOK_DELETE_POST` is excluded** at config level — cannot be called.
- **Facebook only for now.** Twitter/LinkedIn/Instagram/etc. are not yet connected.

**Default behavior: DRAFT FOR REVIEW.** Do NOT call publishing tools unless the task brief
sets `auto_publish: true`. Always draft to the inbox task file first.
