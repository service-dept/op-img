#!/usr/bin/env python3
"""Line-integral convolution along the image's edge tangents: brushed strokes that follow its contours."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates, sobel


def main() -> None:
    parser = argparse.ArgumentParser(description="Brush strokes that follow the image's contours.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--length", type=int, default=36, help="Steps traced each way along the flow, 0 to 40 (default: 36)")
    parser.add_argument("--sigma", type=float, default=6.0, help="Smoothing of the flow field (default: 6.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0 <= args.length <= 40:
        parser.error("--length must be between 0 and 40")
    if args.sigma < 0:
        parser.error("--sigma must be 0 or more")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    h, w, _ = arr.shape

    # Structure tensor: its dominant eigenvector is across edges; the tangent is 90 degrees from it.
    lum = arr @ np.array([0.299, 0.587, 0.114])
    gx, gy = sobel(lum, axis=1), sobel(lum, axis=0)
    jxx = gaussian_filter(gx * gx, args.sigma)
    jxy = gaussian_filter(gx * gy, args.sigma)
    jyy = gaussian_filter(gy * gy, args.sigma)
    angle = 0.5 * np.arctan2(2.0 * jxy, jxx - jyy) + np.pi / 2.0
    tx, ty = np.cos(angle), np.sin(angle)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    acc = arr.copy()
    count = 1
    for sign in (1.0, -1.0):
        px, py = xx.copy(), yy.copy()
        prev_x = prev_y = None
        for _ in range(args.length):
            vx = map_coordinates(tx, [py, px], order=0, mode="nearest")
            vy = map_coordinates(ty, [py, px], order=0, mode="nearest")
            if prev_x is None:
                vx, vy = sign * vx, sign * vy
            else:
                # The tangent has no preferred sign; keep stepping the way we were going.
                flip = vx * prev_x + vy * prev_y < 0
                vx, vy = np.where(flip, -vx, vx), np.where(flip, -vy, vy)
            px = np.clip(px + vx, 0, w - 1)
            py = np.clip(py + vy, 0, h - 1)
            prev_x, prev_y = vx, vy
            for c in range(3):
                acc[:, :, c] += map_coordinates(arr[:, :, c], [py, px], order=1, mode="nearest")
            count += 1

    result_img = Image.fromarray(np.clip(np.rint(acc / count), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-flow{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved flow-streak image to {out_path} (length={args.length}, sigma={args.sigma})", file=sys.stderr)


if __name__ == "__main__":
    main()
