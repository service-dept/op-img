#!/usr/bin/env python3
"""cross-hatch -- Convert an image to a cross-hatching pattern.

Multiple layers of lines at different angles, drawn in areas darker than
per-layer brightness thresholds. Pink on transparent.
"""

import argparse
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter


def parse_args():
    p = argparse.ArgumentParser(description="Generate a cross-hatch pattern from an image.")
    p.add_argument("input", help="Source image path")
    p.add_argument("output", nargs="?", default=None, help="Output image path (default: <input>-hatch.png); formats without transparency, such as JPEG, get a white background")
    p.add_argument("--layers", type=int, default=3, help="Number of hatch angle passes (default: 3)")
    p.add_argument("--spacing", type=int, default=12, help="Pixels between lines (default: 12)")
    p.add_argument("--thresholds", type=str, default=None,
                   help="Comma-separated brightness cutoffs 0-255, one per layer "
                        "(default: evenly spaced from 200 down to 50)")
    return p.parse_args()


def draw_hatch_layer(draw, img, w, h, angle_deg, spacing, threshold):
    """Draw lines at the given angle only where the image is darker than threshold."""
    pixels = img.load()
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    diag = math.hypot(w, h)
    num_lines = int(diag / spacing) + 2
    num_samples = int(diag / spacing) + 2
    step = spacing

    cx, cy = w / 2.0, h / 2.0

    for li in range(-num_lines, num_lines + 1):
        perp_offset = li * spacing
        line_cx = cx + perp_offset * (-sin_a)
        line_cy = cy + perp_offset * cos_a

        for si in range(-num_samples, num_samples + 1):
            along_offset = si * step
            px = line_cx + along_offset * cos_a
            py = line_cy + along_offset * sin_a
            nx = line_cx + (along_offset + step) * cos_a
            ny = line_cy + (along_offset + step) * sin_a

            mx, my = (px + nx) / 2.0, (py + ny) / 2.0
            xi, yi = int(round(mx)), int(round(my))
            if xi < 0 or xi >= w or yi < 0 or yi >= h:
                continue

            brightness = pixels[xi, yi]
            if brightness < threshold:
                draw.line([(px, py), (nx, ny)], fill=(236, 72, 153, 255), width=1)


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
        args.output = f"{base}-hatch.png"

    # Parse or generate thresholds
    if args.thresholds:
        thresholds = [int(x.strip()) for x in args.thresholds.split(",")]
        if len(thresholds) != args.layers:
            print(f"Error: expected {args.layers} thresholds, got {len(thresholds)}", file=sys.stderr)
            sys.exit(1)
    else:
        # Evenly spaced from 200 down to 50
        if args.layers == 1:
            thresholds = [128]
        else:
            thresholds = [int(200 - i * (150 / (args.layers - 1))) for i in range(args.layers)]

    # Compute angles evenly spaced across 180 degrees
    angles = [i * 180.0 / args.layers for i in range(args.layers)]

    img = Image.open(args.input).convert("L")
    blur_radius = max(1, args.spacing // 3)
    img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    w, h = img.size

    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(out)

    for angle, threshold in zip(angles, thresholds):
        draw_hatch_layer(draw, img, w, h, angle, args.spacing, threshold)

    save(out, args.output)
    print(f"cross-hatch: {os.path.basename(args.input)} -> {os.path.basename(args.output)} "
          f"(layers={args.layers}, spacing={args.spacing})", file=sys.stderr)


if __name__ == "__main__":
    main()
