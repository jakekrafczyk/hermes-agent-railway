---
name: web-design-prototyping
description: Umbrella skill for HTML-based design and prototyping — one-off artifacts, throwaway mockups with variant comparison, and design system replicas from 54 popular web brands.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [design, html, prototype, ux, ui, creative, artifact, deck, motion, mockup, sketch, variants, design-system, branding, templates]
    related_skills: [excalidraw, architecture-diagram, generative-widgets]
    supersedes: [claude-design, sketch, popular-web-designs]
---

# Web Design & Prototyping

Three complementary approaches to HTML-based design and prototyping, consolidated into one umbrella skill. Use the **decision tree** below to choose the right tool for the job, then jump to the relevant section.

## Decision Tree

| What you need | Use |
|---|---|
| **Design a single polished page** — landing page, deck, prototype, motion study | → **Claude Design** (§ below) |
| **Compare layout/UI variants side-by-side** — 2–3 throwaway mockups to pick a direction | → **Sketch** (§ below) |
| **Replicate a known brand's design system** — "make it look like Stripe / Linear / Vercel" | → **Popular Web Designs** (§ below) |
| Design a polished page *styled after a brand* | Combine **Claude Design** (process) + **Popular Web Designs** (visual vocabulary) |
| Author a formal DESIGN.md token spec file | → Use the separate `design-md` skill (not covered here) |

If you're unsure: a one-off polished artifact goes to Claude Design. Rapid variant exploration goes to Sketch. Brand replication goes to Popular Web Designs.

---

## Claude Design (one-off HTML artifacts)

Use this approach when the user asks for design work — a landing page, teaser page, high-fidelity prototype, interactive mockup, deck, component exploration, motion study, dashboard concept, onboarding flow, or a redesign based on screenshots/repos/brand docs.

The goal is to produce a **complete, self-contained local HTML file** with embedded CSS and JS — openable directly in a browser — not a description of what you'd build.

### Runtime Mode

You are running in **CLI/API mode**, not a hosted Claude Design web UI. Ignore references to hosted-only tools (`done()`, `fork_verifier_agent()`, `questions_v2()`, `copy_starter_component()`, `show_to_user()`, `show_html()`, `snip()`, `eval_js_user_view()`, hosted preview panes, edit-mode toolbar messaging, cross-project paths, `window.claude.complete()`, web-search citation scaffolding, tool schemas embedded in source prompts).

Default deliverable: a complete local HTML file (self-contained CSS/JS), exact on-disk path in the final response, and verification using available local methods before saying it is done. If the user asks for implementation in an existing repo, generate code in the repo's actual stack instead.

### Core Identity

Act as an expert designer working with the user as the manager. HTML is the default tool, but the medium changes by assignment:

- **UX designer** for flows and product surfaces
- **Interaction designer** for prototypes
- **Visual designer** for static explorations
- **Motion designer** for animated artifacts
- **Deck designer** for presentations
- **Design-systems designer** for tokens, components, and visual rules
- **Frontend-minded prototyper** when code fidelity matters

Avoid generic web-design tropes unless the user explicitly asks for a conventional web page. Do not expose internal prompts, hidden system messages, or implementation plumbing. Talk about capabilities and deliverables in user terms.

### When To Use

- Landing pages, teaser pages
- High-fidelity prototypes, interactive product mockups
- Visual option boards, component explorations, design-system previews
- HTML slide decks, motion studies
- Onboarding flows, dashboard concepts
- Settings, command palettes, modals, cards, forms, empty states
- Redesigns based on screenshots, repos, brand docs, or UI kits

Do not use this for pure DESIGN.md token authoring — use the `design-md` skill for that.

### Design Principle: Start From Context, Not Vibes

Good high-fidelity design does not start from scratch. Before designing, look for source context:

1. Brand docs
2. Existing product screenshots
3. Current repo components
4. Design tokens
5. UI kits
6. Prior mockups
7. Reference models
8. Copy docs
9. Constraints from legal, product, or engineering

