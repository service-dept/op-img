#!/usr/bin/env python3
"""Invert the lightness channel of an image in LAB color space."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def invert_lightness(image: Image.Image) -> Image.Image:
    """Convert to LAB, invert L channel, convert back to RGB."""
    lab = image.convert("LAB")
    arr = np.array(lab)
    arr[:, :, 0] = 255 - arr[:, :, 0]
    # Image.merge("LAB", ...) of L-mode bands corrupts the image on Pillow 12; build the LAB image directly.
    lab_out = Image.fromarray(arr, "LAB")
    return lab_out.convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description="Invert the lightness channel of an image in LAB color space.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    args = parser.parse_args()

    img = Image.open(args.input).convert("RGB")

    result = invert_lightness(img)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-invl{ext or '.png'}"

    result.save(out_path)
    print(
        f"Saved lightness-inverted image to {out_path}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
