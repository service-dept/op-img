#!/usr/bin/env python3
"""stipple -- Convert an image to a stipple dot pattern.

Randomly places dots weighted by image darkness. Pink dots on transparent.
"""

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw


def parse_args():
    p = argparse.ArgumentParser(description="Generate a stipple pattern from an image.")
    p.add_argument("input", help="Source image path")
    p.add_argument("output", nargs="?", default=None, help="Output image path (default: <input>-stipple.png); formats without transparency, such as JPEG, get a white background")
    p.add_argument("--dots", type=int, default=50000, help="Total dot count (default: 50000)")
    p.add_argument("--dot-size", type=float, default=1, help="Dot radius in pixels (default: 1)")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    return p.parse_args()


def save(out: Image.Image, path: str) -> None:
    """Save in the format the path names, PNG when it names none. Formats without
    transparency, such as JPEG, get a white background."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".jpg", ".jpeg", ".bmp"):
        flat = Image.new("RGB", out.size, (255, 255, 255))
        flat.paste(out, mask=out.getchannel("A"))
        out = flat
    out.save(path, Image.registered_extensions().get(ext, "PNG"))


def main():
    args = parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if args.output is None:
        base, _ = os.path.splitext(args.input)
        args.output = f"{base}-stipple.png"

    rng = np.random.default_rng(args.seed)

    img = Image.open(args.input).convert("L")
    w, h = img.size
    gray = np.array(img, dtype=np.float64)

    # Invert: darker pixels get higher probability
    density = 255.0 - gray
    total = density.sum()
    if total == 0:
        # Completely white image, nothing to draw
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        save(out, args.output)
        print(f"stipple: {os.path.basename(args.input)} -> {os.path.basename(args.output)} "
              f"(0 dots, image is blank)", file=sys.stderr)
        return

    # Flatten to 1D probability distribution
    prob = density.ravel() / total

    # Sample pixel indices weighted by probability
    indices = rng.choice(len(prob), size=args.dots, p=prob)
    ys, xs = np.divmod(indices, w)

    # Add sub-pixel jitter so dots don't all land on pixel centers
    xs = xs.astype(np.float64) + rng.uniform(-0.5, 0.5, size=args.dots)
    ys = ys.astype(np.float64) + rng.uniform(-0.5, 0.5, size=args.dots)

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(out)

    r = args.dot_size
    for x, y in zip(xs, ys):
        draw.ellipse([x - r, y - r, x + r, y + r], fill=(236, 72, 153, 255))

    save(out, args.output)
    print(f"stipple: {os.path.basename(args.input)} -> {os.path.basename(args.output)} "
          f"(dots={args.dots}, dot-size={args.dot_size})", file=sys.stderr)


if __name__ == "__main__":
    main()
