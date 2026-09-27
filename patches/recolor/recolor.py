#!/usr/bin/env python3
"""Repaint an image's most prevalent colors with the colors you give, keeping their light and shade."""

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageColor

NEUTRAL_CHROMA = 12.0  # a*b* distance below which a color family counts as gray, black or white
HUE_WIDTH = np.radians(22)  # how far in hue a family reaches (standard deviation)
MERGE_HUE = np.radians(30)  # k-means centers closer than this in hue are one color
SHARE_WIDTH = np.radians(12)  # how sharply a pixel is shared between neighboring families


def to_lab(image: Image.Image) -> np.ndarray:
    """RGB image to float L, a, b arrays. Pillow stores a and b as signed bytes."""
    lab = np.array(image.convert("LAB"), dtype=np.int16)
    lab[:, :, 1:] = np.where(lab[:, :, 1:] > 127, lab[:, :, 1:] - 256, lab[:, :, 1:])
    return lab.astype(np.float32)


def from_lab(lab: np.ndarray) -> Image.Image:
    out = np.rint(lab)
    out[:, :, 0] = np.clip(out[:, :, 0], 0, 255)
    out[:, :, 1:] = np.clip(out[:, :, 1:], -128, 127) % 256
    # Image.merge("LAB", ...) corrupts the image on Pillow 12; build the LAB image directly.
    return Image.fromarray(out.astype(np.uint8), "LAB").convert("RGB")


def color_families(ab: np.ndarray, k: int, seed: int = 0) -> np.ndarray:
    """k-means on a*b* (chroma only, so light and shadow of one color stay together). Returns k centers."""
    rng = np.random.default_rng(seed)
    sample = ab[rng.choice(len(ab), size=min(len(ab), 20000), replace=False)]
    centers = [sample[rng.integers(len(sample))]]
    for _ in range(1, k):
        d = np.min(((sample[:, None, :] - np.array(centers)[None]) ** 2).sum(-1), axis=1)
        if d.sum() == 0:
            break
        centers.append(sample[rng.choice(len(sample), p=d / d.sum())])
    centers = np.array(centers)
    for _ in range(20):
        labels = ((sample[:, None, :] - centers[None]) ** 2).sum(-1).argmin(1)
        centers = np.array([sample[labels == i].mean(0) if np.any(labels == i) else centers[i] for i in range(len(centers))])
    return centers


def wrap(angle):
    """Wrap angles to [-pi, pi)."""
    return (angle + np.pi) % (2 * np.pi) - np.pi


def nearest_center(ab: np.ndarray, centers: np.ndarray, chunk: int = 250_000) -> np.ndarray:
    """Label each pixel with its nearest center, a chunk at a time so large photos stay in memory."""
    labels = np.empty(len(ab), dtype=np.int64)
    for start in range(0, len(ab), chunk):
        part = ab[start:start + chunk]
        labels[start:start + chunk] = ((part[:, None, :] - centers[None]) ** 2).sum(-1).argmin(1)
    return labels


def rank_families(ab: np.ndarray, centers: np.ndarray) -> list[dict]:
    """Merge k-means centers of one hue (light and saturated orange are one color), drop grays,
    and rank what is left by how many pixels it covers."""
    labels = nearest_center(ab, centers)
    counts = np.bincount(labels, minlength=len(centers))
    groups = []
    for i in np.argsort(-counts):
        chroma = float(np.hypot(*centers[i]))
        if counts[i] == 0 or chroma < NEUTRAL_CHROMA:
            continue
        hue = float(np.arctan2(centers[i][1], centers[i][0]))
        for g in groups:
            if abs(np.angle(np.exp(1j * (hue - g["hue"])))) < MERGE_HUE:
                g["members"].append(i)
                g["count"] += int(counts[i])
                break
        else:
            groups.append({"hue": hue, "members": [i], "count": int(counts[i])})
    for g in groups:
        sel = np.isin(labels, g["members"])
        g["pixels"] = sel
        mean_ab = ab[sel].mean(0)
        g["hue"] = float(np.arctan2(mean_ab[1], mean_ab[0]))
        g["chroma"] = float(np.hypot(ab[sel, 0], ab[sel, 1]).mean())
    return sorted(groups, key=lambda g: -g["count"])


