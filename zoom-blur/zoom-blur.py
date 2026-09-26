#!/usr/bin/env python3
"""Average copies of the image scaled up about a centre point, for radial warp-speed streaks."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates


def parse_center(value: str) -> tuple[float, float]:
    try:
        fx, fy = (float(v) for v in value.split(","))
    except ValueError:
        raise argparse.ArgumentTypeError("--center must be X,Y fractions, for example 0.5,0.5")
    if not (0.0 <= fx <= 1.0 and 0.0 <= fy <= 1.0):
        raise argparse.ArgumentTypeError("--center fractions must be between 0 and 1")
    return fx, fy


def main() -> None:
    parser = argparse.ArgumentParser(description="Radial zoom blur about a centre point.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=0.3, help="Zoom strength, 0 to 1; the largest copy is scaled by 1 + amount (default: 0.3)")
    parser.add_argument("--center", type=parse_center, default=(0.5, 0.5), help="Zoom centre as X,Y fractions (default: 0.5,0.5)")
    parser.add_argument("--samples", type=int, default=32, help="Number of scaled copies averaged (default: 32)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")
    if args.samples < 1:
        parser.error("--samples must be at least 1")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    h, w, _ = arr.shape
    cx, cy = args.center[0] * (w - 1), args.center[1] * (h - 1)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)

    acc = np.zeros_like(arr)
    for i in range(args.samples):
        scale = 1.0 + args.amount * i / max(args.samples - 1, 1)
        src_x = cx + (xx - cx) / scale
        src_y = cy + (yy - cy) / scale
        for c in range(3):
            acc[:, :, c] += map_coordinates(arr[:, :, c], [src_y, src_x], order=1, mode="nearest")

    result_img = Image.fromarray(np.clip(np.rint(acc / args.samples), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-zoomblur{ext or '.png'}"

    result_img.save(out_path)
    center = f"{args.center[0]},{args.center[1]}"
    print(f"Saved zoom-blurred image to {out_path} (amount={args.amount}, center={center}, samples={args.samples})", file=sys.stderr)


if __name__ == "__main__":
    main()
