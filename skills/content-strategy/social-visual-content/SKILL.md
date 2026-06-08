---
name: social-visual-content
description: AI-assisted social media photo/video content creation pipeline — photorealism frameworks, anti-AI-detection techniques, tool selection, post-processing, and QA checklist. For agencies creating visual content for audiences skeptical of AI-generated marketing.
triggers:
  - User asks about creating AI photos/videos for social media
  - User mentions "non-AI-looking" or "authentic" AI content
  - User needs to compare AI image/video generation tools for marketing
  - User asks about AI video editing from raw footage
  - User mentions Midjourney, DALL-E, Runway, OpusClip, or similar tools for social content
  - "How do we make AI content that doesn't look like AI?"
  - Photo/video social media pipeline design
  - Hermes video_gen toolset or video_generate tool
  - Automating social content creation end-to-end in Hermes
---

# AI-Assisted Social Media Visual Content

Framework for creating photo and video content with AI tools that passes as authentic, professional photography/videography — not AI-generated marketing slop. Designed for audiences (especially Midwest/local markets) that actively distrust AI content.

## The Core Principle: AI Enhances, Doesn't Originate

> **The 80/20 Rule:** At least 80% of visual content should be real footage/photos. AI is used to enhance (backgrounds, B-roll, graphics, supplementary scenes) rather than replace. Never use AI to generate fake people, fake staff, or fake facility images.

## Design Principles (User Preferences)

- **Full Hermes automation.** Pipeline should run end-to-end in Hermes — no human-operated desktop tools in the critical path. Human reviews final output and manually posts; everything upstream is automated.
- **Simplest possible stack.** Before adding a tool, verify it's actually needed. Prefer Hermes-native tools (image_generate, video_generate, Composio MCP) over external services.
- **Two distinct pipelines.** Image posts (photo + educational text overlay) and video posts (raw footage → social clips) are separate workflows with different tool chains.
- **Final output = post package.** Hermes produces the finished media file + caption text + hashtags. Human reviews, then posts manually via Composio or directly.

**Trust hierarchy** (what audiences accept → reject):
1. Real photos of real people in real places → **Most trusted**
2. AI-enhanced real photos (background replacement, color grading) → **Trusted if undetectable**
3. AI-generated B-roll / abstract imagery / establishing shots → **Acceptable**
4. AI-generated educational diagrams / infographics → **Acceptable ("obviously AI" is fine here)**
5. AI-generated photos of fake people → **Rejected (trust-destroying)**
6. AI-generated fake patient testimonials / fake facilities → **Brand-destroying**

---

## 1. Photorealism Framework — The 5-Point System

For generating images that don't trigger "this is AI" alarms:

### Point 1: Camera & Lens Metadata in Prompts
```
❌ "photorealistic, high quality, 8K"
✅ "Shot on Sony A7IV, 50mm f/1.8, ISO 100, shallow depth of field"
```
Include: camera model, focal length, aperture, ISO, depth of field.

### Point 2: Natural Lighting Specificity
```
❌ "cinematic lighting"
✅ "Soft window light from the left, golden hour sunlight with subtle rim light, natural shadows"
```
Describe: direction, quality (hard/soft), color temperature, time of day.

### Point 3: Deliberate Imperfections
```
✅ "Fine film grain, natural skin texture, slight chromatic aberration, minor lens flare"
✅ "Candid, not posed, slight motion blur on hand"
```
AI images are too clean — imperfections signal authenticity.

### Point 4: Photographer-Style Prompt Structure
Template: `[Subject] + [Environment] + [Lighting] + [Camera/Settings] + [Mood/Imperfections]`

Example: *"A nurse practitioner smiling naturally while examining a patient in a bright living room, soft afternoon light through bay windows, 35mm f/2.0, candid capture, slight grain, natural skin texture"*

### Point 5: Reduce Over-Stylization
- **Midjourney:** `--style raw` or `--stylize 50-100` (lower = more natural)
- **Flux/Stable Diffusion:** Lower guidance scale (4-6 instead of 7-10)
- Avoid default "beauty mode" processing

---

## 2. Post-Processing Pipeline (De-AI-Fication)

### Minimum Bar (Every AI Image)
1. Add subtle film grain overlay (1-3% opacity)
2. Desaturate 5-10% — AI tends to oversaturate
3. Add slight vignette (natural lens characteristic)
4. Compress and re-save at 85-90% JPEG quality (destroys generation artifacts)
5. Crop slightly — non-standard crops feel more authentic
6. Add real EXIF data (camera, lens, date, GPS) using exiftool

