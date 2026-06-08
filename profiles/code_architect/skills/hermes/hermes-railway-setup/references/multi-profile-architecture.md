# Multi-Profile Architecture on Railway

## Profile Filesystem Layout

On Railway, `HERMES_HOME=/data` — the single volume mount point. Profiles live at
`/data/profiles/<name>/`. Each profile has isolated Hermes state (config.yaml,
.env, SOUL.md, AGENTS.md, sessions, skills, memories) but they share the SAME
filesystem, workspace, Kanban DB, and Supermemory container.

```
/data/
├── config.yaml              ← default profile config
├── .env                     ← default profile env
├── SOUL.md                  ← global persona (loaded every turn)
├── .hermes/
│   └── webui/               ← webui state
├── profiles/
│   ├── default/             ← orchestrator profile
│   │   ├── config.yaml
│   │   ├── .env
│   │   ├── SOUL.md
│   │   ├── AGENTS.md
│   │   ├── sessions/
│   │   ├── skills/
│   │   └── memories/
│   └── researcher/          ← worker profile
│       ├── config.yaml
│       ├── .env
│       ├── SOUL.md
│       ├── AGENTS.md          ← deterministic execution loop
│       ├── sessions/
│       ├── skills/
│       └── memories/
├── workspace/
│   └── triage/              ← universal task handoff (inbox/in_progress/resolved/archive)
│       ├── .task-format.md    ← markdown output format spec
│       ├── task_requests/     ← orchestrator writes task briefs for worker
│       │   └── consumed/      ← worker archives read briefs
│       ├── inbox/             ← worker writes completed/error task files
│       ├── in_progress/       ← orchestrator claims tasks while processing
│       ├── resolved/          ← completed with resolution appended (30-day retention)
│       └── archive/           ← >30-day items moved from resolved/
└── camofox/cookies/         ← shared cookie store
```

**Key implication:** Profiles are isolated at the Hermes state layer, NOT at the
filesystem layer. Any profile can read/write `/data/workspace/`. This is by
design — it makes cross-profile coordination trivial since everything lives on
one volume.

## Coordination Architecture: File Inbox + Supermemory

Two mechanisms, not four. Kanban adds token burn (full agent session per worker
spawn) and requires a gateway daemon for dispatch. The file-based inbox has no
infrastructure dependency beyond cron.

### Mechanism 1: File-Based Task Inbox (Universal)

The `/data/workspace/triage/` folder handles ALL task types — errors, research
findings, scraped data, analysis, reports. One inbox, one processing loop.

**Files are markdown (`.md`) with YAML frontmatter — not JSON.** The old
JSON schema (`.schema.json`) is deprecated in favor of `.task-format.md`.

**Directory contract:**
| Directory | Who writes | Who reads | Purpose |
|---|---|---|---|
| `task_requests/` | Orchestrator | Worker | New research briefs |
| `inbox/` | Worker | Orchestrator (cron) | Completed task output |
| `in_progress/` | Orchestrator | Orchestrator | Being processed |
| `resolved/` | Orchestrator | Orchestrator | Done, 30-day retention |
| `archive/` | Orchestrator | Orchestrator | Long-term record |

**Orchestrator cron:** polls `inbox/` every 5 minutes. Acts based on
`output_type` frontmatter field. Appends `## Resolution` section and moves
to `resolved/`. Silent when empty.

### Mechanism 2: Supermemory as Shared Context Bus

Both profiles share a Supermemory container tag (`voltaic`). Worker commits
every external retrieval before writing task output. Orchestrator's context
pre-fetch surfaces relevant memories automatically.

**Cross-profile memory sharing:**
- Researcher writes findings → `supermemory_store(container_tag="voltaic")`
- Orchestrator reads → `supermemory_search(container_tag="voltaic")`
- Multi-container mode (`enable_custom_container_tags: true`) allows both
  private and shared tags
- Scoped API keys can be assigned to multiple container tags (March 2026)

**Config (`/data/supermemory.json`):**
```json
{
  "container_tag": "voltaic",
  "enable_custom_container_tags": false,
  "auto_recall": false,
  "auto_capture": true,
  "search_mode": "hybrid"
}
```

Set `auto_recall: false` to avoid runaway token burn from prefetch injection.

### Why Not Kanban

Kanban was evaluated and rejected for this use case:
- **Token cost:** every dispatcher worker spawn is a full agent session
- **Infrastructure:** requires gateway daemon (`START_GATEWAY=true`)
- **Overhead:** 60s polling, dashboard UI that profiles-as-workers never see
- **Simplicity:** file-based inbox has zero new moving parts beyond cron

## Railway Volume Constraints

| Constraint | Impact |
|---|---|
| 1 volume per service | All profiles share `/data` — no isolated volumes per profile |
| Free plan: 1 volume per project | Can't spin up independent Hermes instances as separate services |
| Hobby: 10 volumes | Could run up to 10 Hermes services with isolated volumes |
| Pro: 20 volumes, up to 1TB each | Flexible for scaling |
| No replicas with volumes | Single instance, downtime on redeploy |

## Task Coordination Flow

```
1. Orchestrator writes task brief  →  task_requests/task_<uuid>.md
2. Worker polls task_requests/ on session start
3. Worker moves consumed brief     →  task_requests/consumed/
4. Worker executes deterministic loop
5. Worker writes output            →  inbox/task_<uuid>.md
6. Orchestrator cron processes inbox file:
   - error_state  →  diagnose, apply fix_hint, verify
   - other        →  validate, store to Supermemory, archive
7. Orchestrator appends ## Resolution
8. Orchestrator moves file         →  resolved/
```

## Git-Based Profile Sync for Partner Sharing

Each partner deploys their OWN Railway project from the repo. They do NOT share
your `/data` volume. To keep profile configs in sync across deployments:

### Setup
1. **Fork** `protemplate/hermes-agent-railway` → your GitHub account
2. **Add `profiles/` directory** to the repo with subdirectories per profile
3. **Entrypoint copies profiles on boot** (extends existing skill-sync pattern
   at lines 216-224 of entrypoint.sh):
   ```bash
   if [ -d "/opt/hermes-railway/profiles" ]; then
     for profile_dir in /opt/hermes-railway/profiles/*/; do
       profile_name="$(basename "${profile_dir}")"
       mkdir -p "${HERMES_HOME}/profiles/${profile_name}"
       cp -R "${profile_dir}"/* "${HERMES_HOME}/profiles/${profile_name}/"
     done
   fi
   ```
4. **Secrets stay out of git** — `.env` files with API keys are set via Railway
   environment variables per-instance, not committed
5. **Partner deploys from YOUR fork** — gets the same profile structure
6. **You push to main → partner pulls → redeploys** — profiles update

### GitHub Access for Agent Editing
To let the agent push changes to the repo:
1. Fork the template repo to your GitHub account
2. In Railway, reconnect the service to YOUR fork (Settings → Source Repo)
3. Generate a GitHub Personal Access Token (classic) with `repo` scope
4. Provide the repo URL and token to the agent

### What NOT to put in git
- `.env` files (API keys, tokens)
- `auth.json` (OAuth credentials)
- `sessions/` (chat history)
- `memories/` (potentially sensitive memory data)
- `skills/.usage.json` (per-instance usage tracking)