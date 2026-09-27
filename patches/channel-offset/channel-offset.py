#!/usr/bin/env python3
"""Shift the red, green and blue channels by independent pixel offsets, wrapping at the edges."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def parse_offset(value: str) -> tuple[int, int]:
    """'X,Y' to (x, y). A single number applies to both axes."""
    parts = value.split(",")
    try:
        if len(parts) == 1:
            return int(parts[0]), int(parts[0])
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except ValueError:
        pass
    raise argparse.ArgumentTypeError(f"not an offset: '{value}' (use X,Y, for example 30,15)")


def channel_offset(image: Image.Image, offsets: list[tuple[int, int]]) -> Image.Image:
    arr = np.array(image)
    out = np.empty_like(arr)
    for c, (x, y) in enumerate(offsets):
        # Positive offsets move the channel right and down.
        out[:, :, c] = np.roll(np.roll(arr[:, :, c], y, axis=0), x, axis=1)
    return Image.fromarray(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Shift RGB channels by independent pixel offsets.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--r", type=parse_offset, default=(140, 50), help="Red channel offset X,Y in pixels (default: 140,50)")
    parser.add_argument("--g", type=parse_offset, default=(-20, 40), help="Green channel offset X,Y in pixels (default: -20,40)")
    parser.add_argument("--b", type=parse_offset, default=(-120, -40), help="Blue channel offset X,Y in pixels (default: -120,-40)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    result = channel_offset(Image.open(args.input).convert("RGB"), [args.r, args.g, args.b])

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-offset{ext or '.png'}"

    result.save(out_path)
    fmt = lambda o: f"{o[0]},{o[1]}"
    print(f"Channel offset (r:{fmt(args.r)} g:{fmt(args.g)} b:{fmt(args.b)}) → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
