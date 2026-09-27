#!/usr/bin/env python3
"""Keep the pixels brighter than a threshold as a flat color on a transparent background."""

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageColor


def isolate_threshold(image: Image.Image, threshold: float, color: tuple[int, int, int], scale: int) -> Image.Image:
    """Pixels whose Rec. 709 luma is above threshold% become color; the rest become transparent.
    Nearest-neighbor upscaling keeps the edges crisp."""
    arr = np.asarray(image, dtype=np.float64)
    luma = arr @ np.array([0.2126, 0.7152, 0.0722])
    keep = luma > threshold * 255.0 / 100.0
    out = np.zeros(arr.shape[:2] + (4,), dtype=np.uint8)
    out[keep] = (*color, 255)
    result = Image.fromarray(out, "RGBA")
    if scale != 1:
        result = result.resize((image.width * scale, image.height * scale), Image.NEAREST)
    return result


def parse_color(value: str) -> tuple[int, int, int]:
    try:
        return ImageColor.getrgb(value)[:3]
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a color: '{value}' (use hex like #ff0000 or a name like red)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Keep the bright pixels as a flat color on a transparent background.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path; formats without transparency, such as JPEG, get a white background")
    parser.add_argument("--threshold", type=float, default=50.0, help="Brightness cutoff as a percentage, 0 to 100 (default: 50)")
    parser.add_argument("--color", type=parse_color, default=parse_color("#ff0000"), help="Fill color for the kept pixels (default: #ff0000)")
    parser.add_argument("--scale", type=int, default=1, help="Upscale multiplier, nearest-neighbor (default: 1)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0 <= args.threshold <= 100:
        parser.error("--threshold must be between 0 and 100")
    if args.scale < 1:
        parser.error("--scale must be at least 1")

    img = Image.open(args.input).convert("RGB")
    result = isolate_threshold(img, args.threshold, args.color, args.scale)

    if args.output:
        out_path = args.output
    else:
        base, _ = os.path.splitext(args.input)
        out_path = f"{base}-threshold.png"

    if os.path.splitext(out_path)[1].lower() in (".jpg", ".jpeg", ".bmp"):
        # These formats have no transparency: flatten onto white, as ImageMagick did.
        flat = Image.new("RGB", result.size, (255, 255, 255))
        flat.paste(result, mask=result.getchannel("A"))
        result = flat
    result.save(out_path)
    print(f"Isolate threshold {args.threshold:g}% at {args.scale}x ({result.width}x{result.height}) → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
