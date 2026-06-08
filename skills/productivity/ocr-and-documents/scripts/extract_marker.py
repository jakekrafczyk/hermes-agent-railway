#!/usr/bin/env python3
"""
extract_marker.py — High-quality PDF extraction using marker-pdf (OCR, equations, forms).

Usage:
    python extract_marker.py document.pdf                    # Markdown output
    python extract_marker.py document.pdf --json             # JSON with metadata
    python extract_marker.py document.pdf --output_dir out/  # Save to directory
    python extract_marker.py scanned.pdf                     # Scanned PDF (OCR)
    python extract_marker.py document.pdf --use_llm          # LLM-boosted accuracy
    python extract_marker.py --check                         # Check disk space
"""

import argparse
import json
import os
import shutil
import subprocess
import sys


def check_disk(min_gb: float = 5.0) -> dict:
    """Check available disk space."""
    usage = shutil.disk_usage(os.path.expanduser("~"))
    free_gb = usage.free / (1024**3)
    total_gb = usage.total / (1024**3)
    return {
        "free_gb": round(free_gb, 2),
        "total_gb": round(total_gb, 2),
        "sufficient": free_gb >= min_gb,
        "required_gb": min_gb,
    }


def extract_marker(
    pdf_path: str,
    output_dir: str | None = None,
    json_output: bool = False,
    use_llm: bool = False,
    force_ocr: bool = False,
    languages: str | None = None,
):
    """Run marker_single on a PDF."""
    cmd = [sys.executable, "-m", "marker_single", pdf_path]

    if output_dir:
        cmd.extend(["--output_dir", output_dir])
    else:
        cmd.extend(["--output_dir", "./marker_output"])

    if force_ocr:
        cmd.append("--force_ocr")

    if languages:
        cmd.extend(["--languages", languages])

    if use_llm:
        cmd.append("--use_llm")

    if json_output:
        cmd.append("--output_format")
        cmd.append("json")

    print(f"Running: {' '.join(cmd)}", file=sys.stderr)
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Extract content from PDFs using marker-pdf (high-quality OCR)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("pdf", nargs="?", help="Path to PDF file")
    parser.add_argument("--json", action="store_true", help="Output as JSON with metadata")
    parser.add_argument("--output_dir", "-o", help="Output directory for extracted content")
    parser.add_argument("--check", action="store_true", help="Check disk space only")
    parser.add_argument("--use_llm", action="store_true", help="Use LLM to boost accuracy")
    parser.add_argument("--force_ocr", action="store_true", help="Force OCR even on text PDFs")
    parser.add_argument("--languages", help="Languages for OCR, e.g. 'en,fr,de'")

    args = parser.parse_args()

    if args.check:
        info = check_disk()
        print(json.dumps(info, indent=2))
        if info["sufficient"]:
            print(f"\n✅ {info['free_gb']}GB free — sufficient for marker-pdf ({info['required_gb']}GB required)")
        else:
            print(f"\n❌ Only {info['free_gb']}GB free — need at least {info['required_gb']}GB for marker-pdf")
        return

    if not args.pdf:
        parser.print_help()
        print("\nError: PDF path required", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.pdf):
        print(f"Error: File not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)

    # Pre-flight disk check
    info = check_disk()
    if not info["sufficient"]:
        print(
            f"Warning: Only {info['free_gb']}GB free. marker-pdf may fail due to insufficient space.",
            file=sys.stderr,
        )

    print(f"Processing {args.pdf} with marker-pdf...", file=sys.stderr)
    rc = extract_marker(
        args.pdf,
        output_dir=args.output_dir,
        json_output=args.json,
        use_llm=args.use_llm,
        force_ocr=args.force_ocr,
        languages=args.languages,
    )

    if rc != 0:
        print(f"\nError: marker_single exited with code {rc}", file=sys.stderr)
        print("Common issues:", file=sys.stderr)
        print("  - First run downloads ~3.3GB of models to ~/.cache/datalab/. Retry if network error.", file=sys.stderr)
        print("  - Check ~/.cache/datalab/ for model files (marker-pdf 1.10.2).", file=sys.stderr)
        sys.exit(rc)

    print("\n✅ Extraction complete.", file=sys.stderr)


if __name__ == "__main__":
    main()
