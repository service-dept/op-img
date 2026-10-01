#!/usr/bin/env python3
"""Extract a wedge from the image and mirror/rotate it N times around the center."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates


def main() -> None:
    parser = argparse.ArgumentParser(prog=os.environ.get("OP_IMG_PROG"), description="Create a kaleidoscope effect by mirroring wedges around center.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--segments", type=int, default=6, help="Number of kaleidoscope segments (default: 6)")
    parser.add_argument("--angle", type=float, default=90.0, help="Rotation offset in degrees (default: 90.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(args.input).convert("RGB")
    arr = np.array(img, dtype=np.float64)
    h, w, _ = arr.shape

    cx, cy = w / 2.0, h / 2.0

    # Create output coordinate grid
    yy, xx = np.mgrid[0:h, 0:w]

    # Convert to relative coordinates from center
    dx = xx - cx
    dy = yy - cy

    # Compute angle and radius in polar coordinates
    theta = np.arctan2(dy, dx)
    radius = np.sqrt(dx ** 2 + dy ** 2)

    # Add angle offset (convert degrees to radians)
    theta = theta - np.radians(args.angle)

    # Map theta into a single wedge
    wedge_angle = 2.0 * np.pi / args.segments

    # Normalize theta to [0, 2*pi)
    theta = theta % (2.0 * np.pi)

    # Determine which segment we're in
    segment_idx = (theta / wedge_angle).astype(int)

    # Map into single wedge
    theta_mapped = theta % wedge_angle

    # Mirror odd segments
    odd_mask = (segment_idx % 2) == 1
    theta_mapped[odd_mask] = wedge_angle - theta_mapped[odd_mask]

    # Add back the angle offset for sampling
    theta_source = theta_mapped + np.radians(args.angle)

    # Convert back to cartesian source coordinates
    src_x = cx + radius * np.cos(theta_source)
    src_y = cy + radius * np.sin(theta_source)

    # Clamp to image bounds
    src_x = np.clip(src_x, 0, w - 1)
    src_y = np.clip(src_y, 0, h - 1)

    # Sample each channel using map_coordinates
    result = np.zeros_like(arr)
    for c in range(3):
        result[:, :, c] = map_coordinates(
            arr[:, :, c],
            [src_y, src_x],
            order=1,
            mode='reflect',
        )

    result_img = Image.fromarray(result.astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-kaleido{ext or '.png'}"

    result_img.save(out_path)
    print(
        f"Saved kaleidoscope image to {out_path} (segments={args.segments}, angle={args.angle})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
