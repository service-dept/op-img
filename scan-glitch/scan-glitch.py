#!/usr/bin/env python3
"""Apply a scan-glitch effect by shifting random horizontal slices."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def glitch(image: Image.Image, severity: int, rng: np.random.Generator) -> Image.Image:
    """Divide image into random horizontal slices and shift them."""
    pixels = np.array(image)
    h, w, _ = pixels.shape

    # Number of slices scales with severity (roughly 5-50 slices)
    n_slices = int(5 * severity)

    # Max horizontal shift scales with severity (roughly 2%-20% of width)
    max_shift = int(w * severity * 0.02)

    # Pick random split points to define slices
    splits = sorted(rng.choice(range(1, h), size=min(n_slices, h - 1), replace=False))
    splits = [0] + list(splits) + [h]

    result = pixels.copy()
    for i in range(len(splits) - 1):
        y0, y1 = splits[i], splits[i + 1]
        shift = int(rng.integers(-max_shift, max_shift + 1))
        if shift != 0:
            result[y0:y1] = np.roll(result[y0:y1], shift, axis=1)

    return Image.fromarray(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply a scan-glitch effect to an image.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument(
        "--severity",
        type=int,
        default=8,
        choices=range(1, 11),
        metavar="N",
        help="Glitch severity 1-10 (default: 8)",
    )
    parser.add_argument("--seed", type=int, default=None, help="RNG seed for reproducible output")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(args.input).convert("RGB")
    rng = np.random.default_rng(args.seed)

    result = glitch(img, args.severity, rng)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-glitch{ext or '.png'}"

    result.save(out_path)
    print(
        f"Saved glitched image to {out_path} (severity={args.severity}, seed={args.seed})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
