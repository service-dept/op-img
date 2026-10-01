#!/usr/bin/env python3
"""dot-halftone -- Convert an image to a halftone dot pattern.

Pink dots on a transparent background, sized by local brightness.
"""

import argparse
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter


def parse_args():
    p = argparse.ArgumentParser(description="Generate a halftone dot pattern from an image.")
    p.add_argument("input", help="Source image path")
    p.add_argument("output", nargs="?", default=None, help="Output image path (default: <input>-halftone.png); formats without transparency, such as JPEG, get a white background")
    p.add_argument("--spacing", type=int, default=8, help="Pixels between dot centers (default: 8)")
    p.add_argument("--min-dot", type=float, default=0, help="Minimum dot radius (default: 0)")
    p.add_argument("--max-dot", type=float, default=None, help="Maximum dot radius (default: spacing/2)")
    p.add_argument("--angle", type=float, default=0, help="Grid rotation in degrees (default: 0)")
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
        args.output = f"{base}-halftone.png"

    max_dot = args.max_dot if args.max_dot is not None else args.spacing / 2.0

    img = Image.open(args.input).convert("L")
    # Slight blur to smooth sampling
    blur_radius = max(1, args.spacing // 4)
    img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    w, h = img.size
    pixels = img.load()

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(out)

    angle_rad = math.radians(args.angle)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    # Compute grid bounds: we need to cover the whole image even when rotated.
    # Project corners into rotated space to find the range of grid indices.
    diag = math.hypot(w, h)
    grid_min = -int(diag / args.spacing) - 1
    grid_max = int(diag / args.spacing) + 1

    cx, cy = w / 2.0, h / 2.0

    for gi in range(grid_min, grid_max + 1):
        for gj in range(grid_min, grid_max + 1):
            # Grid point in rotated space, then rotate to image space
            gx = gi * args.spacing
            gy = gj * args.spacing
            ix = cos_a * gx - sin_a * gy + cx
            iy = sin_a * gx + cos_a * gy + cy

            xi, yi = int(round(ix)), int(round(iy))
            if xi < 0 or xi >= w or yi < 0 or yi >= h:
                continue

            brightness = pixels[xi, yi]  # 0=black, 255=white
            # Map brightness to dot radius: black -> max_dot, white -> min_dot
            t = 1.0 - brightness / 255.0
            radius = args.min_dot + t * (max_dot - args.min_dot)

            if radius <= 0:
                continue

            draw.ellipse(
                [ix - radius, iy - radius, ix + radius, iy + radius],
                fill=(236, 72, 153, 255),
            )

    save(out, args.output)
    print(f"dot-halftone: {os.path.basename(args.input)} -> {os.path.basename(args.output)} "
          f"(spacing={args.spacing}, angle={args.angle})", file=sys.stderr)


if __name__ == "__main__":
    main()
