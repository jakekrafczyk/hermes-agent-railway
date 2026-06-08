# Cookie Export Formats (Pitfalls)

## hotcleaner.com Cookie Editor — vcrv1 Format

The Cookie Editor extension at hotcleaner.com exports cookies in a proprietary vcrv1
binary format. This format is NOT usable directly.

**Structure:**
```json
{
  "url": "https://www.hotcleaner.com/cookie-editor/cookie-manager.html",
  "version": 2,
  "data": "vcrv1<base64-encoded-binary-blob>..."
}
```

The `vcrv1` prefix is followed by Base64-encoded data that is internally compressed
(possibly LZString or a custom variant). Decoding attempts in this session all failed:

- Base64 decode + zlib decompress → "incorrect header check"
- LZString.decompressFromUTF16 / decompressFromBase64 → null
- Raw binary inspection → no recognizable JSON structure

**Recommendation:** Do NOT use hotcleaner.com exports. Instead, export cookies from:
- **EditThisCookie** extension — exports plain JSON arrays
- **cookie-editor** extension (cggpkbnlneloepbiejicfmkaihnelmeg) — standard Netscape format
- **Firefox/Chrome DevTools** — use Application > Cookies > right-click > export

## Valid Cookie Format for Camofox Injection

```json
[
  {
    "name": "reddit_session",
    "value": "eyJ...",
    "domain": ".reddit.com",
    "path": "/",
    "httpOnly": true,
    "secure": true,
    "sameSite": "Lax",
    "expirationDate": 1749000000
  }
]
```

Required fields: `name`, `value`, `domain`. Recommended: `path`, `httpOnly`, `secure`, `sameSite`.

## Valid Cookie Format for browser_console Injection

```js
document.cookie = "reddit_session=eyJ...; domain=.reddit.com; path=/; secure; httponly";
```

Note: `httponly` cookies cannot be set via `document.cookie` — those must be injected
via the browser's cookie jar (Camofox API, CDP Network.setCookie, or extension).