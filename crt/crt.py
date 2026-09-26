#!/usr/bin/env python3
"""Simulate a CRT: barrel curvature, an RGB aperture-grille mask, scanlines and a slight bloom."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates


def main() -> None:
    parser = argparse.ArgumentParser(description="Show the image on a simulated CRT.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=1.0, help="Effect strength, 0 to 1 (default: 1.0)")
    parser.add_argument("--pitch", type=int, default=3, help="Width of one mask stripe in pixels (default: 3)")
    parser.add_argument("--curve", type=float, default=0.12, help="Barrel curvature at full strength (default: 0.12)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")
    if args.pitch < 1:
        parser.error("--pitch must be at least 1")
    if args.curve < 0:
        parser.error("--curve must be 0 or more")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    h, w, _ = arr.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)

    # Barrel distortion in normalised coordinates; anything pushed past the frame is black.
    nx = xx / max(w - 1, 1) * 2.0 - 1.0
    ny = yy / max(h - 1, 1) * 2.0 - 1.0
    k = args.curve * args.amount
    scale = 1.0 + k * (nx ** 2 + ny ** 2)
    sx, sy = nx * scale, ny * scale
    inside = (np.abs(sx) <= 1.0) & (np.abs(sy) <= 1.0)
    src_x = (sx + 1.0) / 2.0 * (w - 1)
    src_y = (sy + 1.0) / 2.0 * (h - 1)
    warped = np.zeros_like(arr)
    for c in range(3):
        warped[:, :, c] = map_coordinates(arr[:, :, c], [src_y, src_x], order=1, mode="constant", cval=0.0)
    warped[~inside] = 0.0

    stripe = (xx // args.pitch).astype(int) % 3
    onehot = np.eye(3)[stripe]
    mask = 1.0 - args.amount * 0.6 * (1.0 - onehot)
    scan = 1.0 - args.amount * 0.4 * (0.5 - 0.5 * np.cos(2.0 * np.pi * yy / (2.0 * args.pitch)))
    result = warped * mask * scan[:, :, None]
    result += gaussian_filter(result, (2, 2, 0)) * 0.3 * args.amount

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-crt{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved CRT image to {out_path} (amount={args.amount}, pitch={args.pitch}, curve={args.curve})", file=sys.stderr)


if __name__ == "__main__":
    main()
