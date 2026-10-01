#!/usr/bin/env python3
"""Re-encode as a low-quality JPEG many times, shifting a pixel each time so the artifacts pile up."""

import argparse
import io
import os
import sys

from PIL import Image, ImageChops


def main() -> None:
    parser = argparse.ArgumentParser(prog=os.environ.get("OP_IMG_PROG"), description="Generational JPEG loss.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--quality", type=int, default=5, help="JPEG quality per generation, 1 to 95 (default: 5)")
    parser.add_argument("--generations", type=int, default=80, help="Number of re-encodes, 0 to 200 (default: 80)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 1 <= args.quality <= 95:
        parser.error("--quality must be between 1 and 95")
    if not 0 <= args.generations <= 200:
        parser.error("--generations must be between 0 and 200")

    img = Image.open(args.input).convert("RGB")
    for _ in range(args.generations):
        # Shifting moves the 8x8 block grid, so each pass damages new places instead of settling.
        img = ImageChops.offset(img, 1, 0)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=args.quality, subsampling=2)
        buf.seek(0)
        img = Image.open(buf).convert("RGB")
    img = ImageChops.offset(img, -args.generations, 0)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-jpegrot{ext or '.png'}"

    img.save(out_path)
    print(f"Saved JPEG-rotted image to {out_path} (quality={args.quality}, generations={args.generations})", file=sys.stderr)


if __name__ == "__main__":
    main()
