#!/usr/bin/env python3
"""line-halftone -- Convert an image to a variable-width line pattern.

Pink lines on a transparent background, width varies with brightness.
"""

import argparse
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter


def parse_args():
    p = argparse.ArgumentParser(description="Generate a halftone line pattern from an image.")
    p.add_argument("input", help="Source image path")
    p.add_argument("output", nargs="?", default=None, help="Output PNG path (default: <input>-lines.png)")
    p.add_argument("--spacing", type=int, default=14, help="Pixels between line centers (default: 14)")
    p.add_argument("--min-width", type=float, default=0, help="Minimum line width (default: 0)")
    p.add_argument("--max-width", type=float, default=None, help="Maximum line width (default: spacing)")
    p.add_argument("--angle", type=float, default=0, help="Line angle in degrees, 0=horizontal 90=vertical (default: 0)")
    return p.parse_args()


def main():
    args = parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if args.output is None:
        base, _ = os.path.splitext(args.input)
        args.output = f"{base}-lines.png"

    max_width = args.max_width if args.max_width is not None else float(args.spacing)

    img = Image.open(args.input).convert("L")
    blur_radius = max(1, args.spacing // 3)
    img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    w, h = img.size
    pixels = img.load()

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(out)

    angle_rad = math.radians(args.angle)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    # Direction along the line and perpendicular (for spacing)
    # Lines run along the angle direction; spacing is perpendicular.
    # "Along" vector: (cos_a, sin_a)
    # "Perp" vector: (-sin_a, cos_a)

    diag = math.hypot(w, h)
    num_lines = int(diag / args.spacing) + 2
    # Number of sample points along each line
    num_samples = int(diag / args.spacing) + 2

    cx, cy = w / 2.0, h / 2.0

    for li in range(-num_lines, num_lines + 1):
        # Line center in image space: offset perpendicular from center
        perp_offset = li * args.spacing
        line_cx = cx + perp_offset * (-sin_a)
        line_cy = cy + perp_offset * cos_a

        # Walk along the line and draw segments with variable width
        step = args.spacing
        for si in range(-num_samples, num_samples + 1):
            along_offset = si * step
            # Current point
            px = line_cx + along_offset * cos_a
            py = line_cy + along_offset * sin_a
            # Next point
            nx = line_cx + (along_offset + step) * cos_a
            ny = line_cy + (along_offset + step) * sin_a

            # Sample brightness at midpoint of this segment
            mx, my = (px + nx) / 2.0, (py + ny) / 2.0
            xi, yi = int(round(mx)), int(round(my))
            if xi < 0 or xi >= w or yi < 0 or yi >= h:
                continue

            brightness = pixels[xi, yi]
            t = 1.0 - brightness / 255.0
            line_w = args.min_width + t * (max_width - args.min_width)

            if line_w < 0.5:
                continue

            draw.line([(px, py), (nx, ny)], fill=(236, 72, 153, 255), width=max(1, int(round(line_w))))

    out.save(args.output, "PNG")
    print(f"line-halftone: {os.path.basename(args.input)} -> {os.path.basename(args.output)} "
          f"(spacing={args.spacing}, angle={args.angle})", file=sys.stderr)


if __name__ == "__main__":
    main()
