# MCP Tool Guardrails vs. Cloud API Reality

**Date:** 2026-06-04  
**Example:** Firecrawl `firecrawl_parse` MCP tool

## The Pattern

An MCP tool returns an error like:
```
firecrawl_parse requires FIRECRAWL_API_URL to be set to a self-hosted Firecrawl API instance.
```

The orchestrator interprets this as "Firecrawl doesn't support local file parsing" and falls through to local extractors (pymupdf → marker-pdf). Seven attempts and 30+ minutes later, the user points to the official docs and shows the cloud API supports `/v2/parse` natively.

## The Anti-Pattern

```
MCP tool error → "this capability is unavailable" → fall back to local alternatives
```

## The Correct Pattern

```
MCP tool error → "this MCP tool has a constraint" → check official docs → use direct API if available
```

## When This Applies

Any MCP tool that wraps a cloud API may have tighter constraints than the underlying API:
- `firecrawl_parse` requires self-hosted URL → cloud API doesn't
- Similar patterns could exist for other MCP tools (Composio, etc.)

## The Fix

1. **Don't trust the MCP tool's error message as a capability statement.** It's a tool constraint, not an API limitation.
2. **Check the official docs** for the underlying service before assuming a capability is missing.
3. **Bypass the MCP tool** with a direct API call (curl, Python requests) when the cloud API supports what the MCP tool blocks.
4. **Update the relevant skill** with the working approach so future sessions don't replay the failure.

## Cost of Getting This Wrong

- 8 failed attempts across pymupdf and marker-pdf
- ~30 minutes of wall clock time
- 14-credit Firecrawl call that should have been the first attempt
- User frustration ("looks like you have hit an error. stop what you were doing")