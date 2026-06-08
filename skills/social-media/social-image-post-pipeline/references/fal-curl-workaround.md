# FAL API Direct Curl Workaround

When `image_generate` returns "No credentials found" after adding `FAL_KEY` mid-session, the session environment doesn't pick up the new variable until restart. Use direct FAL API curl calls as a workaround.

All calls use the same FAL_KEY. The key is in `/data/.env` and `/data/profiles/social_media/.env`.

## Ideogram 3.0 (Text + Image Generation)

Best for social media graphics with readable text. ~$0.04/image.

```bash
FAL_KEY="<key>"

# Submit
curl -sS -X POST "https://queue.fal.run/fal-ai/ideogram/v3" \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"...","image_size":"square_hd","num_images":1}'

# Poll (wait 12-20s)
curl -sS "https://queue.fal.run/fal-ai/ideogram/requests/<request_id>/status" \
  -H "Authorization: Key $FAL_KEY"

# Fetch result URL
curl -sS "https://queue.fal.run/fal-ai/ideogram/requests/<request_id>" \
  -H "Authorization: Key $FAL_KEY" | python3 -c "import sys,json; print(json.load(sys.stdin)['images'][0]['url'])"
```

**Image sizes:** `square_hd`, `square`, `portrait_4_3`, `portrait_16_9`, `landscape_4_3`, `landscape_16_9`. No native 4:5 — crop from portrait_4_3.

## FLUX.1 [dev] Image-to-Image (Refinement)

Sharpens edges, unifies shadows, improves typography after Ideogram. ~$0.03/MP. Use strength 0.15-0.25.

```bash
curl -sS -X POST "https://queue.fal.run/fal-ai/flux/dev/image-to-image" \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_url":"<url>","prompt":"Same layout. Clean sharp professional. No artifacts.","strength":0.2,"num_inference_steps":28}'

# Poll uses: /fal-ai/flux/requests/<id> (different path than Ideogram!)
curl -sS "https://queue.fal.run/fal-ai/flux/requests/<request_id>/status" \
  -H "Authorization: Key $FAL_KEY"
```

## Pitfalls

- FAL `image_size` names differ from Hermes `aspect_ratio` — don't cross them
- Poll status first, then fetch result separately — the result URL may 404 if fetched too early
- Ideogram and FLUX use different request paths (`/ideogram/requests/` vs `/flux/requests/`)
- Always use PNG base for Pillow compositing, save final as JPEG quality=95
