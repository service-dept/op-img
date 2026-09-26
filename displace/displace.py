#!/usr/bin/env python3
"""Move each pixel along an angle by an amount taken from its own blurred brightness."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates


def main() -> None:
    parser = argparse.ArgumentParser(description="Displace pixels by their own brightness.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=60.0, help="Maximum displacement in pixels, 0 to 300 (default: 60.0)")
    parser.add_argument("--angle", type=float, default=0.0, help="Displacement direction in degrees (default: 0.0)")
    parser.add_argument("--blur", type=float, default=3.0, help="Blur sigma of the brightness map (default: 3.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 300.0:
        parser.error("--amount must be between 0 and 300")
    if args.blur < 0:
        parser.error("--blur must be 0 or more")

    img = Image.open(args.input).convert("RGB")
    arr = np.array(img, dtype=np.float64)
    h, w, _ = arr.shape

    # Centred on mid-grey, so mid-tones stay put while light and dark move in opposite directions.
    brightness = gaussian_filter(np.array(img.convert("L"), dtype=np.float64), args.blur) / 255.0 - 0.5
    rad = np.radians(args.angle)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    src_x = xx + args.amount * brightness * np.cos(rad)
    src_y = yy + args.amount * brightness * np.sin(rad)

    result = np.zeros_like(arr)
    for c in range(3):
        result[:, :, c] = map_coordinates(arr[:, :, c], [src_y, src_x], order=1, mode="reflect")

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-displace{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved displaced image to {out_path} (amount={args.amount}, angle={args.angle}, blur={args.blur})", file=sys.stderr)


if __name__ == "__main__":
    main()
