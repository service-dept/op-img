#!/usr/bin/env python3
"""Remap image from Cartesian to polar coordinates (or vice versa)."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates


def join_pair_values(argv: list[str], options: set[str]) -> list[str]:
    """Pass each X,Y option as --opt=VALUE. Before Python 3.14, argparse reads a value that
    starts with a minus, such as -120,-40, as another option rather than as the value."""
    out, i = [], 0
    while i < len(argv):
        if argv[i] in options and i + 1 < len(argv):
            out.append(f"{argv[i]}={argv[i + 1]}")
            i += 2
        else:
            out.append(argv[i])
            i += 1
    return out


def main() -> None:
    parser = argparse.ArgumentParser(prog=os.environ.get("OP_IMG_PROG"), description="Transform image between Cartesian and polar coordinates.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument(
        "--mode",
        choices=["to-polar", "from-polar"],
        default="to-polar",
        help="Direction of transformation (default: to-polar)",
    )
    parser.add_argument("--center", default="0.5,0.5", help="Pole position as X,Y fractions of the image (default: 0.5,0.5)")
    parser.add_argument("--rotate", type=float, default=0.0, help="Angle offset in degrees (default: 0.0)")
    parser.add_argument("--radius", type=float, default=1.0,
                        help="Outer radius as a fraction of the distance to the farthest corner (default: 1.0)")
    args = parser.parse_args(join_pair_values(sys.argv[1:], {"--center"}))
    try:
        fx, fy = (float(v) for v in args.center.split(","))
    except ValueError:
        parser.error("--center must be two numbers, X,Y (for example 0.5,0.5)")
    if args.radius <= 0:
        parser.error("--radius must be greater than 0")

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(args.input).convert("RGB")
    arr = np.array(img, dtype=np.float64)
    h, w, _ = arr.shape

    cx, cy = w * fx, h * fy
    # Distance from the pole to the farthest corner, so radius 1 covers the whole frame.
    max_radius = max(np.hypot(x - cx, y - cy) for x in (0, w) for y in (0, h)) * args.radius
    rot = np.radians(args.rotate)

    # Create output coordinate grid
    yy, xx = np.mgrid[0:h, 0:w]

    if args.mode == "to-polar":
        # Output (x, y) maps to source at:
        # angle = x * 2*pi / width
        # radius = y * max_radius / height
        angle = xx.astype(np.float64) * (2.0 * np.pi) / w + rot
        radius = yy.astype(np.float64) * max_radius / h

        src_x = cx + radius * np.cos(angle)
        src_y = cy + radius * np.sin(angle)
    else:
        # from-polar: inverse mapping
        # Source pixel at (x, y) in polar output came from angle and radius
        dx = xx.astype(np.float64) - cx
        dy = yy.astype(np.float64) - cy
        angle = (np.arctan2(dy, dx) - rot) % (2.0 * np.pi)
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
