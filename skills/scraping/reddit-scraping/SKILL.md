---
name: reddit-scraping
description: Scrape top posts and comments from Reddit subreddits using old.reddit.com and browser JS extraction
version: 1.0.0
---

# Reddit Scraping (Browser-Based)

Scrape Reddit without authentication using old.reddit.com and JavaScript DOM
extraction via the browser tool. No cookies, API keys, or auth needed.

## When to Use

- Scraping the top/hot posts from any public subreddit
- Extracting top N comments per post
- Quick research on subreddit activity or sentiment

## Approach

Use **old.reddit.com** — it returns server-rendered HTML with consistent DOM
structure. Extract data via `browser_console` with JS selectors instead of
parsing snapshots.

### Step 1: Extract Top Posts from Listing

Navigate to `https://old.reddit.com/r/SUBREDDIT/`, then run in console:

```js
const posts = [];
const entries = document.querySelectorAll('#siteTable .thing.link:not(.promoted)');
for (let i = 0; i < Math.min(N, entries.length); i++) {
    const el = entries[i];
    const titleEl = el.querySelector('a.title');
    const commentsEl = el.querySelector('a.comments');
    const authorEl = el.querySelector('a.author');
    const scoreEl = el.querySelector('.score.unvoted');
    posts.push({
        rank: i + 1,
        title: titleEl ? titleEl.textContent.trim() : '',
        url: titleEl ? titleEl.href : '',
        permalink: el.getAttribute('data-permalink') || '',
        comments_url: commentsEl ? commentsEl.href : '',
        score: scoreEl ? scoreEl.textContent.trim() : el.getAttribute('data-score') || '',
        author: authorEl ? authorEl.textContent.trim() : ''
    });
}
JSON.stringify(posts, null, 2);
```

Key selectors:
- Posts container: `#siteTable .thing.link:not(.promoted)` — excludes ads/promoted
- Title link: `a.title`
- Comments link: `a.comments`
- Author: `a.author`
- Score: `.score.unvoted` (fallback: `data-score` attribute)

### Step 2: Extract Comments from Each Post

Navigate to each post's `comments_url`, then run:

```js
const comments = [];
const bodies = document.querySelectorAll('.commentarea .entry .usertext-body');
for (let i = 0; i < Math.min(N, bodies.length); i++) {
    const body = bodies[i];
    const thing = body.closest('.entry').closest('.thing.comment');
    const authorEl = thing ? thing.querySelector('a.author') : null;
    const scoreEl = thing ? thing.querySelector('.score.unvoted') : null;
    comments.push({
        rank: i + 1,
        author: authorEl ? authorEl.textContent.trim() : '[deleted]',
        body: body.textContent.trim().substring(0, 500),
        score: scoreEl ? scoreEl.textContent.trim() : (thing ? thing.getAttribute('data-score') || '' : '')
    });
}
JSON.stringify(comments, null, 2);
```

Key selectors:
- Comment body: `.commentarea .entry .usertext-body`
- Walk up to comment wrapper: `.closest('.thing.comment')`
- Author within comment: `a.author`
- Score within comment: `.score.unvoted`

### Step 3: Add Human-Like Delays

Between each navigation, pause with random delays:

```bash
sleep 2.3 && echo "done"
```

Use random values between 2.0-5.0 seconds. Vary the delays — don't use the
same value each time.

## Full Workflow Example (5 posts, 2 comments each)

1. `browser_navigate` to `https://old.reddit.com/r/SUBREDDIT/`
2. `browser_console` → extract top 5 posts (JS from Step 1)
3. For each post:
   a. `terminal: sleep RANDOM` (2-5s random)
   b. `browser_navigate` to `comments_url`
   c. `browser_console` → extract top 2 comments (JS from Step 2)
4. Compile all results into a JSON file via `write_file`

## Reference: Successful Test Run

Scraped r/cleveland on 2026-05-21:
- 5 posts extracted from hot listing (including stickies)
- 2 comments per post extracted successfully
- Delays used: 2.3s, 3.1s, 2.7s, 3.4s
- Results saved to `reddit-cleveland-scrape.json`

## Researcher Profile: Camofox Authenticated Path

When operating under the `researcher` Hermes profile (HERMES_HOME=/data/profiles/researcher),
the AGENTS.md overrides this skill's default approach. The researcher profile mandates
the **Camofox runbook** for any authenticated platform scraping (Reddit, LinkedIn, X).

**BEFORE any Reddit task, check what profile is active.** If the researcher profile
is loaded, switch to the Camofox path — do NOT fall back to old.reddit.com public view
unless Camofox is confirmed unreachable AND a triage error has been filed.

Full details in `references/camofox-authenticated-path.md`. Summary:

1. **Switch model** to DeepSeek Pro for the entire authenticated phase
2. **Check Camofox**: `CAMOFOX_URL` env var, `curl localhost:9377/health`, cookie dir
3. **Locate cookies** at `/data/camofox/cookies/<platform>_<account>.json`
4. **Inject cookies** via `POST /sessions/<USER_ID>/cookies`
5. **Create tab**, navigate, get **accessibility snapshot**, run **schema extraction**
6. **Check for auth gates** (login walls, CAPTCHA, 2FA, paywalls) — halt if detected

If Camofox is unreachable, write a triage error state to
`/data/workspace/triage/inbox/` (see `references/triage-format.md`) and inform
the operator. Do NOT silently fall back to the public scraping path — the
researcher profile considers that a deviation from the deterministic loop.

## Pitfalls

- **Researcher profile override**: When HERMES_HOME points to a profile with an
  AGENTS.md that mandates a specific scraping path (Camofox, model switching),
  that profile's doctrine takes precedence over the general approach in this skill.
  Always check for and follow profile-level instructions first.
- **Camofox unavailability**: If `CAMOFOX_URL` is unset or `localhost:9377` is
  unreachable, authenticated scraping is blocked. File a triage error — do not
  silently bypass to old.reddit.com without the operator's knowledge.
- **Cookie format**: Avoid cookies exported from hotcleaner.com Cookie Editor —
  the vcrv1 binary format is undecodable. Use plain JSON arrays. See
  `references/cookie-formats.md` for details.
- **Score visibility**: Some subreddits hide scores for X hours. Scores may
  show as "•" or be empty. Use the `data-score` attribute as fallback.
- **Stickied posts**: These appear first in the listing. If you want only
  organic posts, filter out `.thing.stickied`.
- **Deleted comments**: Comments with `[deleted]` author still have body text
  if not also removed. Check for both cases.
- **Deep comment trees**: The query selects all top-level + replies mixed.
  If you need only top-level, filter by checking parent depth.
- **Rate limiting**: old.reddit.com is more lenient than new Reddit, but
  keep delays ≥ 2s between requests to avoid throttling.
- **Auth**: The public approach works without login. If you have cookies and need
  to use them, inject them via `browser_console` before navigating:  
  `document.cookie = "session=...; domain=.reddit.com; path=/";`
  For httponly cookies, use the Camofox cookie injection API instead.

- **browser_navigate behavior**: The tool auto-runs a compact snapshot after
  navigation, includes security checks (SSRF blocks, bot detection scan),
  and auto-selects a backend. See `references/browser-navigate-internals.md`
  for the full flow, including session isolation and hybrid routing.
