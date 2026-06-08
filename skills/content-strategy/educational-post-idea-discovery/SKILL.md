---
name: educational-post-idea-discovery
description: Orchestrator workflow for discovering educational social media post ideas by combining brand context with research from Reddit, local forums, and local SEO data. Researcher agent gathers raw intelligence → orchestrator synthesizes with brand context → presents ranked ideas to user for approval → delegates to social_media for creation. Produces both image+text and text-only post ideas.
triggers:
  - User asks to "find post ideas" for a client
  - User mentions Reddit research for content ideas
  - "What should we post about?"
  - User mentions "local forum" or "Nextdoor" or "community research" for content
  - User asks to "combine brand context with research" for post ideas
  - Any request to generate a batch of educational social media post concepts
---

# Educational Post Idea Discovery

Orchestrator-level workflow. Coordinates the researcher profile → orchestrator synthesis → user approval → social_media creation pipeline. Discovers educational post ideas from real community conversations (Reddit, local forums, local SEO), not from guesswork.

## When to Use

The user wants a batch of post ideas for a client. They don't want to brainstorm from scratch — they want data-backed ideas sourced from what the target audience is actually talking about right now.

## Workflow Phases

```
PHASE 1: RESEARCHER → gathers raw intelligence
PHASE 2: ORCHESTRATOR → synthesizes with brand context, ranks ideas
PHASE 3: USER → reviews and approves specific ideas
PHASE 4: SOCIAL_MEDIA → creates approved posts (image+text or text-only)
```

---

## Phase 1 — Delegate Research

Create a task brief for the researcher profile. The brief must include:
- Client name, industry, location, target audience
- Specific research targets
- Output format

### Task Brief Template

```yaml
---
task_id: <uuid>
assignee_profile: researcher
assignee_domain: research
created_at: '<ISO 8601>'
task_type: research
priority: normal
approval_gates: output_only
---

# Task: Educational Post Idea Research for <Client>

## Context
<Client> is a <industry> serving <location/region>. Target audience: <demographics>.
We need raw intelligence to generate educational social media post ideas.

## Scope — What to Research

### 1. Reddit (highest priority)
Search these subreddits for recent discussions, questions, pain points:
- Local city/region subreddits (e.g., r/Cleveland, r/<city>)
- Industry-specific subreddits (e.g., r/healthcare, r/smallbusiness)
- Adjacent interest subreddits (e.g., r/personalfinance for financial services, r/homeowners for home services)
- Use Reddit search with keywords: <industry terms>, <local terms>, "recommend", "looking for", "anyone else", "frustrated with", "best way to"

For each relevant post/thread found:
- Title, subreddit, upvote count, comment count
- Key pain points or questions expressed
- Top 3 comments (highest upvoted)
- Sentiment: frustrated / curious / seeking advice / sharing experience

### 2. Local Forums & Community Platforms
- Nextdoor (public posts in the client's service area)
- Local Facebook community groups (public posts only)
- City-data.com forums for the target region
- Local Patch.com or neighborhood news sites
- Any hyperlocal discussion platforms in the service area

For each relevant discussion:
- Platform, location, date
- Topic and key concerns discussed
- Recurring themes or frequently asked questions

### 3. Local SEO & Search Intent
- Common "near me" searches related to the client's industry in their service area
- Google "People Also Ask" questions for: <industry> <location>, <industry> <common pain point>
- Seasonal search trends (e.g., Google Trends for <industry> in <region>)
- Competitor content gaps — what are competitors NOT answering?

### 4. Pain Points & FAQs
- What questions does the target audience ask repeatedly?
- What misconceptions exist about the industry?
- What decisions are people struggling with?
- What would someone new to this service/product need explained?

## NOT in Scope
- Do NOT generate post ideas — just gather raw conversations and data points
- Do NOT analyze competitor creative or ad strategy
- Do NOT scrape gated/private content

## Output Format
Write to `/data/workspace/triage/inbox/task_<uuid>_idea_research.md`
- YAML frontmatter: output_type: research_findings, status: complete, profile: researcher
- Section: ## Reddit Findings (per subreddit)
- Section: ## Local Forum Findings
- Section: ## Local SEO & Search Intent
- Section: ## Pain Points & FAQ Themes
- Include URLs, dates, upvote/engagement counts where available
```

