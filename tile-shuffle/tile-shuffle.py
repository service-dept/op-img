#!/usr/bin/env python3
"""Chop image into NxN grid and randomly permute tiles."""

import argparse
import os
import sys
from typing import Optional

import numpy as np
from PIL import Image


def tile_shuffle(image: Image.Image, grid: int, seed: Optional[int]) -> Image.Image:
    """Divide image into grid x grid tiles and reassemble in shuffled order."""
    arr = np.array(image)
    h, w, c = arr.shape
    tile_h = h // grid
    tile_w = w // grid

    # Crop to exact tile grid dimensions
    cropped = arr[:tile_h * grid, :tile_w * grid]

    # Extract tiles
    tiles = []
    for row in range(grid):
        for col in range(grid):
            tile = cropped[row * tile_h:(row + 1) * tile_h, col * tile_w:(col + 1) * tile_w]
            tiles.append(tile)

    # Shuffle tiles
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(tiles))

    # Reassemble
    out = np.zeros_like(cropped)
    for idx, src_idx in enumerate(perm):
        row = idx // grid
        col = idx % grid
        out[row * tile_h:(row + 1) * tile_h, col * tile_w:(col + 1) * tile_w] = tiles[src_idx]

    return Image.fromarray(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Shuffle tiles of an image in a grid.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument(
        "--grid",
        type=int,
        default=4,
        help="Grid size NxN (default: 4)",
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
