#!/usr/bin/env python3
"""Rearrange RGB channels of an image."""

import argparse
import os
import sys

import numpy as np
from PIL import Image

CHANNEL_MAP = {"R": 0, "G": 1, "B": 2}


def channel_swap(image: Image.Image, mapping: str) -> Image.Image:
    """Rearrange RGB channels according to a comma-separated mapping string."""
    channels = [ch.strip().upper() for ch in mapping.split(",")]
    if len(channels) != 3 or any(ch not in CHANNEL_MAP for ch in channels):
        raise ValueError(f"Invalid channel map '{mapping}'. Use comma-separated R,G,B values (e.g. B,G,R)")
    indices = [CHANNEL_MAP[ch] for ch in channels]
    arr = np.array(image)
    result = arr[:, :, indices]
    return Image.fromarray(result)


def main() -> None:
    parser = argparse.ArgumentParser(prog=os.environ.get("OP_IMG_PROG"), description="Rearrange RGB channels of an image.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument(
        "--map",
        default="B,G,R",
        help="Channel mapping as comma-separated R,G,B values (default: B,G,R)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(args.input).convert("RGB")

    result = channel_swap(img, args.map)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-chswap{ext or '.png'}"

    result.save(out_path)
    print(
        f"Saved channel-swapped image to {out_path} (map={args.map})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