def recolor(image: Image.Image, colors: list[tuple[int, int, int]], amount: float, clusters: int) -> Image.Image:
    if amount <= 0:
        return image.copy()
    src = np.array(image, dtype=np.float32)
    lab = to_lab(image)
    h, w, _ = lab.shape
    L = lab[:, :, 0].reshape(-1)
    ab = lab[:, :, 1:].reshape(-1, 2)
    chroma = np.hypot(ab[:, 0], ab[:, 1])
    hue = np.arctan2(ab[:, 1], ab[:, 0])
    families = rank_families(ab, color_families(ab, clusters))
    targets = families[:len(colors)]
    if not targets:
        return image.copy()
    # A pixel belongs to a chosen family by how close its hue is, scaled by how colorful it is, so
    # every shade of one color moves together and near-grays barely move. Its share is weighed
    # against every family found, chosen or not, so a neighboring color keeps its own pixels.
    colorful = np.clip((chroma - 4.0) / 16.0, 0.0, 1.0)

    def closeness(fh: float, width: float) -> np.ndarray:
        dh = wrap(hue - np.float32(fh))
        return np.exp(-0.5 * (dh / width) ** 2)

    everyone = np.zeros_like(hue)
    for f in families:
        everyone += closeness(f["hue"], SHARE_WIDTH)
    fam_hues = [f["hue"] for f in targets]
    member = np.array([
        colorful * closeness(fh, HUE_WIDTH) * closeness(fh, SHARE_WIDTH) / np.maximum(everyone, 1e-12)
        for fh in fam_hues
    ])
    new_l, new_c, new_h = L.copy(), chroma.copy(), hue.copy()
    for m, fam, fh, color in zip(member, targets, fam_hues, colors):
        t = to_lab(Image.new("RGB", (1, 1), color))[0, 0]
        th, tc = np.arctan2(t[2], t[1]), np.hypot(t[1], t[2])
        fl, fc = L[fam["pixels"]].mean(), fam["chroma"]
        # Keep each pixel's light and shade relative to its family; move hue and chroma to the target.
        new_l += m * (t[0] - fl)
        new_c *= 1 + m * (tc / max(fc, 1e-6) - 1)
        new_h += m * np.angle(np.exp(1j * (th - fh)))
    new_lab = np.stack([new_l, new_c * np.cos(new_h), new_c * np.sin(new_h)], 1).reshape(h, w, 3)
    out = np.array(from_lab(new_lab), dtype=np.float32)
    blend = (amount * np.clip(member.sum(0), 0, 1)).reshape(h, w, 1)
    result = src + blend * (out - src)
    return Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))


def parse_colors(value: str) -> list[tuple[int, int, int]]:
    colors = []
    for part in value.split(","):
        part = part.strip()
        try:
            colors.append(ImageColor.getrgb(part)[:3])
        except ValueError:
            raise argparse.ArgumentTypeError(f"not a color: '{part}' (use hex like #ec4899 or a name like pink)")
    if not colors:
        raise argparse.ArgumentTypeError("give at least one color")
    return colors


def main() -> None:
    parser = argparse.ArgumentParser(description="Repaint the most prevalent colors with the colors you give.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--colors", type=parse_colors, default=parse_colors("#1e3a8a,#facc15"),
                        help="Comma-separated colors, most prevalent first, (default: #1e3a8a,#facc15)")
    parser.add_argument("--amount", type=float, default=1.0, help="Strength, 0 (original) to 1 (full swap) (default: 1.0)")
    parser.add_argument("--clusters", type=int, default=6, help="Color families to find, 2 to 16 (default: 6)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")
    if not 2 <= args.clusters <= 16:
        parser.error("--clusters must be between 2 and 16")
    if len(args.colors) >= args.clusters:
        parser.error("give fewer colors than --clusters")

    img = Image.open(args.input).convert("RGB")
    result = recolor(img, args.colors, args.amount, args.clusters)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-recolor{ext or '.png'}"

    result.save(out_path)
    print(f"Saved recolored image to {out_path} (colors={len(args.colors)}, amount={args.amount}, clusters={args.clusters})", file=sys.stderr)


if __name__ == "__main__":
    main()
