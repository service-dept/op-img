#!/usr/bin/env python3
"""Draw iso-luminance lines at N levels, like a topographic map of the photo."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, gaussian_filter


def parse_color(value: str) -> tuple[int, int, int]:
    hexstr = value.lstrip("#")
    if len(hexstr) == 3:
        hexstr = "".join(ch * 2 for ch in hexstr)
    if len(hexstr) != 6:
        raise argparse.ArgumentTypeError(f"invalid color: {value}")
    try:
        return tuple(int(hexstr[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid color: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Topographic contour lines of brightness.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--levels", type=int, default=16, help="Number of brightness bands, 2 to 64 (default: 16)")
    parser.add_argument("--blur", type=float, default=2.0, help="Blur sigma before banding (default: 2.0)")
    parser.add_argument("--width", type=int, default=1, help="Line width in pixels (default: 1)")
    parser.add_argument("--color", type=parse_color, default="#ec4899", help="Line color as hex (default: #ec4899)")
    parser.add_argument("--amount", type=float, default=1.0, help="Blend from the photo (0) to lines on black (1) (default: 1.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 2 <= args.levels <= 64:
        parser.error("--levels must be between 2 and 64")
    if args.width < 1:
        parser.error("--width must be at least 1")
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")

    img = Image.open(args.input).convert("RGB")
    arr = np.array(img, dtype=np.float64)
    lum = gaussian_filter(np.array(img.convert("L"), dtype=np.float64), args.blur)
    band = np.floor(lum * args.levels / 256.0).astype(int)

    edge = np.zeros(band.shape, dtype=bool)
    edge[1:, :] |= band[1:, :] != band[:-1, :]
    edge[:, 1:] |= band[:, 1:] != band[:, :-1]
    if args.width > 1:
        edge = binary_dilation(edge, iterations=args.width - 1)

    result = arr * (1.0 - args.amount)
    result[edge] += np.array(args.color, dtype=np.float64) * args.amount
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-contour{ext or '.png'}"

    color = "#%02x%02x%02x" % args.color
    result_img.save(out_path)
    print(f"Saved contour image to {out_path} (levels={args.levels}, blur={args.blur}, width={args.width}, color={color}, amount={args.amount})", file=sys.stderr)


if __name__ == "__main__":
    main()
