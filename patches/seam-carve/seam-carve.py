#!/usr/bin/env python3
"""Content-aware seam removal using dynamic programming for energy minimization."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def compute_energy_gradient(img: np.ndarray) -> np.ndarray:
    """Compute energy map using absolute differences between neighboring pixels."""
    h, w, c = img.shape
    img_f = img.astype(np.float64)

    # Horizontal differences: |img[y,x] - img[y,x+1]|
    horiz = np.zeros((h, w), dtype=np.float64)
    horiz[:, :-1] = np.sum(np.abs(img_f[:, :-1] - img_f[:, 1:]), axis=2)
    horiz[:, -1] = horiz[:, -2]  # replicate last column

    # Vertical differences: |img[y,x] - img[y+1,x]|
    vert = np.zeros((h, w), dtype=np.float64)
    vert[:-1, :] = np.sum(np.abs(img_f[:-1, :] - img_f[1:, :]), axis=2)
    vert[-1, :] = vert[-2, :]  # replicate last row

    return horiz + vert


def compute_energy_sobel(img: np.ndarray) -> np.ndarray:
    """Compute energy map using Sobel filter magnitude."""
    gray = np.sum(img.astype(np.float64) * [0.299, 0.587, 0.114], axis=2)

    # Sobel kernels applied via numpy operations
    # Horizontal gradient
    gx = np.zeros_like(gray)
    gx[:, 1:-1] = -gray[:, :-2] + gray[:, 2:]
    gx[:, 0] = gray[:, 1] - gray[:, 0]
    gx[:, -1] = gray[:, -1] - gray[:, -2]

    # Vertical gradient
    gy = np.zeros_like(gray)
    gy[1:-1, :] = -gray[:-2, :] + gray[2:, :]
    gy[0, :] = gray[1, :] - gray[0, :]
    gy[-1, :] = gray[-1, :] - gray[-2, :]

    return np.sqrt(gx ** 2 + gy ** 2)


def find_seam(energy: np.ndarray) -> np.ndarray:
    """Find lowest-energy vertical seam using dynamic programming."""
    h, w = energy.shape
    M = energy.copy()

    # Build cumulative energy matrix
    for r in range(1, h):
        # Left neighbor (shifted right): pad left with inf
        left = np.empty(w, dtype=np.float64)
        left[0] = np.inf
        left[1:] = M[r - 1, :-1]

        # Right neighbor (shifted left): pad right with inf
        right = np.empty(w, dtype=np.float64)
        right[-1] = np.inf
        right[:-1] = M[r - 1, 1:]

        # Center
        center = M[r - 1]

        M[r] += np.minimum(np.minimum(left, center), right)

    # Backtrack from minimum of bottom row
    seam = np.zeros(h, dtype=np.int64)
    seam[-1] = np.argmin(M[-1])

    for r in range(h - 2, -1, -1):
        j = seam[r + 1]
        lo = max(0, j - 1)
        hi = min(w, j + 2)
        seam[r] = lo + np.argmin(M[r, lo:hi])

    return seam


def remove_seam(img: np.ndarray, seam: np.ndarray) -> np.ndarray:
    """Remove a vertical seam from the image, reducing width by 1."""
    h, w, c = img.shape
    result = np.zeros((h, w - 1, c), dtype=img.dtype)

    for r in range(h):
        j = seam[r]
        result[r, :j] = img[r, :j]
        result[r, j:] = img[r, j + 1:]

    return result


def main() -> None:
    parser = argparse.ArgumentParser(prog=os.environ.get("OP_IMG_PROG"), description="Content-aware seam carving to reduce image width.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument(
        "--percent",
        type=int,
        default=35,
        help="Percentage of width to remove, 1-50 (default: 35)",
    )
    parser.add_argument(
        "--energy",
        choices=["gradient", "sobel"],
        default="sobel",
        help="Energy function (default: sobel)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Clamp percent to valid range
    percent = max(1, min(50, args.percent))

    img = Image.open(args.input).convert("RGB")
    pixels = np.array(img)
    height = pixels.shape[0]
    original_width = pixels.shape[1]

    energy_fn = compute_energy_gradient if args.energy == "gradient" else compute_energy_sobel

    seams_to_remove = int(original_width * percent / 100)
    seams_to_remove = max(1, min(seams_to_remove, original_width - 1))

    for _ in range(seams_to_remove):
        energy = energy_fn(pixels)
        seam = find_seam(energy)
        pixels = remove_seam(pixels, seam)

    result_width = pixels.shape[1]
    result = Image.fromarray(pixels)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-seamcarve{ext or '.png'}"

    result.save(out_path)
    print(
        f"Saved seam-carved image to {out_path} ({seams_to_remove} seams removed, {result_width}x{height})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