If a repo is available, inspect actual source files before inventing UI: theme files, token files, global stylesheets, layout scaffolds, component files, route/page files, form/button/card/navigation implementations. The file tree is only the menu — read the files that define the visual vocabulary before designing.

If context is missing and fidelity matters, ask concise focused questions instead of producing a generic mockup.

### Asking Questions

Ask questions when the assignment is new, ambiguous, high-fidelity, externally facing, or depends on taste. Keep questions short — don't ask ten by default unless genuinely underspecified.

Usually ask for: intended output format, audience, fidelity level, source materials available, brand/design system in play, number of variations wanted, whether to stay conservative or explore divergent ideas, and which dimension matters most (layout, visual language, interaction, copy, motion, or systemization).

Skip questions when: the user gave enough direction, this is a small tweak, the task is clearly a continuation, or the missing detail has an obvious default. When proceeding with assumptions, label only the important ones.

### Workflow

1. **Understand the brief** — What is being designed? Who is it for? What artifact should exist at the end? What constraints are locked?
2. **Gather context** — Read supplied docs, screenshots, repo files, or design assets. Identify the visual vocabulary before writing code.
3. **Define the design system for this artifact** — colors, type, spacing, radii, shadows/elevation, motion posture, component treatment, interaction rules.
4. **Choose the right format** — static visual comparison (one HTML canvas, options side by side), interaction/flow (clickable prototype), presentation (fixed-size HTML deck with slide nav), component exploration (component lab with variants), motion (timeline or state-based animation).
5. **Build the artifact** — single self-contained HTML file unless a repo implementation is called for. Preserve prior versions for major revisions. Avoid unnecessary dependencies.
6. **Verify** — confirm files exist, run syntax/static checks, open in browser and check console errors if available, inspect primary viewport if screenshot tools are available.
7. **Report briefly** — exact file path, what was created, caveats, next decision/iteration.

### Artifact Format Rules

Default to local files. For standalone artifacts:

- Create a descriptive filename, e.g. `Landing Page.html`, `Command Palette Prototype.html`, `Design System Board.html`
- Embed CSS in `<style>`, embed JS in `<script>`
- Keep the artifact openable directly in a browser
- Avoid remote dependencies unless explicitly useful and stable
- Include responsive behavior unless intentionally fixed-size

For significant revisions: preserve the previous version as `Name.html`, create `Name v2.html`, `Name v3.html`, etc. Or keep one file with in-page toggles for variant exploration.

For repo implementation: follow the repo's actual stack, use existing components and tokens, don't create a standalone artifact if the user asked for production code.

### HTML / CSS / JS Standards

Use modern CSS well:

- CSS variables for tokens
- CSS grid for layout
- Container queries when helpful
- `text-wrap: pretty` where supported
- Real focus and hover states
- `prefers-reduced-motion` handling for non-trivial motion
- Responsive scaling
- Semantic HTML where practical

Avoid: huge monolithic files when a real repo structure is expected, fragile hard-coded viewport assumptions, inaccessible tiny hit targets, decorative JS that fights usability, `scrollIntoView` unless there is no safer option. Mobile hit targets should be at least 44px. For print documents, text should be at least 12pt. For 1920×1080 slide decks, text should generally be 24px or larger.

### React Guidance for Standalone HTML

Use plain HTML/CSS/JS by default. Use React only when: the artifact needs meaningful state, variants/toggles are easier as components, interaction complexity warrants it, or the target implementation is React/Next.js and fidelity matters.

If using React from CDN in standalone HTML: pin exact versions, avoid unpinned `react@18` style URLs, avoid `type="module"` unless necessary, avoid multiple global objects named `styles` (give them specific names, e.g. `commandPaletteStyles`, `deckStyles`), and if splitting Babel scripts, explicitly attach shared components to `window`.

If building inside a real repo, use the repo's package manager and component architecture instead.

### Deck Rules

For slide decks, use a fixed-size canvas and scale it to fit the viewport. Default slide size: 1920×1080, 16:9.

Requirements: keyboard navigation, visible slide count, localStorage persistence for current slide, print-friendly layout when practical, screen labels or stable IDs for important slides, no speaker notes unless explicitly asked. Do not hand-wave a deck as markdown bullets — create a designed artifact if asked for a deck.

