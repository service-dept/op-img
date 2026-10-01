#!/usr/bin/env python3
"""Pixelate an image by sampling it down and scaling it back up with nearest-neighbor."""

import argparse
import os
import sys

from PIL import Image


def res_crush(image: Image.Image, size: int) -> Image.Image:
    """Point-sample to fit within size x size, keeping the aspect ratio, then scale back."""
    w, h = image.size
    scale = min(size / w, size / h)
    small = image.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.NEAREST)
    return small.resize((w, h), Image.NEAREST)


def main() -> None:
    parser = argparse.ArgumentParser(prog=os.environ.get("OP_IMG_PROG"), description="Pixelate an image by downscaling and upscaling with nearest-neighbor.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--size", type=int, default=64, help="Longest side of the sampled image in pixels (default: 64)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if args.size < 1:
        parser.error("--size must be at least 1")

    result = res_crush(Image.open(args.input).convert("RGB"), args.size)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-pixelate-{args.size}{ext or '.png'}"

    result.save(out_path)
    print(f"Pixelated to {args.size}px → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
