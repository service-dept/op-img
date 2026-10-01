#!/usr/bin/env python3
"""Ordered (Bayer) or error-diffusion (Floyd-Steinberg, Atkinson) dithering to N levels per channel."""

import argparse
import os
import sys

import numpy as np
from PIL import Image

# (dy, dx, weight) for each error-diffusion kernel.
KERNELS = {
    "floyd": [(0, 1, 7 / 16), (1, -1, 3 / 16), (1, 0, 5 / 16), (1, 1, 1 / 16)],
    "atkinson": [(0, 1, 1 / 8), (0, 2, 1 / 8), (1, -1, 1 / 8), (1, 0, 1 / 8), (1, 1, 1 / 8), (2, 0, 1 / 8)],
}


def bayer(n: int) -> np.ndarray:
    m = np.array([[0, 2], [3, 1]])
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return m


def ordered(arr: np.ndarray, levels: int, size: int) -> np.ndarray:
    h, w, _ = arr.shape
    m = bayer(size)
    thresh = (m + 0.5) / (size * size) - 0.5
    tiled = np.tile(thresh, (h // size + 1, w // size + 1))[:h, :w]
    q = np.floor(arr / 255.0 * (levels - 1) + 0.5 + tiled[:, :, None])
    return np.clip(q, 0, levels - 1) * 255.0 / (levels - 1)


def diffuse(arr: np.ndarray, levels: int, kernel: list[tuple[int, int, float]]) -> np.ndarray:
    h, w, _ = arr.shape
    buf = arr.copy()
    step = 255.0 / (levels - 1)
    for y in range(h):
        for x in range(w):
            old = buf[y, x].copy()
            new = np.clip(np.round(old / step), 0, levels - 1) * step
            buf[y, x] = new
            err = old - new
            for dy, dx, weight in kernel:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w:
                    buf[ny, nx] += err * weight
    return buf


def main() -> None:
    parser = argparse.ArgumentParser(prog=os.environ.get("OP_IMG_PROG"), description="Dither to a few levels per channel.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--method", choices=["bayer", "floyd", "atkinson"], default="bayer", help="Dithering method (default: bayer)")
    parser.add_argument("--levels", type=int, default=2, help="Levels per channel, 2 to 256 (default: 2)")
    parser.add_argument("--matrix", type=int, choices=[2, 4, 8], default=8, help="Bayer matrix size (default: 8)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 2 <= args.levels <= 256:
        parser.error("--levels must be between 2 and 256")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    if args.method == "bayer":
        result = ordered(arr, args.levels, args.matrix)
    else:
        result = diffuse(arr, args.levels, KERNELS[args.method])

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-dither{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved dithered image to {out_path} (method={args.method}, levels={args.levels}, matrix={args.matrix})", file=sys.stderr)


if __name__ == "__main__":
    main()
