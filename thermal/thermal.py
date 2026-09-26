#!/usr/bin/env python3
"""Map brightness to false-color thermal palette (black-blue-magenta-red-yellow-white)."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def build_thermal_lut() -> np.ndarray:
    """Build a 256-entry RGB lookup table for thermal colormap."""
    anchors = [
        (0, (0, 0, 0)),        # black
        (64, (0, 0, 200)),     # blue
        (128, (200, 0, 200)),  # magenta
        (170, (255, 0, 0)),    # red
        (210, (255, 255, 0)),  # yellow
        (255, (255, 255, 255)),  # white
    ]

    lut = np.zeros((256, 3), dtype=np.uint8)

    for idx in range(len(anchors) - 1):
        pos_start, color_start = anchors[idx]
        pos_end, color_end = anchors[idx + 1]
        span = pos_end - pos_start
        for i in range(span):
            t = i / span
            r = int(color_start[0] + t * (color_end[0] - color_start[0]))
            g = int(color_start[1] + t * (color_end[1] - color_start[1]))
            b = int(color_start[2] + t * (color_end[2] - color_start[2]))
            lut[pos_start + i] = [r, g, b]

    # Fill the last anchor point
    lut[255] = list(anchors[-1][1])

    return lut


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply false-color thermal palette based on brightness.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(args.input).convert("RGB")
    gray = np.array(img.convert("L"))

    lut = build_thermal_lut()

    # Vectorized LUT application
    thermal = lut[gray]

    result = Image.fromarray(thermal.astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-thermal{ext or '.png'}"

    result.save(out_path)
    print(f"Saved thermal image to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