Use 1–2 background colors max unless the brand system requires more. Keep slides sparse — solve emptiness with layout, rhythm, scale, or imagery placeholders, not filler text.

### Prototype Rules

For interactive prototypes: make the primary path clickable, include key states (default, hover/focus, loading, empty, error, success where relevant), expose variations with in-page controls when useful, keep controls out of the final composition unless intentionally part of the prototype, persist important state in localStorage when refresh continuity matters. If the prototype models a product flow, design the flow, not just the first screen.

### Variation Rules

When exploring, default to at least three options:

1. **Conservative** — closest to existing patterns / lowest risk
2. **Strong-fit** — best interpretation of the brief
3. **Divergent** — more novel, useful for discovering taste boundaries

Variations can explore: layout, hierarchy, type scale, density, color posture, surface treatment, motion, interaction model, copy structure, component shape. Do not create variations that are merely color swaps unless color is the actual question. When the user picks a direction, consolidate — don't leave the project as a pile of options forever.

### Tweakable Designs in CLI/API Mode

The hosted Claude Design edit-mode toolbar does not exist here. Still preserve the idea: when useful, add in-page controls called `Tweaks`.

A good `Tweaks` panel can control: theme mode, layout variant, density, accent color, type scale, motion on/off, copy variant, component variant. Keep it small and unobtrusive — the design should look final when tweaks are hidden. Persist tweak values with localStorage when helpful.

### Content Discipline

Do not add filler content. Every element must earn its place. Avoid: fake metrics, decorative stats, generic feature grids, unnecessary icons, placeholder testimonials, AI-generated fluff sections, invented content that changes strategy or claims. If additional sections/pages/copy/claims would improve the artifact, ask before adding them. When copy is necessary but not final, mark it as draft or placeholder.

### Anti-Slop Rules

Avoid common AI design sludge: aggressive gradient backgrounds, glassmorphism by default, emoji unless the brand uses them, generic SaaS cards with icons everywhere, left-border accent callout cards, fake dashboards filled with arbitrary numbers, stock-photo hero sections, oversized rounded rectangles as a substitute for hierarchy, rainbow palettes, vague labels like "Insights," "Growth," "Scale," "Optimize" without content, decorative SVG illustrations pretending to be product imagery. Minimal is not automatically good. Dense is not automatically cluttered. Choose intentionally.

### Typography

Use the existing type system if one exists. If not, choose type deliberately:

- **Editorial:** serif or humanist headline with restrained sans body
- **Software/productivity:** precise sans with strong numeric treatment
- **Luxury/minimal:** fewer weights, more spacing discipline
- **Technical:** mono accents only, not mono everywhere
- **Deck:** large, clear, high contrast

Avoid overused defaults when a stronger choice is appropriate. Keep the number of font families and weights low. Use type as hierarchy before adding boxes, icons, or color.

### Color

Use brand/design-system colors first. If no palette exists: define a small system including neutrals, surface, ink, muted text, border, accent, danger/success if needed. Use one primary accent unless the assignment calls for a broader palette. Prefer oklch for harmonious invented palettes when browser support is acceptable. Check contrast for important text and controls. Do not invent lots of colors from scratch.

### Layout and Composition

Design with rhythm: scale, whitespace, density, alignment, repetition, contrast, interruption. Avoid making every section the same card grid. For product UIs, prioritize speed of comprehension over decoration. For marketing surfaces, make one idea land per section. For dashboards, avoid "data slop" — only show data that helps the user decide or act.

### Motion

Use motion as discipline, not theater. Good motion: clarifies state changes, reduces anxiety during loading, shows continuity between surfaces, gives controls tactility, stays subtle. Bad motion: loops without purpose, delays the user, calls attention to itself, hides poor hierarchy. Respect `prefers-reduced-motion` for non-trivial animation.

### Images and Icons

Use real supplied imagery when available. If an asset is missing: use a clean placeholder, use typography/layout/abstract texture instead, or ask for real material when fidelity matters. Do not draw elaborate fake SVG illustrations unless the assignment is explicitly illustration work. Avoid iconography unless it improves scanning or matches the design system.