### Advanced (Adobe Workflow)
1. Import into Lightroom/Photoshop
2. Apply subtle color grading (warm shadows, slightly cool highlights)
3. Add localized texture (grain brush on skin areas)
4. Lens correction profile distortion
5. Save through multiple compression cycles

### Hybrid Approach (Most Undetectable)
Generate scene elements with AI → composite with real photos of actual staff/patients (consented) → final edit in Photoshop/Lightroom. Nearly impossible to detect as AI.

---

## 3. Common AI Tells & Fixes

| Tell | Why It Looks Fake | Fix |
|------|-------------------|-----|
| Too-perfect skin | No pores, texture, blemishes | Add texture/grain; use `--style raw` |
| Unnatural hands | Wrong finger count, impossible poses | Hide hands in composition or inpaint |
| Lighting inconsistencies | Multiple shadow directions | Be specific about single light source |
| Over-saturated colors | "HDR" look, neon skin tones | Desaturate 5-15% in post |
| Symmetrical faces | AI defaults to overly symmetrical | Prompt "asymmetrical natural face, character" |
| Stiff poses | "Mannequin-like" | Prompt "candid, mid-action, natural posture" |
| Generic backgrounds | Too-perfect bokeh | Describe specific local details |
| AI watermarks/logos | Some generators add marks | Crop or clone out |
| Metadata inconsistency | Missing/inconsistent EXIF | Add real camera EXIF data |

---

## 4. Tool Selection Quick-Reference

### Logo Placement — CRITICAL RULE

**Never ask any AI model to generate a logo.** Models hallucinate approximations. Always composite the official logo file via Pillow after generation. See `social-image-post-pipeline` skill for the reusable `scripts/add-logo-footer.py` script.

### Image Generation (Hermes-Native)
| Priority | Tool | Photorealism | API | Cost | Best For |
|----------|------|-------------|-----|------|----------|
| 1st | FAL Flux 2 Pro via `image_generate` | ★★★★½ | ✅ Hermes built-in | $0.03/MP | API-driven generation, speed, Hermes-native |
| 2nd | FAL GPT Image 2 via `image_generate` | ★★★★☆ | ✅ Hermes built-in | $0.04–0.06/img | Best prompt adherence, text rendering |
| 3rd | xAI Grok Imagine via `image_generate` | ★★★★☆ | ✅ Hermes built-in (xAI OAuth) | Subscription quota | Quick social content, integrated with xAI stack |
| 4th | FAL Ideogram 3.0 via `image_generate` | ★★★★☆ | ✅ Hermes built-in | $0.03–0.09/img | Best text-in-image accuracy (98%) for self-contained graphics |
| 5th | Midjourney V7 | ★★★★★ | ❌ No direct API (Discord-based) | $10–60/mo | Hero/campaign images when maximum quality needed |

> **Hermes `image_generate` uses FAL.ai with 11 models.** FAL and xAI are both built-in backends. xAI requires SuperGrok or X Premium+ subscription with OAuth — one token covers chat, image, video, TTS, transcription, and X search.

### Video Generation (Hermes-Native)
| Priority | Tool | Quality | Cost | Best For |
|----------|------|---------|------|----------|
| 1st | xAI Grok Imagine via `video_generate` | ★★★★☆ | Subscription quota | Text-to-video, image-to-video, integrated with xAI |
| 2nd | FAL Veo 3.1 via `video_generate` | ★★★★★ | Per-use | Cinematic quality, best-in-class prompt accuracy |
| 3rd | FAL Pixverse v6 via `video_generate` | ★★★★☆ | Per-use | Quick social effects, budget-friendly |
| 4th | FAL Kling O3 via `video_generate` | ★★★★½ | Per-use | Photorealistic motion, complex human scenes |

> **`video_gen` toolset is DISABLED by default.** Must be enabled via `hermes tools` → 🎬 Video Generation → press space. The tool is `video_generate` with two modalities: text-to-video (prompt only) and image-to-video (prompt + image_url). Backends are plugin-based — xAI Grok Imagine and FAL.ai (Veo 3.1, Pixverse v6, Kling O3) ship as bundled plugins.

### Video Editing from Raw Footage (Automated)

