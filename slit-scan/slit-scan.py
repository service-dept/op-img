#!/usr/bin/env python3
"""Create a slit-scan effect by stitching columns from incrementally rotated copies of the image."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser(description="Slit-scan effect via rotated column extraction.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument(
        "--slits",
        type=int,
        default=0,
        help="Number of slits to take (0 = use image width, fewer = faster with interpolation)",
    )
    parser.add_argument(
        "--max-angle",
        type=float,
        default=180.0,
        help="Total rotation range in degrees (default: 180.0)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(args.input).convert("RGB")
    width, height = img.size

    actual_slits = args.slits if args.slits > 0 else width

    # Width of each slit band in the output
    band_width = width / actual_slits

    result = np.zeros((height, width, 3), dtype=np.uint8)

    for i in range(actual_slits):
        angle = i * args.max_angle / actual_slits
        rotated = img.rotate(angle, resample=Image.BICUBIC, expand=False)
        rotated_arr = np.array(rotated)

        # Source column from the rotated image
        src_col = int(i * width / actual_slits)
        src_col = min(src_col, width - 1)

        # Destination columns in the output
        dst_start = int(i * band_width)
        dst_end = int((i + 1) * band_width)
        dst_end = min(dst_end, width)

        # Fill the band with the source column
        for col in range(dst_start, dst_end):
            result[:, col] = rotated_arr[:, src_col]

    result_img = Image.fromarray(result)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-slitscan{ext or '.png'}"

    result_img.save(out_path)
    print(
        f"Saved slit-scan image to {out_path} (slits={actual_slits}, max_angle={args.max_angle})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
