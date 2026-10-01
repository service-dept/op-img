#!/usr/bin/env python3
"""Map every pixel in an image to the nearest color in a given palette."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def extract_palette_kmeans(image: Image.Image, n_colors: int) -> np.ndarray:
    """Extract dominant colors from an image using simple k-means."""
    pixels = np.array(image.convert("RGB")).reshape(-1, 3).astype(np.float64)

    # Subsample if image is large
    if len(pixels) > 50000:
        indices = np.random.choice(len(pixels), 50000, replace=False)
        samples = pixels[indices]
    else:
        samples = pixels

    # Initialize centroids with k-means++
    centroids = [samples[np.random.randint(len(samples))]]
    for _ in range(1, n_colors):
        dists = np.min(
            [np.sum((samples - c) ** 2, axis=1) for c in centroids], axis=0
        )
        probs = dists / dists.sum()
        centroids.append(samples[np.random.choice(len(samples), p=probs)])
    centroids = np.array(centroids, dtype=np.float64)

    for _ in range(50):
        dists = np.linalg.norm(samples[:, None] - centroids[None, :], axis=2)
        labels = np.argmin(dists, axis=1)
        new_centroids = np.array(
            [
                samples[labels == k].mean(axis=0) if np.any(labels == k) else centroids[k]
                for k in range(n_colors)
            ]
        )
        if np.allclose(centroids, new_centroids, atol=0.5):
            break
        centroids = new_centroids

    return np.clip(np.round(centroids), 0, 255).astype(np.uint8)


def snap_to_palette(image: Image.Image, palette: np.ndarray) -> Image.Image:
    """Replace every pixel with the nearest palette color (Euclidean RGB)."""
    pixels = np.array(image.convert("RGB")).astype(np.float64)
    h, w, _ = pixels.shape
    flat = pixels.reshape(-1, 3)

    dists = np.linalg.norm(flat[:, None] - palette[None, :].astype(np.float64), axis=2)
    nearest = np.argmin(dists, axis=1)
    result = palette[nearest].reshape(h, w, 3)

    return Image.fromarray(result)


def main() -> None:
    parser = argparse.ArgumentParser(prog=os.environ.get("OP_IMG_PROG"), description="Snap image pixels to nearest palette color.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument(
        "--palette",
        help='Comma-separated hex colors, e.g. "#ff0000,#00ff00,#0000ff"',
    )
    parser.add_argument("--from-image", dest="from_image", help="Extract palette from this image")
    parser.add_argument(
        "--colors",
        type=int,
        default=6,
        help="Number of colors to extract when using --from-image (default: 6)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if not args.palette and not args.from_image:
        parser.error("Provide --palette or --from-image")

    img = Image.open(args.input).convert("RGB")

    if args.palette:
        colors = [hex_to_rgb(c.strip()) for c in args.palette.split(",")]
        palette = np.array(colors, dtype=np.uint8)
    else:
        ref = Image.open(args.from_image).convert("RGB")
        palette = extract_palette_kmeans(ref, args.colors)

    result = snap_to_palette(img, palette)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-palette{ext or '.png'}"

    result.save(out_path)
    print(f"Saved palette-mapped image to {out_path} ({len(palette)} colors)", file=sys.stderr)


if __name__ == "__main__":
    main()
