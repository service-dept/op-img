#!/usr/bin/env python3
"""Remap image from Cartesian to polar coordinates (or vice versa)."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates


def main() -> None:
    parser = argparse.ArgumentParser(description="Transform image between Cartesian and polar coordinates.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument(
        "--mode",
        choices=["to-polar", "from-polar"],
        default="to-polar",
        help="Direction of transformation (default: to-polar)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(args.input).convert("RGB")
    arr = np.array(img, dtype=np.float64)
    h, w, _ = arr.shape

    cx, cy = w / 2.0, h / 2.0
    max_radius = np.sqrt(cx ** 2 + cy ** 2)

    # Create output coordinate grid
    yy, xx = np.mgrid[0:h, 0:w]

    if args.mode == "to-polar":
        # Output (x, y) maps to source at:
        # angle = x * 2*pi / width
        # radius = y * max_radius / height
        angle = xx.astype(np.float64) * (2.0 * np.pi) / w
        radius = yy.astype(np.float64) * max_radius / h

        src_x = cx + radius * np.cos(angle)
        src_y = cy + radius * np.sin(angle)
    else:
        # from-polar: inverse mapping
        # Source pixel at (x, y) in polar output came from angle and radius
        dx = xx.astype(np.float64) - cx
        dy = yy.astype(np.float64) - cy
        angle = np.arctan2(dy, dx) % (2.0 * np.pi)
        radius = np.sqrt(dx ** 2 + dy ** 2)

        src_x = angle * w / (2.0 * np.pi)
        src_y = radius * h / max_radius

    # Clamp to image bounds
    src_x = np.clip(src_x, 0, w - 1)
    src_y = np.clip(src_y, 0, h - 1)

    # Sample each channel
    result = np.zeros_like(arr)
    for c in range(3):
        result[:, :, c] = map_coordinates(
            arr[:, :, c],
            [src_y, src_x],
            order=1,
            mode='constant',
            cval=0.0,
        )

    result_img = Image.fromarray(result.astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-polar{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved polar image to {out_path} (mode={args.mode})", file=sys.stderr)


if __name__ == "__main__":
    main()
