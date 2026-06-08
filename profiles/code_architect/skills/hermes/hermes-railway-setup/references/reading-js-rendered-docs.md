# Reading JS-Rendered Documentation Pages

Some doc sites (Mintlify, Next.js SSR) render content entirely in JavaScript —
`web_extract` returns nothing useful because the extract backend is SearXNG (search-only).
`browser_navigate` may be unavailable. Use `curl` + regex on embedded data.

## Pattern: Extract text from Next.js `__next_f` data chunks

Next.js apps embed page content in `self.__next_f.push(...)` script tags.
These chunks contain the compiled MDX/React tree with actual page text.

```python
import subprocess, re
from html import unescape

result = subprocess.run(['curl', '-s', '<URL>'], capture_output=True, text=True)
html = result.stdout

# Pull all __next_f chunks
chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL)

# From each chunk, extract "children" string values (actual rendered text)
for chunk in chunks:
    texts = re.findall(r'children: \\"([^\\"]{3,})\\"', chunk)
    for t in texts:
        t = t.replace('\\\\n', '\n').replace('\\"', '"')
        t = unescape(t)
        if t.strip():
            print(t)
```

This reliably extracts headings, paragraph text, code snippets, and list items
from Mintlify/Next.js doc sites without a browser.

## Filtering for relevant sections

```python
# Find chunks that mention a keyword
for i, chunk in enumerate(chunks):
    if 'keyword' in chunk.lower():
        texts = re.findall(r'children: \\"([^\\"]{2,})\\"', chunk)
        print(f"=== Chunk {i} ===")
        for t in texts[:30]:
            print(repr(t.replace('\\\\n', '\n')))
```

## Extracting shell/code blocks

Code blocks in these pages are wrapped in `<span class="line">` tags with
syntax-highlighted spans. Strip them with:

```python
import re
from html import unescape

def extract_code(html_fragment):
    # Remove all HTML tags
    code = re.sub(r'<[^>]+>', '', html_fragment)
    return unescape(code).strip()
```

## When this is needed

- `web_extract` says "SearXNG is a search-only backend"
- The page is a Mintlify, Nextra, or Next.js SSR doc site
- The browser tool is unavailable (no Chrome installed)

## Sites confirmed to use this pattern

- `supermemory.ai/docs/*` (Mintlify)
- Similar: `firecrawl.dev/docs`, `mintlify.com/docs`
