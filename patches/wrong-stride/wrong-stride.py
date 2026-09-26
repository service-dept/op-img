#!/usr/bin/env python3
"""Flatten pixel buffer and reshape with wrong row width for a diagonal shear effect."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def wrong_stride(image: Image.Image, offset: int) -> Image.Image:
    """Reshape pixel data with a per-row offset to create a diagonal shear effect."""
    arr = np.array(image)
    h, w, _ = arr.shape
    flat = arr.flatten()
    row_bytes = w * 3
    total = len(flat)

    out = np.zeros_like(arr)
    for r in range(h):
        start = (r * row_bytes + r * offset * 3) % total
        row_data = np.empty(row_bytes, dtype=np.uint8)
        for i in range(row_bytes):
            row_data[i] = flat[(start + i) % total]
        out[r] = row_data.reshape(w, 3)

    return Image.fromarray(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reshape pixel data with wrong stride for diagonal shear effect.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument(
        "--offset",
        type=int,
        default=1,
        help="Pixel offset per row (default: 1)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(args.input).convert("RGB")

    result = wrong_stride(img, args.offset)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-stride{ext or '.png'}"

    result.save(out_path)
    print(
        f"Saved wrong-stride image to {out_path} (offset={args.offset})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
