# Composio MCP — Direct Tool Calls via curl

When the Hermes MCP bridge isn't loading tools (e.g., `defer_loading: true`), or when you need to
call tools from a terminal/script, you can call Composio's MCP endpoint directly via HTTP.

## Transport Quirks (Discovered June 2026)

| Quirk | Detail |
|---|---|
| **URL subpath** | Base URL `.../v3/mcp/<UUID>?user_id=X` → 307 redirects to `.../v3/mcp/<UUID>/mcp?user_id=X`. Tool calls MUST use the `/mcp` subpath. |
| **Accept header** | MUST include BOTH: `application/json, text/event-stream`. Omitting either returns 400 "Not Acceptable". |
| **Transport** | POST-only for tool calls. GET/SSE streaming is NOT supported — returns 405. |
| **Response format** | SSE-wrapped (even though it's not streaming): `event: message\ndata: <json>` |
| **JSON-RPC** | Standard MCP JSON-RPC 2.0: method `tools/list`, `tools/call`, or `initialize`. |

## Tool Discovery — List All Tools

```bash
curl -sS -X POST \
  "https://backend.composio.dev/v3/mcp/<UUID>/mcp?user_id=<USER_ID>" \
  -H "x-api-key: ${COMPOSIO_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

The response is SSE-wrapped:
```
event: message
data: {"result":{"tools":[{...tool schemas...}]},"jsonrpc":"2.0","id":1}
```

## Tool Call — Execute an Action

```bash
curl -sS -X POST \
  "https://backend.composio.dev/v3/mcp/<UUID>/mcp?user_id=<USER_ID>" \
  -H "x-api-key: ${COMPOSIO_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "FACEBOOK_GET_PAGE_POSTS",
      "arguments": {
        "page_id": "590703600800367",
        "fields": "id,message,created_time,permalink_url,reactions.summary(true),comments.summary(true)",
        "limit": 50
      }
    }
  }'
```

Response (SSE-wrapped):
```
event: message
data: {"result":{"content":[{"type":"text","text":"<JSON-encoded result>"}],"isError":false},"jsonrpc":"2.0","id":2}
```

The actual data is JSON-stringified inside `content[0].text` — pipe through `python3 -m json.tool` twice or use `jq`.

## Parsing the Response

The response is double-encoded: the SSE `data` field is JSON, and `result.content[0].text` is
also a JSON string. To extract:

```bash
curl ... | grep '^data: ' | sed 's/^data: //' | python3 -c "
import sys, json
data = json.load(sys.stdin)
text = data['result']['content'][0]['text']
print(json.dumps(json.loads(text), indent=2))
"
```

## Pagination

Facebook GET_PAGE_POSTS returns paging cursors in `data.paging.cursors.after`. Pass as the
`after` argument in a follow-up call. When the same results come back, pagination is exhausted.

## Connected Accounts via REST API

Separate from MCP tool calls — use Composio's REST API:

```bash
curl -sS -H "x-api-key: ${COMPOSIO_API_KEY}" \
  "https://backend.composio.dev/api/v3.1/connected_accounts" | python3 -m json.tool
```

Key fields: `id` (connected account ID), `toolkit.slug`, `user_id`, `status`, `auth_config.id`.

## Common Tasks

### List managed Facebook pages
```
FACEBOOK_LIST_MANAGED_PAGES  →  arguments: {fields: "id,name,category,about,link,picture"}
```

### Get page posts (with engagement)
```
FACEBOOK_GET_PAGE_POSTS  →  arguments: {
  page_id: "590703600800367",
  fields: "id,message,created_time,permalink_url,attachments,reactions.summary(true),comments.summary(true)",
  limit: 50
}
```

### Check if more pages exist (pagination)
```
FACEBOOK_LIST_MANAGED_PAGES → arguments: {fields: "...", limit: 50}
```
If `paging.cursors.after == paging.cursors.before` with only 1 page, no more pages.
