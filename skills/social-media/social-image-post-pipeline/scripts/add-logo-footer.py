#!/usr/bin/env python3
"""Add a branded logo footer to AI-generated social media graphics.

Uses Pillow to composite a dark charcoal footer bar, amber divider line,
and centered logo lockup at the bottom of an image. Does NOT request AI
models to generate logos — uses the official brand file.

Usage:
    python3 add-logo-footer.py <input_image> <logo_file> <output_image>
    
    python3 add-logo-footer.py graphic.png references/voltaic-logo-horizontal.png final.jpg
"""

import sys
from PIL import Image, ImageDraw


def add_logo_footer(img_path, logo_path, output_path):
    """Add branded footer with amber divider and centered logo to an image."""
    img = Image.open(img_path).convert('RGBA')
    w, h = img.size

    # Footer height: 10% of image
    footer_h = int(h * 0.10)

    # Footer bar matching dark charcoal background (#1A1A1A)
    footer = Image.new('RGBA', (w, footer_h), (26, 26, 26, 255))

    # Amber divider line (#C4881A) at top of footer — 3px thick, 70% width
    amber = (196, 136, 26, 255)
    start_x = int(w * 0.15)
    end_x = int(w * 0.85)
    for x in range(start_x, end_x):
        for dy in range(3):
            footer.putpixel((x, dy), amber)

    # Scale logo to 55% of footer height
    logo = Image.open(logo_path).convert('RGBA')
    logo_h = int(footer_h * 0.55)
    ratio = logo_h / logo.height
    logo_w = int(logo.width * ratio)
    logo_scaled = logo.resize((logo_w, logo_h), Image.LANCZOS)

    # Apply 85% opacity
    r, g, b, a = logo_scaled.split()
    a = a.point(lambda p: int(p * 0.85))
    logo_scaled = Image.merge('RGBA', (r, g, b, a))

    # Center logo horizontally and vertically in the footer below the divider
    logo_x = (w - logo_w) // 2
    logo_y = 3 + (footer_h - 3 - logo_h) // 2

    footer.paste(logo_scaled, (logo_x, logo_y), logo_scaled)
    img.paste(footer, (0, h - footer_h), footer)

    img.convert('RGB').save(output_path, quality=95)

    # Verify
    check = Image.open(output_path)
    cw, ch = check.size
    strip = check.crop((0, ch - footer_h, cw, ch))
    pixels = list(strip.getdata())
    amber_px = sum(1 for p in pixels if 185 < p[0] < 210 and 125 < p[1] < 150 and 15 < p[2] < 45)
    verified = "✓" if amber_px > 100 else "✗"
    print(f"{verified} {output_path}: {cw}×{ch}, amber px in footer: {amber_px}")


if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    add_logo_footer(sys.argv[1], sys.argv[2], sys.argv[3])
