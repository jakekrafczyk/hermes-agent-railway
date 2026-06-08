# Voltaic Triage Error State Format

Used by the `researcher` profile to report unrecoverable errors. The Voltaic Marketing
agent monitors `/data/workspace/triage/inbox/` and resolves errors.

## Schema

Full schema at `/data/workspace/triage/.schema.json`. Required fields:

| Field | Type | Description |
|-------|------|-------------|
| `profile` | string | Profile name (e.g., "researcher") |
| `error_id` | string (UUIDv4) | Deduplication and tracking |
| `timestamp` | string (ISO8601) | When the error was triggered |
| `error_type` | string | One of: auth_gate, rate_limit, parse_fail, connection_error, timeout, ssl_error, model_error, tool_unavailable, unknown |
| `severity` | string | blocking, degraded, or warning |

## Directory Contract

| Directory | Who writes | Who reads | Purpose |
|-----------|-----------|-----------|---------|
| `inbox/` | Worker profiles | Voltaic agent | New error states to fix |
| `in_progress/` | Voltaic agent | Voltaic agent | Errors being diagnosed |
| `resolved/` | Voltaic agent | Voltaic agent | Fixed errors (30-day retention) |

## Naming Convention

`error_state_<uuid>.json` — UUID must match the `error_id` in the payload.

## Minimal Example

```json
{
  "profile": "researcher",
  "error_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-05-22T00:30:00Z",
  "error_type": "tool_unavailable",
  "severity": "blocking",
  "step": "C",
  "context": "Camofox not running — CAMOFOX_URL unset, localhost:9377 unreachable",
  "fix_hint": "Start Camofox service, set CAMOFOX_URL, populate /data/camofox/cookies/"
}
```

## After Triaging

When the task halts, immediately inform the operator that:
1. An error state has been written to `/data/workspace/triage/inbox/`
2. The Voltaic agent will pick it up for resolution
3. No further action is taken until the error is resolved