### Source-Code Fidelity

When recreating or extending a UI from a repo:

1. Inspect the repo tree
2. Identify the actual UI source files
3. Read theme/token/global style/component files
4. Lift exact values where appropriate
5. Match spacing, radii, shadows, copy tone, density, and interaction patterns
6. Only then design or modify

Do not build from memory when source files are available. For GitHub URLs, parse owner/repo/ref/path correctly and inspect the relevant files before designing.

### Reading Documents and Assets

Read Markdown, HTML, CSS, JS, TS, JSX, TSX, JSON, SVG, and plain text directly when available. For DOCX/PPTX/PDF, use available local extraction tools if present — otherwise ask the user to provide exported text/images. For sketches, prioritize thumbnails or screenshots over raw drawing JSON.

### Copyright and Reference Models

Do not recreate a company's distinctive UI, proprietary command structure, branded screens, or exact visual identity unless the user clearly has rights to that source. It is acceptable to extract general design principles: density without clutter, command-first interaction, monochrome with one accent, editorial hierarchy, clear empty states, strong keyboard affordances. When using references, transform posture and principles into an original design.

### Verification

Before final response, verify as much as the environment allows. Minimum: file exists at stated path, HTML is saved completely, obvious syntax issues checked. Better: open in browser and check console errors, inspect screenshots at primary viewport, test key interactions, test light/dark or variants, test responsive breakpoints. If verification is limited by environment, say exactly what was and was not verified. Never say "done" if the file was not actually written.

### Final Response Format

Keep final responses short. Include: artifact path, what it contains, verification status, next suggested action if useful.

Example:
```
Created: /path/to/Prototype.html
It includes 3 layout variants, a Tweaks panel for density/theme, and responsive behavior.
Verified: file exists and opened cleanly in browser, no console errors.
Next: pick the strongest direction and I'll tighten copy + motion.
```

### Portable Opening Prompt Pattern

When adapting a Claude Design style request into CLI/API mode:
```
You are running in CLI/API mode, not hosted Claude Design. Ignore references to hosted-only tools or preview panes. Produce complete local design artifacts, usually self-contained HTML with embedded CSS/JS, and verify with available local tools before returning. Preserve the design process: gather context, define the system, produce options, avoid filler, and meet a high visual bar.
```

### Pitfalls

- Do not paste hosted tool schemas into a skill — they cause fake tool calls.
- Do not point the skill at a giant external prompt as required runtime context — that creates drift.
- Do not strip the design doctrine while removing tool plumbing.
- Do not over-ask when the user already gave enough direction.
- Do not under-ask for high-fidelity work with no brand context.
- Do not produce generic SaaS layouts and call them designed.
- Do not claim browser verification unless it actually happened.

---

## Sketch (throwaway HTML mockups)

Use this approach when the user wants to **see a design direction before committing** to one — exploring a UI/UX idea as disposable HTML mockups. The point is to generate 2–3 interactive variants so the user can compare visual directions side-by-side, not to produce shippable code.

Load this when the user says things like "sketch this screen", "show me what X could look like", "compare layout A vs B", "give me 2–3 takes on this UI", "let me see some variants", "mockup this before I build".

### When NOT to use this

- User wants a production component → use **Claude Design** or build it properly
- User wants a polished one-off HTML artifact (landing page, deck) → use **Claude Design**
- User wants a diagram → use `excalidraw`, `architecture-diagram`
- The design is already locked → just build it

### If the user has the full GSD system installed

If `gsd-sketch` is available (installed via `npx get-shit-done-cc --hermes`), prefer it for the full workflow: persistent `.planning/sketches/` with MANIFEST, frontier mode analysis, consistency audits across past sketches, and integration with the rest of GSD. This section describes the lightweight standalone version — one-off sketching without the state machinery.

### Core method

```
intake  →  variants  →  head-to-head  →  pick winner (or iterate)
```

#### 1. Intake (skip if the user already gave you enough)

