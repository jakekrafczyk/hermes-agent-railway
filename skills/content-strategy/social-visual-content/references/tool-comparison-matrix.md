# AI Photo/Video Tool Comparison Matrix — June 2026

Detailed comparison of 14 tools across AI image generation, video generation, video editing, and post-processing.
Ratings reflect photorealism and "non-AI-looking" capability for social media marketing use.

## AI Image Generation

| Tool | Photorealism | Pricing | API | Non-AI-Looking | Notes |
|------|-------------|---------|-----|---------------|-------|
| Midjourney V7 | ★★★★★ | $10–$60/mo | Indirect (EvoLink) | 9/10 | Best aesthetics; `--style raw` for natural look; no native REST API |
| GPT Image 2 (OpenAI) | ★★★★★ | $0.04–0.06/image | ✅ Native | 8/10 | Best prompt adherence; SOTA text rendering; ~20s generation |
| Flux 2 Pro (via FAL) | ★★★★½ | $0.05/image (FAL) | ✅ FAL, Replicate | 8.5/10 | Already integrated in Hermes via FAL; strong photorealism |
| Adobe Firefly 5 | ★★★★☆ | $9.99–$199.99/mo | ✅ | 7/10 | Commercial-safe; Photoshop/Lightroom integration; slightly stiff |
| Ideogram 3.0 | ★★★★☆ | $7–$20/mo | ✅ | 8/10 | Best text-in-image accuracy (98%); Realistic preset |
| Leonardo AI | ★★★★☆ | Free–$24/mo | ✅ | 8/10 | Phoenix model + Alchemy v4; slightly synthetic default |
| Stable Diffusion (Flux base) | ★★★☆☆ | Free (self-hosted) | ✅ | 6/10 | Needs LoRA fine-tuning; "when perfect, looks like AI" |
| Canva AI | ★★★☆☆ | $12.99/mo (Pro) | Limited | 6/10 | Good for design, not primary photorealism |
| Meta AI | ★★★½☆ | Free | ❌ | 7/10 | Social-first; limited control; no developer API |

**Top 3 for Photorealism (Non-AI-Looking):**
1. Midjourney V7 — Best when using camera metadata prompts + `--style raw`
2. Flux 2 Pro via FAL — Best API-accessible; already in Hermes
3. GPT Image 2 — Best prompt understanding; world-aware realism

## AI Video Generation

| Tool | Scene Quality | Pricing | API | Best Use Case |
|------|-------------|---------|-----|---------------|
| Google Veo/Flow | ★★★★★ | Enterprise/limited | Limited | Cinematic B-roll, atmospheric video |
| Runway Gen-4/4.5 | ★★★★½ | $12–$188/mo | ✅ | Full production pipeline; text/image-to-video |
| Kling 2.6/3.0 | ★★★★½ | Credit-based | Limited | Complex scenes, realistic human motion |
| Luma Ray2/3 | ★★★★☆ | Credit-based | ✅ | Image-to-video, B-roll, mood-led clips |
| Adobe Firefly Video | ★★★★☆ | From $10/mo | ✅ | Brand-safe commercial video, B-roll |
| Pika 2.5 | ★★★★☆ | Free–$10/mo | Limited | Short-form social effects, animation |
| Sora 2 (OpenAI) | ★★★★☆ | Pro/Plus access | ❌ | Experimental cinematic |

## AI Avatar & Talking-Head Video

| Tool | Quality | Pricing | Best For |
|------|---------|---------|----------|
| Synthesia | ★★★★☆ | Free–$89/mo | Training, internal comms, brand spokesperson |
| HeyGen | ★★★★☆ | $29–$149/mo | Marketing explainers, localization, UGC ads |
| Descript | ★★★★☆ | Free–$24/mo | Text-based editing, voice cloning, transcription |

⚠️ **Caution:** Avatar/talking-head video triggers AI-detection for skeptical audiences. Use ONLY for voiceover narration with real footage, never synthetic spokespeople.

## AI Video Editing from Raw Footage

| Tool | Strengths | Weaknesses | Pricing | Best For |
|------|-----------|------------|---------|----------|
| OpusClip 3.0 | AI clipping (viral moments); auto captions; B-roll; reframe; multi-platform publish | Pro required for B-roll; limited manual control | Free–$19/mo | Long-form→short-form clipping |
| Descript | Text-based editing; AI voice cloning; filler removal; accurate transcription | Podcast/long-form focused; manual reframe | Free–$24/mo | Educational/healthcare content |
| CapCut Pro | Unlimited AI; auto captions; 4K export; brand kit; cheapest | Requires manual refinement; less specialized AI clipping | Free–$7.99/mo | Best value; hands-on editing |
| VEED.io | Auto subtitles (high accuracy); multi-language translation | Watermark on free; 720p limit free | Free–$35/mo | Quick captioning, simple edits |
| Runway Gen-4 | Text-to-video; image-to-video; full timeline | Expensive; overkill for editing only | $12–$188/mo | AI-generated B-roll supplement |

### Capability Matrix

| Capability | OpusClip | Descript | CapCut Pro | VEED.io | Runway |
|-----------|----------|----------|------------|---------|--------|
| Speaker detection / clip finding | ✅ | ✅ | ✅ | ❌ | N/A |
| Auto B-roll insertion | ✅ | ❌ | ✅ | ❌ | ✅ |
| Auto captions | ✅ | ✅ | ✅ | ✅ | ❌ |
| Auto reframe (16:9→9:16) | ✅ | ⚠️ | ✅ | ✅ | ⚠️ |
| AI pacing optimization | ✅ | ⚠️ | ✅ | ❌ | ❌ |
| Filler word removal | ❌ | ✅ | ❌ | ❌ | ❌ |
| Text-based editing | ❌ | ✅ | ❌ | ❌ | ❌ |
| Face tracking/centering | ✅ | ❌ | ✅ | ❌ | ❌ |
| Multi-platform publish | ✅ | ❌ | ✅ | ❌ | ❌ |

## Post-Processing

| Tool | Pricing | Best For |
|------|---------|----------|
| Adobe Lightroom + Photoshop | $22.99/mo (Photography plan) | Full control; industry standard; grain/desaturation/EXIF |
| Adobe Firefly | $9.99–$59.99/mo | Inpainting; generative fill; commercial-safe |
| GIMP (free alternative) | Free | Budget post-processing; limited but functional |
| exiftool | Free | CLI EXIF injection; scriptable |

## Source Notes
- Research conducted June 2026 — tool capabilities and pricing shift rapidly
- Photorealism ratings are relative to marketing social content use case
- "Non-AI-Looking" rating incorporates both raw output quality AND post-processing requirement
- Hermes `image_generate` uses FAL.ai backend with 11 models; Flux 2 Pro and GPT Image 2 are the photorealism picks
- Composio handles social posting (not covered here — see `composio-integration` skill)
