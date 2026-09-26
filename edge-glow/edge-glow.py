#!/usr/bin/env python3
"""Turn edges into neon lines in each pixel's own hue, with a bloom halo, over a darkening base."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, sobel


def main() -> None:
    parser = argparse.ArgumentParser(description="Glowing neon edges.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=1.0, help="Blend from the photo (0) to glowing edges on black (1) (default: 1.0)")
    parser.add_argument("--radius", type=float, default=6.0, help="Halo blur sigma in pixels (default: 6.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")
    if args.radius < 0:
        parser.error("--radius must be 0 or more")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    lum = gaussian_filter(arr @ np.array([0.299, 0.587, 0.114]), 1.0)
    magnitude = np.hypot(sobel(lum, axis=1), sobel(lum, axis=0))
    peak = np.percentile(magnitude, 99)
    edges = np.clip(magnitude / peak, 0.0, 1.0) if peak > 0 else np.zeros_like(magnitude)

    # Each edge glows in its own pixel's hue at full brightness; black pixels glow white.
    brightest = arr.max(axis=2, keepdims=True)
    hue = np.where(brightest > 0, arr / np.maximum(brightest, 1e-9), 1.0)
    glow = hue * 255.0 * edges[:, :, None]
    halo = gaussian_filter(glow, (args.radius, args.radius, 0))

    result = arr * (1.0 - args.amount) + (glow + halo) * args.amount
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-edgeglow{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved edge-glow image to {out_path} (amount={args.amount}, radius={args.radius})", file=sys.stderr)


if __name__ == "__main__":
    main()
