# Supermemory SDK v3.45.0 — API Version Map

Discovered 2026-06-04 during Supermemory fix review. The SDK (v3.45.0, installed
via `pip3 install supermemory` into `/opt/hermes/.venv`) uses **mixed v3/v4
endpoints** — not a single API version. This is important for direct API calls
and understanding the plugin's behavior.

## Endpoint Map

| SDK Method | API Path | Version | Notes |
|---|---|---|---|
| `client.documents.add()` | `/v3/documents` | v3 | Stores new memories |
| `client.documents.list()` | `/v3/documents/list` | v3 | Lists documents by container |
| `client.documents.batch()` | `/v3/documents/batch` | v3 | Batch operations |
| `client.search.memories()` | `/v4/search` | v4 | Semantic search (what the plugin uses) |
| `client.memories.forget()` | `/v4/memories` | v4 | Delete by ID |
| `client.profile()` | `/v4/profile` | v4 | Profile recall + search |
| `client.connections.*` | `/v3/connections/*` | v3 | All connection endpoints |
| `client.settings.*` | `/v3/settings` | v3 | Settings endpoints |

## Plugin Hardcoded Endpoints

The governed plugin at `/data/plugins/supermemory_governed/__init__.py` hardcodes:

| Constant | Value | Line |
|---|---|---|
| `_CONVERSATIONS_URL` | `https://api.supermemory.ai/v4/conversations` | 41 |

## Base URL Resolution

The SDK resolves its base URL in this priority order (`_client.py` lines 113-116):

1. `base_url` kwarg passed to `Supermemory()` constructor
2. `SUPERMEMORY_BASE_URL` environment variable
3. Hardcoded default: `https://api.supermemory.ai`

The governed plugin's `_SupermemoryClient.__init__()` (line 272) calls
`Supermemory(api_key=api_key, timeout=timeout, max_retries=0)` — **no base_url
passed**. The `config.yaml` key `supermemory.api_base` is **vestigial** — neither
the plugin nor the SDK reads it.

## ID Space Mismatch

Documents stored via `/v3/documents` and memories retrieved via `/v4/memories`
use **different ID spaces**. A document ID from `client.documents.add()` cannot be
used with `client.memories.forget()` — it returns 404. This is a known SDK
inconsistency; not critical for production since the plugin never calls
`forget()` by document ID.

## Version Implications

- **v3 endpoints (documents, connections, settings):** stable, used for CRUD
- **v4 endpoints (search, memories, profile):** semantic search with hybrid mode
- **Plugin operations:** `add_memory()` → v3 documents, `search_memories()` → v4
  search, `get_profile()` → v4 profile, `forget_memory()` → v4 memories, session
  ingest → v4 conversations
- **No conflict:** the mixed versions work correctly because each resource
  class manages its own path independently
