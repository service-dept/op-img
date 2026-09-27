#!/usr/bin/env python3
"""Chop image into NxN grid and randomly permute tiles."""

import argparse
import os
import sys
from typing import Optional

import numpy as np
from PIL import Image


def tile_shuffle(image: Image.Image, grid: int, seed: Optional[int]) -> Image.Image:
    """Divide image into grid x grid tiles and reassemble in shuffled order, keeping the image's size."""
    arr = np.array(image)
    h, w, c = arr.shape
    # Spread the tile edges over the whole image, so tiles differ by at most a pixel when the grid
    # does not divide it. A tile moved into a slot of a different size is resized to fit.
    ys = np.linspace(0, h, grid + 1).round().astype(int)
    xs = np.linspace(0, w, grid + 1).round().astype(int)
    slots = [(ys[r], ys[r + 1], xs[col], xs[col + 1]) for r in range(grid) for col in range(grid)]
    tiles = [arr[y0:y1, x0:x1] for y0, y1, x0, x1 in slots]

    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(tiles))

    out = np.zeros_like(arr)
    for (y0, y1, x0, x1), src_idx in zip(slots, perm):
        tile = tiles[src_idx]
        if tile.shape[:2] != (y1 - y0, x1 - x0):
            tile = np.array(Image.fromarray(tile).resize((x1 - x0, y1 - y0), Image.NEAREST))
        out[y0:y1, x0:x1] = tile

    return Image.fromarray(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Shuffle tiles of an image in a grid.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument(
        "--grid",
        type=int,
        default=8,
        help="Grid size NxN (default: 8)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="RNG seed for reproducibility (default: None)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(args.input).convert("RGB")

    result = tile_shuffle(img, args.grid, args.seed)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-shuffle{ext or '.png'}"

    result.save(out_path)
    print(
        f"Saved tile-shuffled image to {out_path} (grid={args.grid}, seed={args.seed})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
