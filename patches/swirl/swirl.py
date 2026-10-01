#!/usr/bin/env python3
"""Twist the image around a center, with the rotation falling off toward a radius."""

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
    parser = argparse.ArgumentParser(description="Swirl the image around a center point.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--angle", type=float, default=360.0, help="Rotation at the center in degrees, -1080 to 1080 (default: 360.0)")
    parser.add_argument("--radius", type=float, default=1.0, help="Swirl radius as a fraction of the half-diagonal, 0.1 to 1.5 (default: 1.0)")
    parser.add_argument("--center", type=parse_center, default=(0.5, 0.5), help="Swirl center as X,Y fractions (default: 0.5,0.5)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not -1080.0 <= args.angle <= 1080.0:
        parser.error("--angle must be between -1080 and 1080")
    if not 0.1 <= args.radius <= 1.5:
        parser.error("--radius must be between 0.1 and 1.5")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    h, w, _ = arr.shape
    cx, cy = args.center[0] * (w - 1), args.center[1] * (h - 1)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)

    dx, dy = xx - cx, yy - cy
    r = np.hypot(dx, dy)
    theta = np.arctan2(dy, dx)
    limit = args.radius * np.hypot(w / 2.0, h / 2.0)
    falloff = np.clip(1.0 - r / limit, 0.0, 1.0)
    theta_src = theta - np.radians(args.angle) * falloff ** 2

    src_x = cx + r * np.cos(theta_src)
    src_y = cy + r * np.sin(theta_src)

    result = np.zeros_like(arr)
    for c in range(3):
        result[:, :, c] = map_coordinates(arr[:, :, c], [src_y, src_x], order=1, mode="reflect")

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-swirl{ext or '.png'}"

    result_img.save(out_path)
    center = f"{args.center[0]},{args.center[1]}"
    print(f"Saved swirled image to {out_path} (angle={args.angle}, radius={args.radius}, center={center})", file=sys.stderr)


if __name__ == "__main__":
    main()