| Priority | Tool | Monthly | API? | Best For |
|----------|------|---------|------|----------|
| 1st | **OpusClip API** | $19 (Pro, 15 hrs/mo API limit) | ✅ Full REST | Fully automated: submit video URL → auto-clips, captions, reframe, filler removal → webhook on completion |
| 2nd | Bannerbear via Composio | Free tier → $19/mo | ✅ Composio MCP | Template-based image/video rendering with text overlay (NOT AI generation) |

> **CapCut has NO public editing API** (only in-editor plugins and AI feature endpoints). Cannot be automated server-side. OpusClip is the only viable API for fully automated raw footage → social clips.

### Image Text Overlay (Automated)

| Priority | Tool | Monthly | API? | Best For |
|----------|------|---------|------|----------|
| 1st | **FAL Ideogram 3.0 via `image_generate`** | $0.03–0.09/img | ✅ Hermes built-in | Text burned directly into AI image (98% accuracy) — single-step generation, no separate overlay tool needed |
| 2nd | Bannerbear via Composio MCP | Free (50 imgs/mo) → $19 | ✅ Composio MCP | Template-based branded image rendering from JSON data (for complex multi-element layouts or when brand templates already exist) |

> **Ideogram-first approach:** Ideogram 3.0's 98% text-in-image accuracy means educational text can be generated directly in the image in a single `image_generate` call. This eliminates the need for a separate text overlay tool for most educational posts. Bannerbear remains available as an upgrade path when complex branded layouts (multi-font, precise logo placement, data-driven templates) are needed.
> 
> **Ideogram workflow:** Combine visual scene description + educational text in one prompt → `image_generate` with `fal-ai/ideogram/v3` → single output image with readable text and photorealism. See `social-image-post-pipeline` skill for the full operational workflow.

---

## 5. Automated Pipeline Architecture (Hermes-Native)

Two distinct, fully-automated pipelines. Human reviews final output and manually posts — everything upstream runs in Hermes.

### Pipeline A — Image Post (Two-Stage: Ideogram → Flux Refinement)

```text
HERMES (social_media profile)
│
├── STEP 0: Load skill references
│   ├── references/copywriting-rules.md (captions)
│   ├── references/designer-quality-prompting-guide.md (design principles + prompt templates)
│   └── references/voltaic-brand-guide.md or client equivalent (colors, fonts, logo)
│
├── STEP 1: Ideogram 3.0 base graphic
│   image_generate (fal-ai/ideogram/v3) → text + layout
│   Design preset, Magic Prompt OFF, ≤6 words per text string
│   Affirmative descriptions only, negative prompt for shadows/gradients
│   Z-pattern layout: headline top third, cards middle, brand mark bottom-right
│   60-30-10 color rule, 3 colors max
│
├── STEP 2: FLUX.1 [dev] Image-to-Image refinement
│   Strength 0.15–0.25 — sharpens edges, unifies shadows, cleans spacing
│   "Same exact layout and design. <refinement>. No artifacts."
│   Makes the difference between "AI-generated" and "designer-made"
│
├── STEP 3: Real logo composite (Pillow)
│   Overlay client logo icon at 70% opacity, bottom-right corner
│   Never rely on AI to hallucinate a logo — it will get the name wrong
│
├── STEP 4: Package output
│   └── Write task file → inbox with:
│       • Image URL (refined + logo)
│       • CTA caption AND non-CTA caption (both)
│       • Hashtags, alt text, rationale, quality audit
│       → Human reviews, posts manually via Composio
```

> **Full operational workflow:** Load `social-image-post-pipeline` skill for step-by-step instructions, prompt templates, quality checklist, and failure remediation.

### Pipeline B — Video Post (Raw Footage → Social Clips)

