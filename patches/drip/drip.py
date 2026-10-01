#!/usr/bin/env python3
"""Bleed bright pixels in one direction with an exponential tail, like wet paint running."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def orient(arr: np.ndarray, direction: str) -> np.ndarray:
    """Rotate the array so the drip runs down axis 0."""
    if direction == "down":
        return arr
    if direction == "up":
        return arr[::-1]
    if direction == "right":
        return arr.transpose(1, 0, 2)
    return arr.transpose(1, 0, 2)[::-1]


def unorient(arr: np.ndarray, direction: str) -> np.ndarray:
    if direction == "down":
        return arr
    if direction == "up":
        return arr[::-1]
    if direction == "right":
        return arr.transpose(1, 0, 2)
    return arr[::-1].transpose(1, 0, 2)


def main() -> None:
    parser = argparse.ArgumentParser(prog=os.environ.get("OP_IMG_PROG"), description="Drip bright pixels like running paint.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--length", type=float, default=500.0, help="Tail length in pixels; 0 leaves the image unchanged (default: 500.0)")
    parser.add_argument("--threshold", type=int, default=120, help="Brightness above which pixels drip, 0 to 255 (default: 120)")
    parser.add_argument("--direction", choices=["down", "up", "left", "right"], default="down", help="Drip direction (default: down)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if args.length < 0:
        parser.error("--length must be 0 or more")
    if not 0 <= args.threshold <= 255:
        parser.error("--threshold must be between 0 and 255")

    img = Image.open(args.input).convert("RGB")
    arr = np.array(img, dtype=np.float64)
    lum = np.array(img.convert("L"), dtype=np.float64)

    if args.length == 0:
        result = arr
    else:
        gate = np.clip((lum - args.threshold) / max(255 - args.threshold, 1), 0.0, 1.0)
        light = orient(arr * gate[:, :, None], args.direction)
        base = orient(arr, args.direction)
        decay = np.exp(-1.0 / args.length)
        tail = np.zeros(base.shape[1:])
        out = np.empty_like(base)
        for y in range(base.shape[0]):
            tail = np.maximum(light[y], tail * decay)
            out[y] = np.maximum(base[y], tail)
        result = unorient(out, args.direction)

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base_name, ext = os.path.splitext(args.input)
        out_path = f"{base_name}-drip{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved dripped image to {out_path} (length={args.length}, threshold={args.threshold}, direction={args.direction})", file=sys.stderr)


if __name__ == "__main__":
    main()
