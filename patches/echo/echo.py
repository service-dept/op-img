#!/usr/bin/env python3
"""Composite image on itself offset and faded N times for a ghosting/echo effect."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a ghosting/echo effect by compositing offset faded copies.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--count", type=int, default=12, help="Number of echo copies (default: 12)")
    parser.add_argument("--offset-x", type=int, default=30, help="Horizontal offset per echo (default: 30)")
    parser.add_argument("--offset-y", type=int, default=12, help="Vertical offset per echo (default: 12)")
    parser.add_argument("--decay", type=float, default=0.6, help="Opacity multiplier per step (default: 0.6)")
    parser.add_argument(
        "--blend",
        choices=["additive", "screen", "multiply"],
        default="additive",
        help="Blend mode for echo layers (default: additive)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(args.input).convert("RGB")
    w, h = img.size
    src = np.array(img, dtype=np.float64)

    def place_layer(i):
        """Return an (h, w, 3) float64 array with src at offset, scaled by decay."""
        ox = i * args.offset_x
        oy = i * args.offset_y
        opacity = args.decay ** i
        layer = np.zeros((h, w, 3), dtype=np.float64)
        src_x0 = max(0, -ox)
        src_y0 = max(0, -oy)
        dst_x0 = max(0, ox)
        dst_y0 = max(0, oy)
        cw = min(w - src_x0, w - dst_x0)
        ch = min(h - src_y0, h - dst_y0)
        if cw > 0 and ch > 0:
            layer[dst_y0:dst_y0+ch, dst_x0:dst_x0+cw] = (
                src[src_y0:src_y0+ch, src_x0:src_x0+cw] * opacity
            )
        return layer

    if args.blend == "additive":
        # Sum all layers — bright, saturated trails that glow
        acc = np.zeros((h, w, 3), dtype=np.float64)
        for i in range(args.count, -1, -1):
            acc += place_layer(i)
        result_arr = acc

    elif args.blend == "screen":
        # Screen: 1 - prod(1 - layer/255) — always brightens, softer than additive
        complement = np.ones((h, w, 3), dtype=np.float64)
        for i in range(args.count, -1, -1):
            complement *= (1.0 - place_layer(i) / 255.0)
        result_arr = (1.0 - complement) * 255.0

    elif args.blend == "multiply":
        # Multiply: prod(layer/255) — darkens, moody trails
        acc = np.ones((h, w, 3), dtype=np.float64)
        for i in range(args.count, -1, -1):
            layer = place_layer(i)
            # Only multiply where layer has content, otherwise treat as white (1.0)
            mask = layer.sum(axis=2) > 0
            normed = np.ones((h, w, 3), dtype=np.float64)
            normed[mask] = layer[mask] / 255.0
            acc *= normed
        result_arr = acc * 255.0

    result = Image.fromarray(np.clip(result_arr, 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-echo{ext or '.png'}"

    result.save(out_path)
    print(
        f"Saved echo image to {out_path} (count={args.count}, offset=({args.offset_x},{args.offset_y}), decay={args.decay})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