Before generating variants, get three things — one question at a time, not all at once:

1. **Feel.** "What should this feel like? Adjectives, emotions, a vibe." — *"calm, editorial, like Linear"* tells you more than *"minimal"*.
2. **References.** "What apps, sites, or products capture the feel you're imagining?" — actual references beat abstract descriptions.
3. **Core action.** "What's the single most important thing a user does on this screen?" — the variants should all serve this well; if they don't, they're just decoration.

Reflect each answer briefly before the next question. If the user already gave you all three upfront, skip straight to variants.

#### 2. Variants (2–3, never 1, rarely 4+)

Produce **2–3 variants** in one go. Each variant is a complete, standalone HTML file. Don't describe variants — build them. The point is comparison.

Each variant should take a **different design stance**, not different pixel values. Three good variant axes:

- **Density:** compact / airy / ultra-dense (pick two contrasting poles)
- **Emphasis:** content-first / action-first / tool-first
- **Aesthetic:** editorial / utilitarian / playful
- **Layout:** single-column / sidebar / split-pane
- **Grounding:** card-based / bare-content / document-style

Pick one axis and pull apart from it. Two variants that differ only in accent color are wasted effort — the user can't distinguish them.

**Variant naming:** describe the stance, not the number.

```
sketches/
├── 001-calm-editorial/
│   ├── index.html
│   └── README.md
├── 001-utilitarian-dense/
│   ├── index.html
│   └── README.md
└── 001-playful-split/
    ├── index.html
    └── README.md
```

#### 3. Make them real HTML

Each variant is a **single self-contained HTML file**:

- Inline `<style>` — no build step, no external CSS
- System fonts or one Google Font via `<link>`
- Tailwind via CDN (`<script src="https://cdn.tailwindcss.com"></script>`) is fine
- Realistic fake content — actual sentences, actual names, not "Lorem ipsum"
- **Interactive**: links clickable, hovers real, at least one state transition (open/close, filter, toggle). A frozen static image is a worse spike than a sloppy animated one.

Open it in a browser. If it looks broken, fix it before showing the user.

**Verify variants visually — use browser tools.** Don't just write HTML and hope it renders; load each variant and look at it:
```
browser_navigate(url="file:///absolute/path/to/sketches/001-calm-editorial/index.html")
browser_vision(question="Does this layout look clean and readable? Any visible bugs (overlapping text, unstyled elements, broken images)?")
```

`browser_vision` returns an AI description of what's actually on the page plus a screenshot path — catches layout bugs that pure source inspection misses (e.g. a font import that silently failed, a flex container that collapsed). Fix and re-navigate until each variant looks right.

**Default CSS reset + system font stack** for fast starts:

```html
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    color: #1a1a1a;
    background: #fafafa;
    line-height: 1.5;
  }
</style>
```

#### 4. Variant README

Each variant's `README.md` answers:

```markdown
## Variant: {stance name}

### Design stance
One sentence on the principle driving this variant.

### Key choices
- Layout: ...
- Typography: ...
- Color: ...
- Interaction: ...

### Trade-offs
- Strong at: ...
- Weak at: ...

### Best for
- The kind of user or use case this variant actually serves
```

#### 5. Head-to-head

After all variants are built, present them as a comparison. Don't just list — **opinionate**:

```markdown
## Three takes on the home screen

| Dimension | Calm editorial | Utilitarian dense | Playful split |
|-----------|----------------|-------------------|---------------|
| Density   | Low            | High              | Medium        |
| Primary action visibility | Low | High | Medium |
| Scan-ability | High | Medium | Low |
| Feel | Calm, trusted | Sharp, tool-like | Inviting, energetic |

**My take:** Utilitarian dense for power users, calm editorial for content-forward audiences. Playful split is weakest — tries to do both and commits to neither.
```

Let the user pick a winner, or combine two into a hybrid, or ask for another round.

### Theming (when the project has a visual identity)

If the user has an existing theme (colors, fonts, tokens), put shared tokens in `sketches/themes/tokens.css` and `@import` them in each variant. Keep tokens minimal:

```css
/* sketches/themes/tokens.css */
:root {
  --color-bg: #fafafa;
  --color-fg: #1a1a1a;
  --color-accent: #0066ff;
  --color-muted: #666;
  --radius: 8px;
  --font-display: "Inter", sans-serif;
  --font-body: -apple-system, BlinkMacSystemFont, sans-serif;
}
```

Don't over-tokenize a throwaway sketch — three colors and one font is usually enough.

### Interactivity bar

A sketch is interactive enough when the user can:

1. **Click a primary action** and something visible happens (state change, modal, toast, navigation feint)
2. **See one meaningful state transition** (filter a list, toggle a mode, open/close a panel)
3. **Hover recognizable affordances** (buttons, rows, tabs)

More than that is over-engineering a throwaway. Less than that is a screenshot.

### Frontier mode (picking what to sketch next)

If sketches already exist and the user says "what should I sketch next?":

- **Consistency gaps** — two winning variants from different sketches made independent choices that haven't been composed together yet
- **Unsketched screens** — referenced but never explored
- **State coverage** — happy path sketched, but not empty / loading / error / 1000-items
- **Responsive gaps** — validated at one viewport; does it hold at mobile / ultrawide?
- **Interaction patterns** — static layouts exist; transitions, drag, scroll behavior don't

Propose 2–4 named candidates. Let the user pick.

### Output

- Create `sketches/` (or `.planning/sketches/` if the user is using GSD conventions) in the repo root
- One subdir per variant: `NNN-stance-name/index.html` + `README.md`
- Tell the user how to open them: `open` on macOS, `xdg-open` on Linux, `start` on Windows
- Keep variants disposable — a sketch that you felt the need to preserve should be promoted into real project code, not curated as an asset

**Typical tool sequence for one variant:**
```
terminal("mkdir -p sketches/001-calm-editorial")
write_file("sketches/001-calm-editorial/index.html", "<!doctype html>...")
write_file("sketches/001-calm-editorial/README.md", "## Variant: Calm editorial\n...")
browser_navigate(url="file://$(pwd)/sketches/001-calm-editorial/index.html")
browser_vision(question="How does this look? Any obvious layout issues?")
```

Repeat for each variant, then present the comparison table.

### Attribution

Adapted from the GSD (Get Shit Done) project's `/gsd-sketch` workflow — MIT © 2025 Lex Christopherson ([gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)). The full GSD system ships persistent sketch state, theme/variant pattern references, and consistency-audit workflows; install with `npx get-shit-done-cc --hermes --global`.

---

## Popular Web Designs (design system replicas)

Use this approach when the user wants to replicate a known brand's visual language. This section catalogs **54 real-world design systems** ready for use when generating HTML/CSS. Each template captures a site's complete visual language: color palette, typography hierarchy, component styles, spacing system, shadows, responsive behavior, and practical agent prompts with exact CSS values.

### Relation to Claude Design

Pair this with the Claude Design workflow when the user wants a thoughtfully-designed page styled after a known brand: Claude Design drives the process, this section supplies the visual vocabulary. For a formal DESIGN.md token spec file rather than a rendered artifact, use the separate `design-md` skill.

### How to Use

1. Pick a design from the catalog below
2. Load it: `skill_view(name="web-design-prototyping")` and navigate to the template entry
3. Use the design tokens and component specs when generating HTML
4. Pair with the `generative-widgets` skill to serve the result via cloudflared tunnel

Each template includes a **Hermes Implementation Notes** block with:
- CDN font substitute and Google Fonts `<link>` tag (ready to paste)
- CSS font-family stacks for primary and monospace
- Reminders to use `write_file` for HTML creation and `browser_vision` for verification

### HTML Generation Pattern

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title</title>
  <!-- Paste the Google Fonts <link> from the template's Hermes notes -->
  <link href="https://fonts.googleapis.com/css2?family=..." rel="stylesheet">
  <style>
    /* Apply the template's color palette as CSS custom properties */
    :root {
      --color-bg: #ffffff;
      --color-text: #171717;
      --color-accent: #533afd;
      /* ... more from template Section 2 */
    }
    /* Apply typography from template Section 3 */
    body {
      font-family: 'Inter', system-ui, sans-serif;
      color: var(--color-text);
      background: var(--color-bg);
    }
    /* Apply component styles from template Section 4 */
    /* Apply layout from template Section 5 */
    /* Apply shadows from template Section 6 */
  </style>
