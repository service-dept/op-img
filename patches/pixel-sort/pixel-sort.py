#!/usr/bin/env python3
"""Sort contiguous runs of pixels by brightness, hue, or saturation."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def pixel_brightness(rgb: np.ndarray) -> np.ndarray:
    """Perceived brightness (ITU-R BT.601)."""
    return 0.299 * rgb[:, 0] + 0.587 * rgb[:, 1] + 0.114 * rgb[:, 2]


def pixel_hue(rgb: np.ndarray) -> np.ndarray:
    """Hue component (0-360) from RGB."""
    r, g, b = rgb[:, 0] / 255.0, rgb[:, 1] / 255.0, rgb[:, 2] / 255.0
    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    delta = cmax - cmin

    hue = np.zeros(len(rgb), dtype=np.float64)
    mask_r = (cmax == r) & (delta > 0)
    mask_g = (cmax == g) & (delta > 0)
    mask_b = (cmax == b) & (delta > 0)

    hue[mask_r] = 60.0 * (((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6)
    hue[mask_g] = 60.0 * (((b[mask_g] - r[mask_g]) / delta[mask_g]) + 2)
    hue[mask_b] = 60.0 * (((r[mask_b] - g[mask_b]) / delta[mask_b]) + 4)

    return hue


def pixel_saturation(rgb: np.ndarray) -> np.ndarray:
    """HSV saturation component (0-255 scale)."""
    r, g, b = rgb[:, 0] / 255.0, rgb[:, 1] / 255.0, rgb[:, 2] / 255.0
    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    delta = cmax - cmin

    sat = np.zeros(len(rgb), dtype=np.float64)
    nonzero = cmax > 0
    sat[nonzero] = (delta[nonzero] / cmax[nonzero]) * 255.0
    return sat


METRIC_FN = {
    "brightness": pixel_brightness,
    "hue": pixel_hue,
    "saturation": pixel_saturation,
}


def sort_line(line: np.ndarray, metric_fn, threshold: float) -> np.ndarray:
    """Sort contiguous runs of pixels that meet the threshold condition."""
    values = metric_fn(line.reshape(-1, 3)).astype(np.float64)
    mask = values < threshold
    result = line.copy()

    # Find contiguous runs where mask is True
    i = 0
    n = len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            # Sort the run [i, j) by the metric
            run = result[i:j]
            run_values = metric_fn(run.reshape(-1, 3))
            order = np.argsort(run_values)
            result[i:j] = run[order]
            i = j
        else:
            i += 1

    return result


def main() -> None:
    parser = argparse.ArgumentParser(prog=os.environ.get("OP_IMG_PROG"), description="Pixel-sort an image by brightness, hue, or saturation.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument(
        "--by",
        choices=["brightness", "hue", "saturation"],
        default="brightness",
        help="Sort metric (default: brightness)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=200,
        help="Pixels below this value get sorted (0-255, default: 200)",
    )
    parser.add_argument(
        "--direction",
        choices=["row", "column"],
        default="row",
        help="Sort direction (default: row)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(args.input).convert("RGB")
    pixels = np.array(img)
    metric_fn = METRIC_FN[args.by]

    if args.direction == "column":
        pixels = np.transpose(pixels, (1, 0, 2))
        # Now shape is (W, H, 3), each "row" is a column of the original

    for i in range(pixels.shape[0]):
        pixels[i] = sort_line(pixels[i], metric_fn, args.threshold)

    if args.direction == "column":
        pixels = np.transpose(pixels, (1, 0, 2))

    result = Image.fromarray(pixels)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-psort{ext or '.png'}"

    result.save(out_path)
    print(
        f"Saved pixel-sorted image to {out_path} (by={args.by}, threshold={args.threshold}, direction={args.direction})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
