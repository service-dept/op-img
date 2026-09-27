#!/usr/bin/env python3
"""Blur the highlights at several radii and screen them back for a soft glow."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter


def main() -> None:
    parser = argparse.ArgumentParser(description="Highlight bloom and halation.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=1.0, help="Glow strength, 0 to 2 (default: 1.0)")
    parser.add_argument("--threshold", type=int, default=170, help="Brightness above which pixels glow, 0 to 255 (default: 170)")
    parser.add_argument("--radius", type=float, default=8.0, help="Base glow radius in pixels (default: 8.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 2.0:
        parser.error("--amount must be between 0 and 2")
    if not 0 <= args.threshold <= 255:
        parser.error("--threshold must be between 0 and 255")
    if args.radius <= 0:
        parser.error("--radius must be more than 0")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    lum = arr @ np.array([0.299, 0.587, 0.114])
    bright = arr * np.clip((lum - args.threshold) / max(255 - args.threshold, 1), 0.0, 1.0)[:, :, None]

    halo = np.zeros_like(arr)
    for scale, weight in ((1, 0.5), (3, 0.3), (9, 0.2)):
        sigma = args.radius * scale
        halo += weight * gaussian_filter(bright, (sigma, sigma, 0))
    glow = np.clip(halo * args.amount, 0, 255)

    # Screen blend: never darkens.
    result = 255.0 - (255.0 - arr) * (255.0 - glow) / 255.0
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-bloom{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved bloom image to {out_path} (amount={args.amount}, threshold={args.threshold}, radius={args.radius})", file=sys.stderr)


if __name__ == "__main__":
    main()
