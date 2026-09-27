#!/usr/bin/env python3
"""Blur away from a horizontal focus band and lift saturation, so the scene reads as a miniature."""

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

LEVELS = 8


def main() -> None:
    parser = argparse.ArgumentParser(description="Fake miniature with a tilt-shift blur.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--blur", type=float, default=10.0, help="Largest blur radius, 0 to 40 (default: 10.0)")
    parser.add_argument("--focus", type=float, default=0.62, help="Center of the sharp band as a fraction of height (default: 0.62)")
    parser.add_argument("--band", type=float, default=0.25, help="Height of the sharp band as a fraction of height (default: 0.25)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.blur <= 40.0:
        parser.error("--blur must be between 0 and 40")
    if not 0.0 <= args.focus <= 1.0:
        parser.error("--focus must be between 0 and 1")
    if not 0.0 <= args.band <= 1.0:
        parser.error("--band must be between 0 and 1")

    img = Image.open(args.input).convert("RGB")
    h = img.height

    if args.blur == 0:
        result_img = img
    else:
        # A stack of increasingly blurred copies; each row blends the two levels either side of its depth.
        stack = np.stack([
            np.array(img.filter(ImageFilter.GaussianBlur(args.blur * k / (LEVELS - 1))), dtype=np.float64)
            for k in range(LEVELS)
        ])
        rows = (np.arange(h) + 0.5) / h
        depth = np.clip((np.abs(rows - args.focus) - args.band / 2.0) / 0.3, 0.0, 1.0) * (LEVELS - 1)
        k0 = np.floor(depth).astype(int)
        k1 = np.minimum(k0 + 1, LEVELS - 1)
        frac = (depth - k0)[:, None, None]
        idx = np.arange(h)
        blended = stack[k0, idx] * (1.0 - frac) + stack[k1, idx] * frac
        result_img = Image.fromarray(np.clip(np.rint(blended), 0, 255).astype(np.uint8))
        strength = min(args.blur / 10.0, 1.0)
        result_img = ImageEnhance.Color(result_img).enhance(1.0 + 0.4 * strength)
        result_img = ImageEnhance.Contrast(result_img).enhance(1.0 + 0.1 * strength)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-tiltshift{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved tilt-shift image to {out_path} (blur={args.blur}, focus={args.focus}, band={args.band})", file=sys.stderr)


if __name__ == "__main__":
    main()