```
HERMES (social_media profile)
│
├── STEP 1: Submit to OpusClip API
│   POST https://api.opus.pro/api/clip-projects
│   -H "Authorization: Bearer $OPUSCLIP_API_KEY"
│   -d '{
│     "videoUrl": "<google_drive_or_s3_url>",
│     "curationPref": {
│       "model": "ClipBasic",
│       "clipDurations": [[15, 60]],
│       "genre": "Educational"
│     },
│     "renderPref": {
│       "layoutAspectRatio": "portrait",
│       "quickstartConfig": { "enableRemoveFillerWords": true }
│     },
│     "brandTemplateId": "mobilemd_brand",
│     "conclusionActions": [{
│       "type": "WEBHOOK",
│       "url": "<hermes_endpoint>",
│       "notifyFailure": true
│     }]
│   }'
│   → Response: { projectId: "proj_abc123" } → store, poll for completion
│
├── STEP 2: Receive Clips (webhook or poll)
│   Webhook payload:
│   { clips: [{ id, url, duration, title, hook }, ...] }
│   → Download clips to workspace: curl -o clip_001.mp4 <url>
│
│   Fallback (no webhook): cron polls GET /api/clip-projects/{id}
│   every 30 seconds until status: "completed"
│
├── STEP 3: Package Output
│   └── For each clip, write task file → inbox:
│       output_type: generated_post
│       Media: /data/workspace/output/clip_001.mp4
│       Caption: social_media writes engaging hook + body
│       Hashtags: platform-appropriate mix
│       → Human reviews best clips, posts manually via Composio
```

### Setup Prerequisites

| Step | What | Profile | Effort |
|---|---|---|---|
| 1 | Enable `image_gen` toolset on social_media, model `fal-ai/ideogram/v3` | code_architect | config.yaml line |
| 2 | Set `use_gateway: true` (Nous Portal) OR add `FAL_KEY` to social_media `.env` | code_architect | config + env var |
| 3 | Install Pillow (`pip install Pillow`) for logo compositing | code_architect | One-time |
| 4 | Create client brand guide: scrape website CSS for colors/fonts, save logo PNGs | Researcher + Human | Per client, one-time |
| 5 | (Future) Enable `video_gen` toolset on social_media | code_architect | config.yaml line |
| 6 | Sign up for OpusClip API Pro plan | Human | Signup + API key |

---

## 6. Pre-Post QA Checklist

Before ANY post goes live:

- [ ] Image has been post-processed (grain, desaturation, EXIF added)
- [ ] People shown are REAL staff or consented patients — never fully AI-generated people
- [ ] Location-specific elements visible (landmarks, architecture, seasonal context)
- [ ] Lighting is consistent and natural-looking
- [ ] Skin has visible texture (not airbrushed)
- [ ] Hands/fingers checked for anomalies
- [ ] Text overlays use brand fonts (not AI default typography)
- [ ] Video content ≥ 80% real footage, ≤ 20% AI-enhanced
- [ ] Captions are accurate (medical/technical terminology prone to AI errors)
- [ ] Compliance confirmed (HIPAA for healthcare, no PHI in visuals)

---

## 7. Cost Tiers

| Tier | Monthly | Tools | When |
|------|---------|-------|------|
| **MVP** | ~$5–24 | Hermes FAL (Ideogram 3.0, ~$5/mo) + OpusClip Pro ($19/mo) | Both pipelines automated |
| **Growth** | ~$24–44 | + Bannerbear ($19/mo) for complex branded layouts | When Ideogram text placement isn't sufficient |
| **Scale** | ~$44–54+ | + Hermes video_gen (FAL Veo 3.1 ~$10/mo) for AI-generated B-roll | Add AI-generated supplementary video |

> **Simplified vs. desktop tools:** The MVP stack replaces the old $43–$106/mo stack (CapCut, Descript, Lightroom/Photoshop, Canva, Runway) with a single Hermes tool (`image_generate` with Ideogram 3.0) + OpusClip API for video. Savings: ~$20–$50/mo. No human-operated desktop tools in the critical path. The image pipeline is a single API call — no separate text overlay step.

---

## References

- `references/mobilemd-content-strategy.md` — Client-specific: Cleveland west-side pain points, competitor landscape, content angles, audience trust factors for at-home medical care
- `references/tool-comparison-matrix.md` — Detailed June 2026 comparison of 14 AI image/video tools with photorealism ratings, pricing, API availability
- `references/opusclip-api-reference.md` — OpusClip REST API: endpoint reference, authentication, curation/render preferences, webhook setup, poll-based fallback
- `social-image-post-pipeline` skill — **Primary operational skill.** Two-stage pipeline (Ideogram → Flux refinement → Pillow logo), copywriting rules, brand guide, designer-quality prompting guide, FAL curl workarounds, quality checklist. Load this for any image post generation.
- `educational-post-idea-discovery` skill — Orchestrator workflow: researcher gathers community intelligence → orchestrator ranks ideas → user approves → social_media creates
- `composio-integration` skill — Bannerbear MCP setup, Facebook/Instagram posting, and platform-specific Composio toolkits