---
name: social-image-post-pipeline
description: Step-by-step operational workflow for the social_media profile to create image-based social media posts — AI-generated or real photo + educational text, using Ideogram 3.0 for text-in-image generation. Produces finished post packages (image + caption + hashtags) for human review.
triggers:
  - task_type: post_generation with image media
  - User asks social_media to "create an image post"
  - User asks social_media to "generate a social graphic"
  - User provides a photo and asks social_media to "turn this into a post"
  - Any task where the social_media profile needs to produce an image-based post
---

# Social Image Post Pipeline

Operational workflow for creating image-based social media posts. Load this skill whenever the social_media profile receives a task to create an image or graphic post.

## Pipeline Overview

```
SOURCE PHOTO (real or AI) → GENERATE (if AI) → PACKAGE → HUMAN REVIEW
```

Two modes:
- **Mode A — Real photo provided:** Skip generation, go straight to packaging with the provided photo
- **Mode B — AI-generated:** Use `image_generate` with Ideogram 3.0 to create an image with educational text burned in

## Before Starting

1. Read `/data/workspace/active_client.yaml` → extract `active_client` value
2. Read `references/copywriting-rules.md` — all caption copy must follow these rules
3. Read `references/designer-quality-prompting-guide.md` — the two-stage pipeline, design principles, and prompt templates
4. If Voltaic Marketing (agency's own brand): read `references/voltaic-brand-guide.md` for exact colors, fonts, and design system
5. If a client: check for a client-specific brand guide in this skill's `references/` directory. If none exists, extract brand colors from the client's website CSS before generating any graphics. Never guess brand colors.

## Mode A — Real Photo Provided

When a photo file path or URL is in the task brief:

1. **Verify the photo exists** — stat the file or curl-head the URL
2. **Skip generation entirely** — do NOT call `image_generate`
3. **Proceed directly to Package Output** (Step 3 below)
4. Use the provided photo URL as the `media` field

## Mode B — AI-Generated Image (Ideogram 3.0)

When no real photo is provided, generate one with educational text burned into the image. Ideogram 3.0 is the chosen model because it has 98% text-in-image accuracy — best-in-class for images that contain readable text.

### Step 1 — Build the Prompt

Combine two components in ONE prompt: (a) visual scene description using the photorealism framework, (b) the educational text to display.

**Prompt template:**

```
[Visual scene: subject, environment, lighting, camera, imperfections]
Text on image: "[HEADLINE]" in bold at top. Below it: "[BODY TEXT in 1-2 sentences]"
Style: clean modern infographic with subtle [brand color] accents, white background sections for text readability
```

**Photorealism framework (for the visual part):**
- Camera: "Sony A7IV, 35mm f/2.0, ISO 100, shallow depth of field"
- Lighting: "Soft window light from left, natural shadows, golden hour warmth"
- Imperfections: "Fine film grain, natural skin texture, slight chromatic aberration"
- Style: "Candid, unposed, authentic moment" — never "8K photorealistic cinematic"

**Text guidance for Ideogram:**
- Keep headline under 8 words
- Body text under 25 words
- Use pipe `|` for line breaks in multi-line text
- Specify text placement clearly ("top third", "bottom section", "overlay on right side")
- Include a small logo placement instruction if brand logo is needed

**Example prompt:**
```
A nurse practitioner's hands holding a tablet showing a health dashboard, sitting at a wooden kitchen table in a bright Cleveland colonial home, morning light through bay windows, Sony A7IV 35mm f/1.8, shallow depth of field, candid natural moment, slight film grain

Text on image: "Skip the ER Wait" in bold white text at top. Below it: "Same-day urgent care at home for $150. Serving Cleveland's west side." in smaller text. Small MobileMD logo in bottom right corner.

Style: clean medical infographic aesthetic, navy blue accent, white semi-transparent text background for readability
```

### Step 2 — Generate the Image (Two-Stage Pipeline)

**Stage 1: Ideogram 3.0 base graphic** — best text rendering, produces the core layout with headline + card labels.

Call `image_generate` with:
- `prompt`: the combined prompt from Step 1
- `aspect_ratio`: `"square"` (1:1 for feed) or `"portrait"` (9:16 for Stories; use `portrait_4_3` via curl for 4:5 Facebook format)

If `image_generate` fails with credential errors, use the direct FAL curl workaround (`references/fal-curl-workaround.md`).

**Stage 2: FLUX.1 [dev] Image-to-Image refinement** — sharpens edges, unifies shadows, harmonizes spacing, makes the graphic look "designed" not "generated."

Via curl (FAL direct):
```bash
curl -X POST "https://queue.fal.run/fal-ai/flux/dev/image-to-image" \
  -H "Authorization: Key $FAL_KEY" \
  -d '{"image_url":"<stage1_url>","prompt":"Same exact layout and design. <refinement keywords>. No artifacts.","strength":0.2,"num_inference_steps":28}'
```

**Strength 0.15–0.25 for cleanup.** Higher values risk layout changes. See `references/designer-quality-prompting-guide.md` for full refinement patterns.

**Stage 3: Logo composite** — overlay the real client logo icon at 70% opacity, bottom-right corner, using Pillow. Never rely on Ideogram/Flux to hallucinate a logo (it will get the name wrong). See `references/fal-curl-workaround.md` for the Pillow composite script.

The final image is the Stage 3 output — refined + real logo.

If the image has visual AI tells (inconsistent card sizes, uneven shadows, garbled body text), re-run Stage 2 at slightly higher strength, or re-prompt Stage 1 with stricter symmetry language ("identical," "same dimensions," "uniform").

### Step 3 — Package Output

Write the completed post to `/data/workspace/triage/inbox/task_<uuid>_image_post.md`:

```yaml
---
output_type: generated_post
status: awaiting_review
profile: social_media
assignee_domain: social
client: <active_client>
post_type: image
created_at: '<ISO 8601>'
platform: facebook  # or instagram, linkedin, etc.
---

## Platform
Facebook Feed (also suitable for Instagram)

## Image
<generated image URL or provided photo URL>

## Caption
[Hook — first line visible before "see more"]
[Body — 2-4 lines of educational or engaging content]
[CTA — clear next step]

## Hashtags
#Hashtag1 #Hashtag2 #Hashtag3

## Alt Text
[Accessible description of the image for screen readers]

## Rationale
- Why this visual approach was chosen
- How it aligns with brand voice
- Why the text content was selected
- Photorealism measures applied (if AI-generated)
```

Wait for human review. Do NOT auto-post.

## Caption Writing Guidelines

Captions follow the Copywriting Rules at `references/copywriting-rules.md`. Core principles:

**Anti-Marketese:** Zero promotional language. No "hottest," "world-class," "revolutionary," or em dashes. Facts and numbers carry claims, not adjectives.

**Scannability:** Half word count of conventional writing. One idea per line. Inverted pyramid: hook = conclusion first, then evidence, then CTA.

**Four Readers, One Caption:**
- **Skimmer** reads headline only — headline must deliver the full promise alone
- **Data Hunter** scans for numbers/proof — stats close to claims, visually bold
- **Selective Reader** reads headlines + subheads — subheads bridge claim to delivery
- **Detail Reader** reads everything — logic must hold up, no gaps

**Caption Template (with dual closings):**
```
[Hook: 1-2 lines, direct, conversational, no artificial contrast.]
[Blank line]
[Supporting point — mix of sentence lengths]
[Blank line]
[Data point: bolded, visually distinct]
[Blank line]

--- CTA CLOSING (generate this AND the non-CTA version) ---
[One line. Natural invitation. Use a contraction.]
[Blank line]
[Hashtags: 3-5 max]

--- NON-CTA CLOSING ---
[One line. Conversational wrap. No link, no ask. Leaves the insight.]
[Blank line]
[Hashtags: 3-5 max]
```

Always generate both closings. Let the human choose which to post. See `references/copywriting-rules.md` for the full CTA vs non-CTA rules.

**Specific rules:**
- Hook: Start with a fact or stat, not a question or cliché
- Body: 3-4 sentences max. Cut, then cut again
- CTA: One line. No "click here" filler. State the action.
- Hashtags: 3-5 max. Branded + local + topical
- Em dashes: FORBIDDEN. Use commas, colons, or new sentences.

## Quality Checks Before Writing Output

- [ ] **Design style preset** selected (not Auto, not Realistic)
- [ ] **Magic Prompt** OFF
- [ ] All text in **quotation marks** with exact casing specified
- [ ] Text placed **early** in prompt (first third)
- [ ] **≤6 words per text string** — body copy lives in the caption, not the image
- [ ] **Background** explicitly described (solid dark charcoal = #1A1A1A vibe)
- [ ] **Color palette** limited to 3-4 named colors
- [ ] **Composition** described concretely ("three cards side by side," "centered headline," "generous margins")
- [ ] **Negative prompt field** populated: `drop shadows, gradients, bevels, UI elements, bubbles, labels, badges, 3D effects, watermarks`
- [ ] **Affirmative descriptions only** — never "no shadows," use "flat design, clean edges"
- [ ] **No CTAs or action language in the image** — purely educational
- [ ] **No random UI elements** — no badges, no labels, no diagnostic bubbles
- [ ] **Logo** — do NOT mention a logo in the Ideogram/FLUX prompt. The official logo file is composited after generation via Pillow. See Logo Footer script below. ✅ DONE after generation, not before.
- [ ] If AI-generated: prompt included camera metadata + natural lighting + imperfections (for photos; skip for vector graphics)
- [ ] Text is readable and correctly spelled (check each word)
- [ ] Brand colors match brand guide (#1A1A1A, #C4881A, #F0EDE8)
- [ ] Caption hook is compelling before "see more" cutoff
- [ ] Both CTA and non-CTA closings generated
- [ ] Hashtags include at least one local/geographic tag
- [ ] Alt text is descriptive and complete

## Common Failures & Fixes

| Failure | Fix |
|---------|-----|
| Ideogram misspells a word | Regenerate with simpler text or hyphenate the word |
| Image looks too "AI" | Add more imperfections to prompt: "film grain, slight blur, JPEG compression artifacts, desaturated colors" |
| Text unreadable against background | Add "white semi-transparent text background" to prompt |
| Hands look wrong | Avoid hands in composition — describe "hands resting on table, partially out of frame" |
| Too much text, Ideogram truncates | Shorten to headline only (under 8 words), put body text in the Facebook caption instead |
| **Multi-sentence body text garbled in cards/boxes** | **Known Ideogram 3.0 limitation.** Small body text inside cards/boxes (e.g., "Are the right people finding you?") frequently renders as garbled nonsense. Fix: use single-word labels only on the image (TRAFFIC, CONVERSION, FOLLOW-UP). Put all descriptive sentences in the Facebook caption where they belong. Tested v1-v3: short labels pass consistently; multi-word subtext fails ~80% of generations. |
| Brand colors wrong (e.g., navy instead of charcoal) | Check `references/voltaic-brand-guide.md` (or client equivalent). Never guess brand colors. Always extract from the client's actual website before generating graphics. |
| `image_generate` returns "No credentials found" after adding FAL_KEY | Session env loads at startup. Key added mid-session won't take effect until restart. **Workaround:** call FAL API directly via `curl` — POST to `https://queue.fal.run/fal-ai/ideogram/v3` with `Authorization: Key $FAL_KEY` header. Poll status URL for completion, download result. See `references/fal-curl-workaround.md`. |
| **Pillow-composited logo/footer invisible in WebUI** | **Common browser caching issue.** Three causes: (1) Browser caches old image with same filename — always increment version (v5→v6). (2) Subtle alpha blending (70% opacity) lost in JPEG compression — use 85%+ opacity and thick dividers (3px). (3) Vision AI correctly reads the new file even when the browser shows the cached version. **Fix:** Use new filenames each iteration and verify with pixel sampling (`amber_count > 100` check). |
| **AI hallucinates a fake logo** | Never mention a logo in the generation prompt. Always use `scripts/add-logo-footer.py` after generation. |
| **Corner-only logo looks pasted-on, not integrated** | A standalone logo in the bottom-right corner without surrounding design context reads as an afterthought. **Fix: use a footer bar.** Thin amber divider line spanning 70% width (same amber as the existing dot connectors) → centered horizontal logo lockup (icon + wordmark) beneath it. Apply via Pillow compositing after generation — do NOT attempt to generate the logo in the prompt. |

## Logo Footer Compositing (Post-Generation)

After generating the graphic via Ideogram → FLUX refine, add the official logo using this Pillow compositing script. **Never include a logo in the generation prompt.**

```python
from PIL import Image, ImageDraw

def add_logo_footer(img_path, logo_path, output_path):
    img = Image.open(img_path).convert('RGBA')
    w, h = img.size
    footer_h = int(h * 0.10)
    footer = Image.new('RGBA', (w, footer_h), (26, 26, 26, 255))
    # Amber divider — same amber as dot connectors (#C4881A)
    amber = (196, 136, 26, 255)
    for x in range(int(w * 0.15), int(w * 0.85)):
        for dy in range(3):
            footer.putpixel((x, dy), amber)
    # Scale logo to 55% of footer height, 85% opacity
    logo = Image.open(logo_path).convert('RGBA')
    logo_h = int(footer_h * 0.55)
    ratio = logo_h / logo.height
    logo_w = int(logo.width * ratio)
    logo_small = logo.resize((logo_w, logo_h), Image.LANCZOS)
    r, g, b, a = logo_small.split()
    a = a.point(lambda p: int(p * 0.85))
    logo_small = Image.merge('RGBA', (r, g, b, a))
    lx = (w - logo_w) // 2
    ly = 3 + (footer_h - 3 - logo_h) // 2
    footer.paste(logo_small, (lx, ly), logo_small)
    img.paste(footer, (0, h - footer_h), footer)
    img.convert('RGB').save(output_path, quality=95)
```

For aspect ratio variations, apply the same footer after cropping/resizing.

## References

- `references/copywriting-rules.md` — Full copy rules: anti-marketese, Not-X-But-Y ban, simple language, varied rhythm, contractions, dual CTA/non-CTA closings, four-reader framework
- `references/designer-quality-prompting-guide.md` — Two-stage pipeline (Ideogram → Flux refinement), 12 design principles mapped to prompts, Z-pattern/F-pattern layout, typography rules, 60-30-10 color, prompt templates, pre-gen checklist
- `references/voltaic-brand-guide.md` — Voltaic-specific: color palette, typography, design system, logo assets, image design rules
- `references/fal-curl-workaround.md` — Direct FAL API curl patterns for Ideogram, FLUX refinement, and inpainting. Use when `image_generate` fails with credential errors mid-session
- `references/voltaic-logo-horizontal.png` — Full Voltaic brand lockup (text + icon)
- `references/voltaic-logo-icon.png` — Logo icon only (for subtle corner watermark)
- `scripts/add-logo-footer.py` — Standalone Pillow script: adds branded footer (amber divider + centered logo) to generated graphics. Usage: `python3 add-logo-footer.py <input> <logo> <output>`
- `social-visual-content` skill — Full photorealism framework, anti-AI-detection techniques, common AI tells, video pipeline
- `composio-integration` skill — Facebook/Instagram posting via Composio MCP (for manual posting after review)