</head>
<body>
  <!-- Build using component specs from the template -->
</body>
</html>
```

Write the file with `write_file`, serve with the `generative-widgets` workflow (cloudflared tunnel), and verify the result with `browser_vision` to confirm visual accuracy.

### Font Substitution Reference

Most sites use proprietary fonts unavailable via CDN. Each template maps to a Google Fonts substitute that preserves the design's character. Common mappings:

| Proprietary Font | CDN Substitute | Character |
|---|---|---|
| Geist / Geist Sans | Geist (on Google Fonts) | Geometric, compressed tracking |
| Geist Mono | Geist Mono (on Google Fonts) | Clean monospace, ligatures |
| sohne-var (Stripe) | Source Sans 3 | Light weight elegance |
| Berkeley Mono | JetBrains Mono | Technical monospace |
| Airbnb Cereal VF | DM Sans | Rounded, friendly geometric |
| Circular (Spotify) | DM Sans | Geometric, warm |
| figmaSans | Inter | Clean humanist |
| Pin Sans (Pinterest) | DM Sans | Friendly, rounded |
| NVIDIA-EMEA | Inter (or Arial system) | Industrial, clean |
| CoinbaseDisplay/Sans | DM Sans | Geometric, trustworthy |
| UberMove | DM Sans | Bold, tight |
| HashiCorp Sans | Inter | Enterprise, neutral |
| waldenburgNormal (Sanity) | Space Grotesk | Geometric, slightly condensed |
| IBM Plex Sans/Mono | IBM Plex Sans/Mono | Available on Google Fonts |
| Rubik (Sentry) | Rubik | Available on Google Fonts |

When a template's CDN font matches the original (Inter, IBM Plex, Rubik, Geist), no substitution loss occurs. When a substitute is used (DM Sans for Circular, Source Sans 3 for sohne-var), follow the template's weight, size, and letter-spacing values closely — those carry more visual identity than the specific font face.

### Design Catalog

#### AI & Machine Learning

| Template | Site | Style |
|---|---|---|
| `claude.md` | Anthropic Claude | Warm terracotta accent, clean editorial layout |
| `cohere.md` | Cohere | Vibrant gradients, data-rich dashboard aesthetic |
| `elevenlabs.md` | ElevenLabs | Dark cinematic UI, audio-waveform aesthetics |
| `minimax.md` | Minimax | Bold dark interface with neon accents |
| `mistral.ai.md` | Mistral AI | French-engineered minimalism, purple-toned |
| `ollama.md` | Ollama | Terminal-first, monochrome simplicity |
| `opencode.ai.md` | OpenCode AI | Developer-centric dark theme, full monospace |
| `replicate.md` | Replicate | Clean white canvas, code-forward |
| `runwayml.md` | RunwayML | Cinematic dark UI, media-rich layout |
| `together.ai.md` | Together AI | Technical, blueprint-style design |
| `voltagent.md` | VoltAgent | Void-black canvas, emerald accent, terminal-native |
| `x.ai.md` | xAI | Stark monochrome, futuristic minimalism, full monospace |

#### Developer Tools & Platforms

| Template | Site | Style |
|---|---|---|
| `cursor.md` | Cursor | Sleek dark interface, gradient accents |
| `expo.md` | Expo | Dark theme, tight letter-spacing, code-centric |
| `linear.app.md` | Linear | Ultra-minimal dark-mode, precise, purple accent |
| `lovable.md` | Lovable | Playful gradients, friendly dev aesthetic |
| `mintlify.md` | Mintlify | Clean, green-accented, reading-optimized |
| `posthog.md` | PostHog | Playful branding, developer-friendly dark UI |
| `raycast.md` | Raycast | Sleek dark chrome, vibrant gradient accents |
| `resend.md` | Resend | Minimal dark theme, monospace accents |
| `sentry.md` | Sentry | Dark dashboard, data-dense, pink-purple accent |
| `supabase.md` | Supabase | Dark emerald theme, code-first developer tool |
| `superhuman.md` | Superhuman | Premium dark UI, keyboard-first, purple glow |
| `vercel.md` | Vercel | Black and white precision, Geist font system |
| `warp.md` | Warp | Dark IDE-like interface, block-based command UI |
| `zapier.md` | Zapier | Warm orange, friendly illustration-driven |

#### Infrastructure & Cloud

| Template | Site | Style |
|---|---|---|
| `clickhouse.md` | ClickHouse | Yellow-accented, technical documentation style |
| `composio.md` | Composio | Modern dark with colorful integration icons |
| `hashicorp.md` | HashiCorp | Enterprise-clean, black and white |
| `mongodb.md` | MongoDB | Green leaf branding, developer documentation focus |
| `sanity.md` | Sanity | Red accent, content-first editorial layout |
| `stripe.md` | Stripe | Signature purple gradients, weight-300 elegance |

#### Design & Productivity

| Template | Site | Style |
|---|---|---|
| `airtable.md` | Airtable | Colorful, friendly, structured data aesthetic |
| `cal.md` | Cal.com | Clean neutral UI, developer-oriented simplicity |
| `clay.md` | Clay | Organic shapes, soft gradients, art-directed layout |
| `figma.md` | Figma | Vibrant multi-color, playful yet professional |
| `framer.md` | Framer | Bold black and blue, motion-first, design-forward |
| `intercom.md` | Intercom | Friendly blue palette, conversational UI patterns |
| `miro.md` | Miro | Bright yellow accent, infinite canvas aesthetic |
| `notion.md` | Notion | Warm minimalism, serif headings, soft surfaces |
| `pinterest.md` | Pinterest | Red accent, masonry grid, image-first layout |
| `webflow.md` | Webflow | Blue-accented, polished marketing site aesthetic |

#### Fintech & Crypto

| Template | Site | Style |
|---|---|---|
| `coinbase.md` | Coinbase | Clean blue identity, trust-focused, institutional feel |
| `kraken.md` | Kraken | Purple-accented dark UI, data-dense dashboards |
| `revolut.md` | Revolut | Sleek dark interface, gradient cards, fintech precision |
| `wise.md` | Wise | Bright green accent, friendly and clear |

#### Enterprise & Consumer

| Template | Site | Style |
|---|---|---|
| `airbnb.md` | Airbnb | Warm coral accent, photography-driven, rounded UI |
| `apple.md` | Apple | Premium white space, SF Pro, cinematic imagery |
| `bmw.md` | BMW | Dark premium surfaces, precise engineering aesthetic |
| `ibm.md` | IBM | Carbon design system, structured blue palette |
| `nvidia.md` | NVIDIA | Green-black energy, technical power aesthetic |
| `spacex.md` | SpaceX | Stark black and white, full-bleed imagery, futuristic |
| `spotify.md` | Spotify | Vibrant green on dark, bold type, album-art-driven |
| `uber.md` | Uber | Bold black and white, tight type, urban energy |

### Choosing a Design

Match the design to the content:

- **Developer tools / dashboards:** Linear, Vercel, Supabase, Raycast, Sentry
- **Documentation / content sites:** Mintlify, Notion, Sanity, MongoDB
- **Marketing / landing pages:** Stripe, Framer, Apple, SpaceX
- **Dark mode UIs:** Linear, Cursor, ElevenLabs, Warp, Superhuman
- **Light / clean UIs:** Vercel, Stripe, Notion, Cal.com, Replicate
- **Playful / friendly:** PostHog, Figma, Lovable, Zapier, Miro
- **Premium / luxury:** Apple, BMW, Stripe, Superhuman, Revolut
- **Data-dense / dashboards:** Sentry, Kraken, Cohere, ClickHouse
- **Monospace / terminal aesthetic:** Ollama, OpenCode, x.ai, VoltAgent
