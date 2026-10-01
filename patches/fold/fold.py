#!/usr/bin/env python3
"""Fold an image along an axis by mirroring or repeating one half."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def fold(image: Image.Image, axis: str, position: int, mode: str) -> Image.Image:
    """Keep the part before the fold line and place a mirrored or repeated copy after it.
    Anything the copy does not reach stays black."""
    arr = np.array(image)
    if axis == "y":
        arr = arr.transpose(1, 0, 2)
    h, w, _ = arr.shape
    position = max(0, min(position, w))
    kept = arr[:, :position]
    copy = kept[:, ::-1] if mode == "mirror" else kept
    out = np.zeros_like(arr)
    out[:, :position] = kept
    reach = min(position, w - position)
    out[:, position:position + reach] = copy[:, :reach]
    if axis == "y":
        out = out.transpose(1, 0, 2)
    return Image.fromarray(np.ascontiguousarray(out))


def main() -> None:
    parser = argparse.ArgumentParser(prog=os.environ.get("OP_IMG_PROG"), description="Fold an image along an axis by mirroring or repeating one half.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--axis", choices=["x", "y"], default="x", help="Fold axis: x folds at a vertical line, y at a horizontal one (default: x)")
    parser.add_argument("--position", type=int, default=None, help="Pixel position of the fold line (default: center)")
    parser.add_argument("--mode", choices=["mirror", "repeat"], default="mirror", help="Mirror or repeat the kept half (default: mirror)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(args.input).convert("RGB")
    w, h = img.size
    position = args.position if args.position is not None else (w // 2 if args.axis == "x" else h // 2)
    result = fold(img, args.axis, position, args.mode)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-fold{ext or '.png'}"

    result.save(out_path)
    print(f"Fold {args.axis}-axis at {position}px ({args.mode}) → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
