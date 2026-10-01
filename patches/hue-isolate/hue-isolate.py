#!/usr/bin/env python3
"""Keep one hue band in full color and desaturate everything else."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser(description="Color pop: keep one hue, gray out the rest.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--hue", type=float, default=25.0, help="Hue to keep in degrees, 0 to 360 (default: 25.0)")
    parser.add_argument("--width", type=float, default=20.0, help="Half-width of the kept band in degrees (default: 20.0)")
    parser.add_argument("--amount", type=float, default=1.0, help="Desaturation strength outside the band, 0 to 1 (default: 1.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.hue <= 360.0:
        parser.error("--hue must be between 0 and 360")
    if args.width < 0:
        parser.error("--width must be 0 or more")
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")

    img = Image.open(args.input).convert("RGB")
    arr = np.array(img, dtype=np.float64)
    hue = np.array(img.convert("HSV"), dtype=np.float64)[:, :, 0] * 360.0 / 255.0

    distance = np.abs(hue - args.hue) % 360.0
    distance = np.minimum(distance, 360.0 - distance)
    keep = np.clip(1.0 - (distance - args.width) / 15.0, 0.0, 1.0)

    gray = (arr @ np.array([0.299, 0.587, 0.114]))[:, :, None]
    saturation = keep + (1.0 - keep) * (1.0 - args.amount)
    result = gray + (arr - gray) * saturation[:, :, None]
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-hueiso{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved hue-isolated image to {out_path} (hue={args.hue}, width={args.width}, amount={args.amount})", file=sys.stderr)


if __name__ == "__main__":
    main()
