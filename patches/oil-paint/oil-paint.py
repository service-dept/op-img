#!/usr/bin/env python3
"""Kuwahara filter: edge-preserving smoothing into flat painterly patches with crisp edges."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def integral(padded: np.ndarray) -> np.ndarray:
    """Summed-area table with a leading row and column of zeros."""
    table = np.zeros((padded.shape[0] + 1, padded.shape[1] + 1) + padded.shape[2:])
    table[1:, 1:] = padded.cumsum(axis=0).cumsum(axis=1)
    return table


def window_mean(table: np.ndarray, h: int, w: int, r: int, oy: int, ox: int) -> np.ndarray:
    """Mean over the (r+1)x(r+1) window whose top-left corner sits at (y+oy, x+ox) for every pixel."""
    k = r + 1
    y0, x0 = r + oy, r + ox
    total = (table[y0 + k:y0 + k + h, x0 + k:x0 + k + w] - table[y0:y0 + h, x0 + k:x0 + k + w]
             - table[y0 + k:y0 + k + h, x0:x0 + w] + table[y0:y0 + h, x0:x0 + w])
    return total / (k * k)


def main() -> None:
    parser = argparse.ArgumentParser(prog=os.environ.get("OP_IMG_PROG"), description="Oil-paint look with a Kuwahara filter.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--radius", type=int, default=6, help="Quadrant size in pixels, 0 to 16 (default: 6)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0 <= args.radius <= 16:
        parser.error("--radius must be between 0 and 16")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    h, w, _ = arr.shape
    r = args.radius

    if r == 0:
        result = arr
    else:
        lum = arr @ np.array([0.299, 0.587, 0.114])
        color_table = integral(np.pad(arr, ((r, r), (r, r), (0, 0)), mode="edge"))
        lum_table = integral(np.pad(lum, r, mode="edge"))
        sq_table = integral(np.pad(lum ** 2, r, mode="edge"))

        # The four quadrants that share the pixel as a corner: pick the one with the least variance.
        quadrants = [(-r, -r), (-r, 0), (0, -r), (0, 0)]
        means = np.stack([window_mean(color_table, h, w, r, oy, ox) for oy, ox in quadrants])
        variances = np.stack([
            window_mean(sq_table, h, w, r, oy, ox) - window_mean(lum_table, h, w, r, oy, ox) ** 2
            for oy, ox in quadrants
        ])
        best = np.argmin(variances, axis=0)
        result = np.take_along_axis(means, best[None, :, :, None], axis=0)[0]

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-oilpaint{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved oil-paint image to {out_path} (radius={args.radius})", file=sys.stderr)


if __name__ == "__main__":
    main()
