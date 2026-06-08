# OpusClip API Reference — Automated Video Clipping

Complete reference for the OpusClip REST API. Submit a long-form video URL, receive viral short-form clips with captions, reframing, and filler word removal — fully automated.

**API Base:** `https://api.opus.pro`  
**Auth:** Bearer token (`Authorization: Bearer <API_KEY>`)  
**Docs:** https://help.opus.pro/api-reference/overview  
**LLM-friendly index:** https://help.opus.pro/llms.txt  

---

## Access & Plans

| Plan | API Access | Credits | Concurrency | Monthly API Cap |
|------|-----------|---------|-------------|-----------------|
| Pro (Beta) | ✅ | Per-minute (~$0.05-0.10/min) | 4 parallel projects | 15 hours |
| Business | ✅ | Per-minute | 50 parallel projects | Per contract |

- **1 credit = 1 minute of video processed**
- **10-credit minimum per API project** (not applicable to web submissions)
- **Rate limit:** 30 requests/min per API key
- **Max video:** 10 hours duration, 30 GB file size
- **Project expiry:** 30 days by default (auto-save preserves to storage)
- API key from dashboard: https://clip.opus.pro/dashboard (lower left)

---

## Core Endpoint: Create Project

```
POST /api/clip-projects
```

### Minimal Request

```bash
curl --request POST \
  --url https://api.opus.pro/api/clip-projects \
  --header 'Authorization: Bearer <API_KEY>' \
  --header 'Content-Type: application/json' \
  --data '{
    "videoUrl": "https://www.youtube.com/watch?v=tEXaoozFRes"
  }'
```

Response: `{ "projectId": "proj_abc123", "status": "processing" }`

### Full Request (MobileMD Healthcare Example)

```bash
curl --request POST \
  --url https://api.opus.pro/api/clip-projects \
  --header 'Authorization: Bearer <API_KEY>' \
  --header 'Content-Type: application/json' \
  --data '{
    "videoUrl": "https://drive.google.com/uc?export=download&id=XYZ",
    "uploadedVideoAttr": {
      "title": "MobileMD Provider Home Visit — Cleveland West Side"
    },
    "curationPref": {
      "model": "ClipBasic",
      "clipDurations": [[15, 60]],
      "genre": "Educational",
      "topicKeywords": ["at-home care", "urgent care alternative", "Cleveland"]
    },
    "renderPref": {
      "layoutAspectRatio": "portrait",
      "quickstartConfig": {
        "enableRemoveFillerWords": true
      }
    },
    "brandTemplateId": "mobilemd_brand",
    "importPreference": {
      "sourceLang": "en"
    },
    "conclusionActions": [
      {
        "type": "WEBHOOK",
        "notifyFailure": true,
        "url": "https://your-hermes-webhook.example.com/opusclip"
      }
    ]
  }'
```

---

## Supported Video Sources

Accepts public video URLs from: YouTube, Google Drive, Vimeo, Zoom, Zoom Clips, Rumble, Twitch, Facebook, LinkedIn, X, Dropbox, Riverside, Loom, Frame.io, StreamYard, Medal.tv, and any public S3 MP4 link.

For raw MobileMD footage, host on Google Drive (shareable link) or S3.

---

## Curation Preferences

| Field | Values | Notes |
|---|---|---|
| `model` | `"ClipBasic"`, `"ClipAnything"` | ClipBasic = topic-guided; ClipAnything = more flexible |
| `clipDurations` | `[[min_sec, max_sec]]` | e.g., `[[15, 60]]` for 15-60 second clips |
| `genre` | `"Auto"` or specific genre | |
| `topicKeywords` | `["keyword1", "keyword2"]` | Only for ClipBasic model |
| `range` | `{ "startSec": 0, "endSec": 300 }` | Limit to specific video section |
| `skipCurate` | `true` / `false` | Skip clipping entirely (just upload/reprocess) |

---

## Render Preferences