### Delegation

Use `delegate_task` with toolsets: `["web", "search", "file"]` — these are verified valid Hermes toolsets. Add the `reddit-scraping` skill reference in the context so the researcher loads it if available (it exists at `/data/skills/scraping/reddit-scraping/SKILL.md`).

**Research context to pass:** Include that `reddit-scraping` skill is available, but also instruct the researcher to fall back to `web_search` with Reddit domain filters (`site:reddit.com/r/smallbusiness`) and search snippet analysis if direct extraction is blocked. Reddit frequently blocks Firecrawl, web_extract, and headless browsers — search snippets from titles and descriptions are valid intelligence when full thread extraction fails.

---

## Phase 2 — Synthesize & Rank

After the researcher returns findings, the orchestrator synthesizes them into post ideas. Do NOT delegate this — the orchestrator does this synthesis.

### Synthesis Process

1. **Extract themes** from researcher findings — group related pain points, questions, and conversations
2. **Cross-reference with brand context** — what can the client actually speak to? What's their unique angle?
3. **Rank by audience demand** — which topics have the most community activity? Most upvotes? Most repeated questions?
4. **Assign format** — does this work better as image+text or text-only?

### Idea Card Format

Each idea should be presented as:

```
### Idea N: [Headline — the hook]

**Source:** [Where this came from — subreddit thread, local forum, SEO data]
**Audience signal:** [Why we know people care — upvotes, comment volume, search volume]
**Format:** Image+Text | Text-Only
**Content angle:** [The educational approach — explainer, myth-bust, comparison, how-to, etc.]

**Suggested caption direction:**
[Hook sentence]
[2-3 sentence body direction]
[CTA direction]

**Visual concept (if image+text):**
[What the image should show — scene, mood, text placement]
```

### Ranking Criteria

| Factor | Weight | How to Assess |
|--------|--------|---------------|
| Audience demand | 40% | Upvotes, comment volume, search volume, recurrence across platforms |
| Brand alignment | 30% | Can the client credibly speak to this? Does it differentiate them? |
| Timeliness | 15% | Seasonal? Trending? Evergreen? |
| Visual potential | 15% | Can this be a compelling image? Or is it text-only? |

---

## Phase 3 — Present to User

Use `clarify` to present the ranked ideas. Format:

"Found [N] post ideas from [Reddit, forums, SEO]. Here they are ranked by audience demand × brand alignment:"

Present each idea card (up to 8 max per batch). Then:

"Which should I send to the social_media profile to create? (Select numbers, e.g., '1,3,5,7')"

Wait for user approval before Phase 4.

---

## Phase 4 — Delegate to Social Media

For each approved idea, create a task brief for the social_media profile:

```yaml
---
task_id: <uuid>
assignee_profile: social_media
assignee_domain: social
created_at: '<ISO 8601>'
task_type: post_generation
priority: normal
approval_gates: output_only
---

# Task: Create [Image+Text | Text-Only] Post — <Idea Headline>

## Context
Client: <client>
Platform: Facebook (can be adapted for Instagram)
Post type: <image | text_only>

## Content Direction
- Hook: <hook sentence>
- Body direction: <body direction>
- CTA: <cta direction>
- Hashtags: <suggested>

## Visual Direction (if image post)
<Visual concept description>

## Source
This idea came from: <Reddit thread URL / forum / SEO finding>

## Instructions
1. Load the `social-image-post-pipeline` skill (if image post) or create text-only
2. Generate the post using brand voice from Supermemory ({active_client}_social)
3. Write output to /data/workspace/triage/inbox/
4. Do NOT auto-post — output for human review only
```

