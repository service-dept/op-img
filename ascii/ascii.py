#!/usr/bin/env python3
"""Replace grid cells with characters chosen by brightness, each in its cell's hue, on black."""

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def glyph_masks(charset: str, cell: int) -> np.ndarray:
    """One cell-by-cell coverage mask (0 to 1) per character, centred in its cell."""
    font = ImageFont.load_default(size=cell)
    masks = []
    for ch in charset:
        tile = Image.new("L", (cell, cell), 0)
        ImageDraw.Draw(tile).text((cell / 2, cell / 2), ch, fill=255, font=font, anchor="mm", stroke_width=1, stroke_fill=255)
        masks.append(np.array(tile, dtype=np.float64) / 255.0)
    return np.stack(masks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the image as coloured ASCII characters.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--cell", type=int, default=10, help="Character cell size in pixels, 6 to 32 (default: 10)")
    parser.add_argument("--charset", default=" .:-=+*#%@", help="Characters from darkest to brightest (default: ' .:-=+*#%%@')")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 6 <= args.cell <= 32:
        parser.error("--cell must be between 6 and 32")
    if not args.charset:
        parser.error("--charset must not be empty")

    img = Image.open(args.input).convert("RGB")
    w, h = img.size
    cols, rows = w // args.cell, h // args.cell
    if cols == 0 or rows == 0:
        print(f"Error: image is smaller than one {args.cell}px cell", file=sys.stderr)
        sys.exit(1)

    small = np.array(img.resize((cols, rows), Image.BOX), dtype=np.float64)
    lum = small @ np.array([0.299, 0.587, 0.114])
    # Stretch brightness to this image's own range so mid-tones reach the dense glyphs.
    # A flat image has no range to stretch, so keep absolute brightness (white stays a glyph).
    lo, hi = np.percentile(lum, 2), np.percentile(lum, 98)
    if hi - lo < 1.0:
        lo, hi = 0.0, 256.0
    norm = np.clip((lum - lo) / max(hi - lo, 1.0), 0.0, 1.0)
    idx = np.clip((norm * len(args.charset)).astype(int), 0, len(args.charset) - 1)

    masks = glyph_masks(args.charset, args.cell)
    coverage = masks[idx].transpose(0, 2, 1, 3).reshape(rows * args.cell, cols * args.cell)
    # The glyph already carries the brightness, so draw it in the cell's hue at full brightness.
    hue = small * 255.0 / np.maximum(small.max(axis=2, keepdims=True), 1.0)
    colour = np.repeat(np.repeat(hue, args.cell, axis=0), args.cell, axis=1)

    result = np.zeros((h, w, 3))
    result[:rows * args.cell, :cols * args.cell] = colour * coverage[:, :, None]
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-ascii{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved ASCII image to {out_path} (cell={args.cell}, charset={len(args.charset)} characters)", file=sys.stderr)


if __name__ == "__main__":
    main()