| Field | Values | Notes |
|---|---|---|
| `layoutAspectRatio` | `"portrait"`, `"landscape"`, `"square"` | 9:16 for Reels/TikTok, 1:1 for feed |
| `quickstartConfig.enableRemoveFillerWords` | `true` / `false` | Removes "um", "uh", "like", etc. |
| `quickstartConfig.enableAutoCaptions` | `true` (default) | AI captions with emoji |

---

## Brand Templates

Create brand templates in the OpusClip dashboard (clip.opus.pro/dashboard). Templates control: colors, fonts, caption styling, logo placement, intro/outro animations.

Preset templates available: `"preset-fancy-Karaoke"`, etc. Custom templates use the template ID string from your dashboard.

**For MobileMD:** Create a template with brand colors (likely medical blue/white), clean sans-serif font, subtle logo watermark.

---

## Conclusion Actions (Webhook)

When processing completes, OpusClip POSTs to your webhook URL:

```json
{
  "projectId": "proj_abc123",
  "status": "completed",
  "clips": [
    {
      "id": "clip_001",
      "url": "https://cdn.opus.pro/clips/abc123/001.mp4",
      "duration": 45,
      "title": "MobileMD: Same-Day Care at Home",
      "hook": "Why wait 3 hours at the ER when a provider can be at your door in 60 minutes?"
    },
    {
      "id": "clip_002",
      "url": "https://cdn.opus.pro/clips/abc123/002.mp4",
      "duration": 38,
      "title": "What $150 Gets You vs. a $1,500 ER Visit",
      "hook": "Cleveland west siders — here's the honest cost breakdown."
    }
  ]
}
```

**Webhook security:** Headers `X-Opus-Signature`, `X-Opus-Salt`, `X-Opus-Timestamp` for signature verification. See https://help.opus.pro/api-reference/webhook#securing-your-webhook.

**Failure webhooks:** When `notifyFailure: true`, also POSTs on error with `status: "failed"` and error details.

---

## Polling Fallback (No Webhook Needed)

If you can't expose a public webhook endpoint (common on Railway/containerized deployments), poll the project status:

```bash
curl --request GET \
  --url https://api.opus.pro/api/clip-projects/proj_abc123 \
  --header 'Authorization: Bearer <API_KEY>'
```

Response: `{ "projectId": "proj_abc123", "status": "processing" | "completed" | "failed", "clips": [...] }`

Poll every 30 seconds until status is `"completed"` or `"failed"`. Typical processing time: 1-5 minutes for a 10-30 minute video.

---

## Query Clips

```bash
curl --request GET \
  --url 'https://api.opus.pro/api/clip-projects/proj_abc123/clips?limit=10&offset=0' \
  --header 'Authorization: Bearer <API_KEY>'
```

---

## Share Project

```bash
curl --request POST \
  --url https://api.opus.pro/api/clip-projects/proj_abc123/share \
  --header 'Authorization: Bearer <API_KEY>' \
  --header 'Content-Type: application/json' \
  --data '{ "expiryDays": 7 }'
```

Returns a shareable link for human review.

---

## Social Posting (Optional — Skip if Posting Manually)

OpusClip can generate social copy and post/schedule to platforms. If using manual Composio posting instead, skip this and use Hermes social_media profile for caption generation.

```bash
curl --request POST \
  --url https://api.opus.pro/api/clip-projects/proj_abc123/social-post \
  --header 'Authorization: Bearer <API_KEY>' \
  --header 'Content-Type: application/json' \
  --data '{
    "clipId": "clip_001",
    "platform": "facebook",
    "scheduleTime": "2026-06-10T14:00:00Z"
  }'
```

---

## Common Pitfalls

- **Drive links must be public/shareable.** Use `https://drive.google.com/uc?export=download&id=FILE_ID` format.
- **10-credit minimum per project.** Short videos (<10 min) still consume 10 credits minimum via API.
- **Video must be accessible via direct URL.** Password-protected or login-required videos fail.
- **Brand template must exist before referencing.** Create in dashboard first, then reference by ID in API calls.
- **Webhook URL must be publicly accessible.** On Railway, use `RAILWAY_PUBLIC_DOMAIN` or fall back to polling.
- **Supported languages:** 20+ languages. Set `sourceLang` explicitly for non-English videos — auto-detection is less reliable.
