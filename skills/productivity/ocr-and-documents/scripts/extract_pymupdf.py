#!/usr/bin/env python3
"""
extract_pymupdf.py — Extract text, markdown, tables, images, and metadata from PDFs using pymupdf.

Usage:
    python extract_pymupdf.py document.pdf                    # Plain text
    python extract_pymupdf.py document.pdf --markdown         # Markdown (via pymupdf4llm)
    python extract_pymupdf.py document.pdf --tables           # Tables only
    python extract_pymupdf.py document.pdf --images out/      # Extract embedded images
    python extract_pymupdf.py document.pdf --metadata         # Title, author, pages
    python extract_pymupdf.py document.pdf --pages 0-4        # Specific pages (0-indexed)
    python extract_pymupdf.py document.pdf --markdown --pages 0-2  # Combine flags
"""

import argparse
import json
import os
import sys
from pathlib import Path


def extract_text(pdf_path: str, pages: list[int] | None = None) -> str:
    """Extract plain text from a PDF."""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    texts = []
    target_pages = pages if pages is not None else range(len(doc))
    for i in target_pages:
        if i < len(doc):
            page = doc[i]
            texts.append(page.get_text())
    doc.close()
    return "\n\n".join(texts)


def extract_markdown(pdf_path: str, pages: list[int] | None = None) -> str:
    """Extract markdown from a PDF using pymupdf4llm."""
    import pymupdf4llm
    if pages is not None:
        return pymupdf4llm.to_markdown(pdf_path, pages=pages)
    return pymupdf4llm.to_markdown(pdf_path)


def extract_tables(pdf_path: str, pages: list[int] | None = None) -> str:
    """Extract tables from a PDF as formatted text."""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    output = []
    target_pages = pages if pages is not None else range(len(doc))
    for i in target_pages:
        if i < len(doc):
            page = doc[i]
            tables = page.find_tables()
            if tables and tables.tables:
                output.append(f"--- Page {i+1} ---")
                for t_idx, table in enumerate(tables.tables):
                    output.append(f"\nTable {t_idx+1}:")
                    df = table.extract()
                    output.append(str(df))
    doc.close()
    return "\n".join(output) if output else "No tables found."


def extract_images(pdf_path: str, output_dir: str, pages: list[int] | None = None):
    """Extract embedded images from a PDF."""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    os.makedirs(output_dir, exist_ok=True)
    count = 0
    target_pages = pages if pages is not None else range(len(doc))
    for i in target_pages:
        if i < len(doc):
            page = doc[i]
            images = page.get_images()
            for img_idx, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]
                fname = os.path.join(output_dir, f"page{i+1}_img{img_idx+1}.{ext}")
                with open(fname, "wb") as f:
                    f.write(image_bytes)
                count += 1
    doc.close()
    print(f"Extracted {count} images to {output_dir}")


def extract_metadata(pdf_path: str) -> dict:
    """Extract metadata from a PDF."""
    import pymupdf
    doc = pymupdf.open(pdf_path)
    meta = {
        "path": pdf_path,
        "pages": len(doc),
        "metadata": dict(doc.metadata),
        "toc": doc.get_toc(),
    }
    doc.close()
    return meta


def parse_pages(pages_str: str) -> list[int] | None:
    """Parse page range like '0-4' or '1,2,3' into a list of ints (0-indexed)."""
    if not pages_str:
        return None
    pages = []
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            pages.extend(range(int(start.strip()), int(end.strip()) + 1))
        else:
            pages.append(int(part))
    return pages


def main():
    parser = argparse.ArgumentParser(
        description="Extract content from PDFs using pymupdf",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("--markdown", action="store_true", help="Output as markdown (via pymupdf4llm)")
    parser.add_argument("--tables", action="store_true", help="Extract tables only")
    parser.add_argument("--images", metavar="DIR", help="Extract embedded images to DIR")
    parser.add_argument("--metadata", action="store_true", help="Show metadata only")
    parser.add_argument("--pages", help="Page range, e.g. '0-4' or '0,2,4' (0-indexed)")
    parser.add_argument("--output", "-o", help="Write output to file instead of stdout")

    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print(f"Error: File not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)

    pages = parse_pages(args.pages)

    if args.metadata:
        meta = extract_metadata(args.pdf)
        output = json.dumps(meta, indent=2, default=str)
    elif args.tables:
        output = extract_tables(args.pdf, pages)
    elif args.images:
        extract_images(args.pdf, args.images, pages)
        return
    elif args.markdown:
        output = extract_markdown(args.pdf, pages)
    else:
        output = extract_text(args.pdf, pages)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
