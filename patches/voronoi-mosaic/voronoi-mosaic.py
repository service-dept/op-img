#!/usr/bin/env python3
"""Split the image into irregular Voronoi cells filled with their mean color, with optional dark leading."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
from scipy.spatial import cKDTree

LEADING = (20, 20, 20)


def main() -> None:
    parser = argparse.ArgumentParser(description="Voronoi stained-glass mosaic.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--size", type=int, default=24, help="Cell spacing in pixels, 1 to 200 (default: 24)")
    parser.add_argument("--jitter", type=float, default=1.0, help="Seed randomness, 0 (grid) to 1 (default: 1.0)")
    parser.add_argument("--edges", type=int, default=0, help="Leading width in pixels; 0 for none (default: 0)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (default: None)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 1 <= args.size <= 200:
        parser.error("--size must be between 1 and 200")
    if not 0.0 <= args.jitter <= 1.0:
        parser.error("--jitter must be between 0 and 1")
    if args.edges < 0:
        parser.error("--edges must be 0 or more")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    h, w, _ = arr.shape

    # Seeds sit on a grid of cell centers; at size 1 with no jitter every pixel is its own cell.
    rng = np.random.default_rng(args.seed)
    centers_y = np.arange((args.size - 1) / 2.0, h, args.size)
    centers_x = np.arange((args.size - 1) / 2.0, w, args.size)
    # An image smaller than one cell still gets a single seed.
    if centers_y.size == 0:
        centers_y = np.array([(h - 1) / 2.0])
    if centers_x.size == 0:
        centers_x = np.array([(w - 1) / 2.0])
    gy, gx = np.meshgrid(centers_y, centers_x, indexing="ij")
    seeds = np.column_stack([gy.ravel(), gx.ravel()])
    seeds += rng.uniform(-0.5, 0.5, seeds.shape) * args.jitter * args.size

    yy, xx = np.mgrid[0:h, 0:w]
    _, labels = cKDTree(seeds).query(np.column_stack([yy.ravel(), xx.ravel()]))
    counts = np.maximum(np.bincount(labels, minlength=len(seeds)), 1)
    means = np.stack([np.bincount(labels, weights=arr[:, :, c].ravel(), minlength=len(seeds)) / counts for c in range(3)], axis=1)
    result = means[labels].reshape(h, w, 3)

    if args.edges > 0:
        grid = labels.reshape(h, w)
        boundary = np.zeros((h, w), dtype=bool)
        boundary[1:, :] |= grid[1:, :] != grid[:-1, :]
        boundary[:, 1:] |= grid[:, 1:] != grid[:, :-1]
        if args.edges > 1:
            boundary = binary_dilation(boundary, iterations=args.edges - 1)
        result[boundary] = LEADING

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-voronoi{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved Voronoi mosaic to {out_path} (size={args.size}, jitter={args.jitter}, edges={args.edges}, seed={args.seed})", file=sys.stderr)


if __name__ == "__main__":
    main()