---

## Full Example — Healthcare Client

### Phase 1 Researcher Output (summarized):
- r/Cleveland: "Anyone know a good urgent care that doesn't cost a fortune?" (47 upvotes, 62 comments)
- r/Cleveland: "ER wait times at Fairview are insane right now" (89 upvotes, 134 comments)
- Nextdoor Westlake: Multiple threads about "sick kids and can't leave the house"
- Google PAA: "is urgent care cheaper than ER" — 3,600 monthly searches in Cleveland metro
- Google PAA: "can a doctor come to my house" — 1,900 monthly searches

### Phase 2 & 3 — Presented to User:
```
### Idea 1: ER vs. Urgent Care vs. At-Home Care — The Real Cost Breakdown
**Source:** r/Cleveland (89 upvotes), Google PAA (3,600/mo searches)
**Audience signal:** HIGH — 134 comments on ER wait time thread, 3.6K monthly searches
**Format:** Image+Text
**Content angle:** Educational comparison infographic with real numbers
...
```

---

## Pitfalls

- **Don't skip Phase 1.** Always delegate research first — never guess what the audience cares about.
- **Don't present more than 8 ideas.** Decision fatigue. If researcher found more, rank and show top 8.
- **Don't send unapproved ideas to social_media.** Phase 3 is mandatory gating.
- **If researcher returns thin data:** ask it to dig deeper into a specific subreddit or platform before proceeding.
- **Local specificity matters.** An idea sourced from r/Cleveland with Cleveland-specific details will always outperform a generic "healthcare tips" post. Prefer hyperlocal over generic.
- **Mix formats.** Aim for ~60% image+text, ~40% text-only. Some topics (complex explanations, story-driven content) work better without an image competing for attention.
- **Reddit blocks direct scraping.** `web_extract`, `firecrawl_scrape`, and `firecrawl_agent` all fail on Reddit URLs. The `reddit-scraping` skill (if loaded) can help, but the reliable fallback is `web_search` with `site:reddit.com/r/<subreddit>` — you'll get titles, snippets, and engagement counts from search results. Accept this limitation and work with snippets. Full thread extraction requires manual review or a dedicated Reddit API key.
- **Researcher may not have Supermemory in its toolset.** If the researcher can't write to Supermemory, the output file at `/data/workspace/triage/inbox/` is the primary delivery mechanism. The orchestrator reads it from there.
- **Reddit will block direct extraction.** Firecrawl, web_extract, and headless browsers are frequently blocked by Reddit's anti-scraping. The fallback is `web_search` with domain filters (`site:reddit.com/r/smallbusiness`) and analyzing search snippet titles/descriptions. Search snippets carry enough signal (title, upvote count, subreddit, sentiment from snippet text) to generate good post ideas. If a specific thread looks high-value, note its URL for manual verification — don't let extraction failures block the pipeline.
- **Research will surface its own limitations.** If the researcher reports Firecrawl MCP failures or Reddit blocks, accept partial data — the orchestrator can still synthesize useful ideas from search snippets, local blog posts, survey data, and SEO findings. Don't send the researcher back for a second pass unless the data is genuinely empty.

## References

- `references/voltaic-test-run-worked-example.md` — Live test run output (2026-06-04): what a completed Phase 1 research file looks like, what signals drove the best ideas, what extraction methods failed, and the successful Reddit fallback pattern. Use as quality benchmark for future runs.
- `social-image-post-pipeline` skill — The operational workflow the social_media profile loads to create image posts
- `lead-magnet-discovery-questions` skill — Similar research → synthesis → stakeholder approval pattern (for reference)
- `researcher` profile AGENTS.md — The researcher's capabilities: Reddit scraping, local forum scraping, SEO data via SearXNG/Firecrawl