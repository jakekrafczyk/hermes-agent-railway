# Scanned PDF Failure Case — CPU-Only Railway (2026-06-04)

## Scenario

14-page scanned/image PDF (`010OurSulfurBarrierApplication.pdf`) — zero embedded text. Orchestrator followed
the 3-tier decision flow (Firecrawl → pymupdf → marker-pdf). All three failed for distinct reasons.

## Failure Chain

| # | Method | Result | Root Cause |
|---|---|---|---|
| 1 | `firecrawl_parse` (primary) | ❌ | `FIRECRAWL_API_URL` not set — needs self-hosted Firecrawl instance |
| 2 | pymupdf (backup) | ❌ | Returns empty text for all 14 pages — this is a scanned image PDF, not text-based |
| 3 | marker-pdf full run (backup) | ❌ | 600s timeout — 381 text recognition items, ~4 min/page → ~56 min total |
| 4 | marker-pdf 1-page test | ⚠️ | 43/44 items completed in 300s — works but too slow for multi-page within timeouts |
| 5 | `vision_analyze` | ❌ | No vision provider configured for openrouter |
| 6 | pytesseract | ❌ | No tesseract binary; no root for `apt-get install` |
| 7 | marker-pdf + background parallel | ❌ | 5 parallel jobs spawned, all lost between turns |
| 8 | marker-pdf + delegate_task | ❌ | 600s timeout — 39 API calls, OCR not completed |

## Root Cause

The 3-tier decision flow (Firecrawl → pymupdf → marker-pdf) works for text-based PDFs but
**fails for scanned PDFs on CPU-only infrastructure** when:

1. No self-hosted Firecrawl instance (primary path unavailable)
2. PDF is image-only (pymupdf path returns nothing)
3. CPU OCR is too slow for multi-page documents within 600s timeouts

## What Worked (Partial)

- **marker-pdf single page:** 43/44 recognition items in 300s, correct output
- **marker-pdf layout recognition:** 17s/page — the slow part is text recognition (~4 min/page), not layout
- **pymupdf page image extraction:** Works at 150+ DPI, slow for high-res but functional

## Fixes That Would Resolve This

1. **Self-hosted Firecrawl** — Set `FIRECRAWL_API_URL` → `firecrawl_parse` becomes the fast primary path for all PDFs
2. **Increase marker-pdf timeout** — 900-1200s for multi-page scanned PDFs (or cronjob with wrapper script)
3. **GPU access** — marker-pdf at 0.2s/page would process 14 pages in ~3 seconds
4. **Vision provider** — Configure vision for openrouter → `vision_analyze` becomes available as alternative OCR path

## Key Lesson

**Stop on 3rd failure, don't keep retrying.** After Firecrawl failed, pymupdf returned empty, and
marker-pdf timed out once — the orchestrator should have generated the error report immediately
rather than trying 5 more variations (background parallel, delegate, page ranges, lower DPI, etc.).