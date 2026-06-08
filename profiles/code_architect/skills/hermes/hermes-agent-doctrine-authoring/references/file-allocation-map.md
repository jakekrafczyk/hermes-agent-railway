# File Allocation Map — Extended Notes

This file backs the allocation table in SKILL.md with edge-case reasoning. Use
it when the table doesn't cleanly cover a piece of content the user wants to
add.

## The Layered Model

Hermes ships agent doctrine and credentials in concentric layers. The inner
rings are **per-profile**, not shared:

```
Default profile (HERMES_HOME=/data/):
┌─────────────────────────────────────────────────────┐
│  config.yaml          (BINDINGS — what runs)        │
│  ┌──────────────────────────────────────────────┐   │
│  │  /data/SOUL.md     (IDENTITY — who runs)     │   │
│  │  ┌────────────────────────────────────────┐  │   │
│  │  │  profile/AGENTS.md (DOCTRINE — how)   │  │   │
│  │  └────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────┘   │
│  /data/.env               (CREDENTIALS — API keys)   │
└─────────────────────────────────────────────────────┘

Named profile (HERMES_HOME=/data/profiles/researcher/):
┌─────────────────────────────────────────────────────┐
│  config.yaml          (BINDINGS — profile-specific)  │
│  ┌──────────────────────────────────────────────┐   │
│  │  profiles/researcher/SOUL.md (IDENTITY)      │   │
│  │  ┌────────────────────────────────────────┐  │   │
│  │  │  profiles/researcher/AGENTS.md         │  │   │
│  │  └────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────┘   │
│  profiles/researcher/.env (CREDENTIALS — per-profile)│
└─────────────────────────────────────────────────────┘
```

- **Outer ring (config.yaml):** infrastructure. Providers, models, MCP servers,
  paths, ports. Things the runtime reads to wire components together.
- **Next ring (SOUL.md):** identity — **per-profile, not shared.** Persona,
  voice, tone, hard rules. Loaded into every turn's system prompt from the
  active profile's `$HERMES_HOME/SOUL.md`. There is no fallback chain — a
  named profile never falls back to `/data/SOUL.md`. Profile creation auto-
  seeds a default SOUL.md from the generic template; this default is stale
  boilerplate unless the user customized it.
- **Inner ring (AGENTS.md):** doctrine — how a specific profile (researcher,
  copywriter, analyst) executes its class of work. Tool stacks, execution
  loops, reasoning style. **Not loaded by Hermes natively** (zero references
  in Hermes Python source) — loaded by workspace context injection in the
  web UI, Cursor, or Claude Code. Doctrine that must survive CLI/gateway/cron
  launches belongs in SOUL.md.
- **`.env` (credentials):** API keys and secrets. **Per-profile, no inheritance.**
  Each profile's `.env` is consumed independently by the Hermes runtime and
  tools. Missing a key in a named profile's `.env` does NOT fall back to
  `/data/.env`. Shared keys (e.g., same OpenRouter API key used by both
  profiles) must be duplicated in both files. Keep each `.env` minimal — only
  the keys that profile actually needs.

> **Security note:** `.env` files are credential containers, not doctrine.
> They should NEVER be read into the agent's context window (e.g., via
> `read_file`) — doing so sends the plaintext keys to the model provider.
> Hermes tooling (runtime, MCP servers) consumes `.env` through internal
> channels. If you need to verify which keys a profile's `.env` should contain,
> check what that profile's `config.yaml` references (e.g., `FIRECRAWL_API_KEY`,
> `__FIRECRAWL_API_KEY__` in MCP env blocks, `api_key_env` fields), then
> confirm the key exists via `terminal` (not `read_file`).

## Allocation Decision Tree

When deciding where new content goes, ask in order:

1. **Is it a provider/model/path/port the runtime needs?** → config.yaml
2. **Is it identity-level — persona, voice, tone, hard rules?** → the active
   profile's SOUL.md. If the identity rule applies to ALL profiles (e.g., a
   multi-tenant client isolation rule for the agency), it needs to be copied
   into each profile's SOUL.md — there is NO shared global SOUL.md fallback.
3. **Is it specific to one profile's class of work?** → that profile's AGENTS.md
4. **Is it a tool contract the persona itself depends on?** → SOUL.md
   (Supermemory is the canonical example for this user — the memory engine is
   so tightly coupled to the persona's token-economy rules that splitting them
   creates more confusion than it saves.)
5. **Otherwise** → AGENTS.md of the profile that uses it.

## Ambiguous Cases (and the user's resolutions)

### Model Routing Rules
- **Default home:** profile AGENTS.md, not SOUL.md.
- **Reasoning:** model routing is execution policy ("for sensitive phases switch
  to DeepSeek Pro"), not identity. Different profiles can have different
  routing rules. Keeping it in AGENTS.md lets each profile tune its own.

### Reasoning Effort / Style
- **Default home:** profile AGENTS.md.
- **Reasoning:** reasoning style is per-task-class. A researcher wants
  High-Structured determinism; a copywriter might want Very High creative.

### Tool API Contracts
- **Default home:** profile AGENTS.md.
- **Exception:** Supermemory v3 contracts live in SOUL.md because the persona's
  token-conservation rules directly reference memory operations.
- **Other tools (Firecrawl, Camofox, SearXNG):** AGENTS.md of the profile that
  uses them. If multiple profiles use them, the contracts can live in a shared
  reference file under `/data/references/` and each AGENTS.md links to it.

### Shared API Keys Across Profiles
- **Default home:** BOTH profiles' `.env` files (duplicate explicitly).
- **Reasoning:** there is no inheritance or fallback mechanism. Each profile's
  `.env` is consumed independently. If a key is needed by both, it must exist
  in both. If only one profile uses a key, only put it there — this minimizes
  risk of the wrong profile consuming the wrong credential.
- **Default home:** SOUL.md.
- **Reasoning:** applies to every profile and every tool call. It's identity-
  level, not task-level.

### Cache / Live-Data Overrides (e.g., Firecrawl `maxAge: 0`)
- **Default home:** the AGENTS.md that owns the tool contract.
- **Reasoning:** it's a runtime behavior of that specific tool, not a global
  persona rule.

## Anti-Patterns

- **"Just put everything in SOUL.md so it's always loaded."** No. SOUL is
  loaded every turn. Bloating it taxes every interaction. Profile AGENTS.md
  loads only when the relevant profile is active.

- **"Just put everything in config.yaml."** config.yaml is parsed by the
  runtime, not the agent. The agent doesn't read it as instruction — it reads
  it as configuration. Behavioral rules belong in SOUL/AGENTS.

- **"Share one `.env` across profiles via symlink or env_passthrough."**
  Each profile's `.env` is independent by design. Sharing credentials this
  way creates a hidden coupling that breaks when the profiles diverge. Duplicate
  shared keys explicitly; keep profile-only keys in that profile's `.env` only.

- **"Duplicate it across files for safety."** Duplication causes drift. When
  one copy is edited and the others aren't, the agent gets contradictory
  instructions and chooses inconsistently. Single source of truth.

## When the User Overrides This Map

The user is the source of truth for their own deployment. When they explicitly
direct content somewhere ("move all model routing to AGENTS", "put supermemory
contracts in SOUL"), follow them. Update this skill's allocation map if their
directive reveals a stable preference (e.g., they've made the same call twice).
