# Self-Sufficient Profile Pattern

When `auto_recall` is disabled (token-efficient), a profile must carry its own
awareness of the deployment so it can make architectural decisions without
relying on Supermemory prefetch. This reference documents the three-part
pattern that achieves that.

## Why

- `auto_recall=true` burns up to 40k input tokens/turn via Supermemory prefetch.
- `auto_recall=false` is the token-efficient default, but the profile starts
  "blind" — no memory context is injected.
- The Infrastructure Atlas + Current State + Session Startup Protocol pattern
  replaces auto_recall with ~2-3k tokens of deliberate reads, giving the
  profile MORE awareness at LOWER cost.

## The Three Parts

### Part 1: Infrastructure Atlas (`# Infrastructure Atlas`)

A hard-coded section in SOUL.md with tables of immutable or rarely-changing
facts about the deployment. Four sub-tables:

**Service Endpoints** — every service the profile depends on:
| Service | Host:Port | Notes |

**Key File Paths** — every config file the profile needs to read before editing:
| Path | What | When to read |

**Profile Inventory** — every profile in the deployment:
| Profile | Path | Configuration files |

**Installed Plugins** — every plugin in `/data/plugins/` with version:
| Plugin | Path | Version |

**config.yaml Key Settings** — the ~10 most important config keys the profile
frequently references (memory provider, delegation limits, Camofox port, etc.)

Rules for the Atlas:
- Facts that change rarely (< once per month) live here.
- Update after every plugin install, profile creation, or service hostname change.
- Keep in tables — dense, scannable, token-efficient.

### Part 2: Current State (`## Current State`)

A bullet list of MUTABLE state — things that change with configuration work.
This is the "what" the profile needs to know that isn't in the hard-coded atlas.

Format: each line is a fact + dash + date confirmed.
```
- `voltaic_code_architect` container is empty (0 memories stored) — confirmed 2026-05-29
- Multi-container mode enabled — `voltaic_code_architect` is an allowed tag
- `auto_recall` is `false` (intentional — avoids 40k token prefetch burn)
```

Rules:
- Update after EVERY config change. The profile MUST keep this current.
- Date-stamp confirmations so future sessions know how fresh the fact is.
- If a fact is confirmed but the state is different now, update both the fact
  AND the date.

### Part 3: Session Startup Protocol (`# Session Startup Protocol`)

A numbered checklist the profile follows at the start of any session where
it's about to make changes:

1. **Read current config** — `read_file("/data/config.yaml")` on relevant section
2. **Check plugin inventory** — `search_files(pattern="plugin.yaml", path="/data/plugins")`
3. **Verify profile state** — read target profile's config.yaml + grep .env
4. **Check architecture memory** — `supermemory_search` in the arch container
5. **Validate against docs** — `read_file` on compact doc indexes

This 5-step protocol costs ~2-3k tokens and replaces `auto_recall=true`.
After ANY config change, update Current State so future sessions stay accurate.

## Token Math

| Approach | Token cost per session |
|---|---|
| `auto_recall=true` with Supermemory prefetch | up to 40k (prefetch path bypasses caps) |
| Infrastructure Atlas (hard-coded in SOUL.md) | ~1k (already part of SOUL.md prompt injection) |
| Session Startup Protocol (5 deliberate reads) | ~2-3k (read_file + search_files calls) |
| **Total: Atlas + Protocol** | **~3-4k** (vs 40k for auto_recall) |

## Prerequisites

For this pattern to work, the profile needs:
1. **Multi-container supermemory** — `enable_custom_container_tags: true` with
   `custom_containers: ["profile_specific_tag"]` so architecture facts don't
   pollute the general `voltaic` namespace.
2. **Compact doc indexes** at `/data/system/reference/` — the 135-line
   `hermes_llms.txt` and 134-line `supermemory_llms.txt` for on-demand docs lookup.
3. **Profile-specific SOUL.md** — the Atlas is per-profile; each profile carries
   its own endpoints, paths, and config keys.

## When to Use

Apply this pattern when:
- `auto_recall` is set to `false` (the token-efficient default).
- The profile is expected to make filesystem/config changes without user guidance.
- The deployment has 3+ services that the profile needs to know about.
- Multiple profiles share infrastructure (SearXNG, Camofox, Firecrawl).

Do NOT apply when:
- `auto_recall` is `true` and working well.
- The profile is read-only (answers questions, never edits config).
- The deployment is a single service with no cross-profile concerns.
