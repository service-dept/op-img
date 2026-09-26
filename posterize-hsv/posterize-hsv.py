#!/usr/bin/env python3
"""Quantize H, S, V channels independently for a posterization effect."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def posterize_hsv(image: Image.Image, h_levels: int, s_levels: int, v_levels: int) -> Image.Image:
    """Quantize each HSV channel to the specified number of levels."""
    hsv = image.convert("HSV")
    arr = np.array(hsv, dtype=np.float64)

    levels = [h_levels, s_levels, v_levels]
    for ch in range(3):
        n = levels[ch]
        arr[:, :, ch] = np.floor(arr[:, :, ch] / 256.0 * n) * (255.0 / (n - 1)) if n > 1 else 0

    arr = np.clip(arr, 0, 255).astype(np.uint8)
    hsv_out = Image.merge("HSV", [Image.fromarray(arr[:, :, c]) for c in range(3)])
    return hsv_out.convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description="Posterize an image by quantizing HSV channels.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument(
        "--h-levels",
        type=int,
        default=8,
        help="Number of hue levels (default: 8)",
    )
    parser.add_argument(
        "--s-levels",
        type=int,
        default=4,
        help="Number of saturation levels (default: 4)",
    )
    parser.add_argument(
        "--v-levels",
        type=int,
        default=4,
        help="Number of value/brightness levels (default: 4)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(args.input).convert("RGB")

    result = posterize_hsv(img, args.h_levels, args.s_levels, args.v_levels)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-posterize{ext or '.png'}"

    result.save(out_path)
    print(
        f"Saved posterized image to {out_path} (h={args.h_levels}, s={args.s_levels}, v={args.v_levels})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
