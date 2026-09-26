#!/usr/bin/env python3
"""Repaint an image's most prevalent colours with the colours you give, keeping their light and shade."""

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageColor

NEUTRAL_CHROMA = 12.0  # a*b* distance below which a colour family counts as grey, black or white
HUE_WIDTH = np.radians(22)  # how far in hue a family reaches (standard deviation)
MERGE_HUE = np.radians(30)  # k-means centres closer than this in hue are one colour


def to_lab(image: Image.Image) -> np.ndarray:
    """RGB image to float L, a, b arrays. Pillow stores a and b as signed bytes."""
    lab = np.array(image.convert("LAB"), dtype=np.int16)
    lab[:, :, 1:] = np.where(lab[:, :, 1:] > 127, lab[:, :, 1:] - 256, lab[:, :, 1:])
    return lab.astype(np.float64)


def from_lab(lab: np.ndarray) -> Image.Image:
    out = np.rint(lab)
    out[:, :, 0] = np.clip(out[:, :, 0], 0, 255)
    out[:, :, 1:] = np.clip(out[:, :, 1:], -128, 127) % 256
    # Image.merge("LAB", ...) corrupts the image on Pillow 12; build the LAB image directly.
    return Image.fromarray(out.astype(np.uint8), "LAB").convert("RGB")


def colour_families(ab: np.ndarray, k: int, seed: int = 0) -> np.ndarray:
    """k-means on a*b* (chroma only, so light and shadow of one colour stay together). Returns k centres."""
    rng = np.random.default_rng(seed)
    sample = ab[rng.choice(len(ab), size=min(len(ab), 20000), replace=False)]
    centres = [sample[rng.integers(len(sample))]]
    for _ in range(1, k):
        d = np.min(((sample[:, None, :] - np.array(centres)[None]) ** 2).sum(-1), axis=1)
        if d.sum() == 0:
            break
        centres.append(sample[rng.choice(len(sample), p=d / d.sum())])
    centres = np.array(centres)
    for _ in range(20):
        labels = ((sample[:, None, :] - centres[None]) ** 2).sum(-1).argmin(1)
        centres = np.array([sample[labels == i].mean(0) if np.any(labels == i) else centres[i] for i in range(len(centres))])
    return centres


def rank_families(ab: np.ndarray, centres: np.ndarray) -> list[dict]:
    """Merge k-means centres of one hue (light and saturated orange are one colour), drop greys,
    and rank what is left by how many pixels it covers."""
    labels = ((ab[:, None, :] - centres[None]) ** 2).sum(-1).argmin(1)
    counts = np.bincount(labels, minlength=len(centres))
    groups = []
    for i in np.argsort(-counts):
        chroma = float(np.hypot(*centres[i]))
        if counts[i] == 0 or chroma < NEUTRAL_CHROMA:
            continue
        hue = float(np.arctan2(centres[i][1], centres[i][0]))
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


def recolor(image: Image.Image, colours: list[tuple[int, int, int]], amount: float, clusters: int) -> Image.Image:
    if amount <= 0:
        return image.copy()
    src = np.array(image, dtype=np.float64)
    lab = to_lab(image)
    h, w, _ = lab.shape
    L = lab[:, :, 0].reshape(-1)
    ab = lab[:, :, 1:].reshape(-1, 2)
    chroma = np.hypot(ab[:, 0], ab[:, 1])
    hue = np.arctan2(ab[:, 1], ab[:, 0])
    families = rank_families(ab, colour_families(ab, clusters))
    targets = families[:len(colours)]
    if not targets:
        return image.copy()
    # A pixel belongs to a family by how close its hue is, scaled by how colourful it is, so every
    # shade of one colour moves together and near-greys barely move.
    colourful = np.clip((chroma - 4.0) / 16.0, 0.0, 1.0)
    fam_hues = [f["hue"] for f in targets]
    member = []
    for fh in fam_hues:
        dh = np.angle(np.exp(1j * (hue - fh)))
        member.append(np.exp(-0.5 * (dh / HUE_WIDTH) ** 2) * colourful)
    member = np.array(member)
    total = member.sum(0)
    member = np.where(total > 1, member / np.maximum(total, 1e-9), member)
    new_l, new_c, new_h = L.copy(), chroma.copy(), hue.copy()
    for m, fam, fh, colour in zip(member, targets, fam_hues, colours):
        t = to_lab(Image.new("RGB", (1, 1), colour))[0, 0]
        th, tc = np.arctan2(t[2], t[1]), np.hypot(t[1], t[2])
        fl, fc = L[fam["pixels"]].mean(), fam["chroma"]
        # Keep each pixel's light and shade relative to its family; move hue and chroma to the target.
        new_l += m * (t[0] - fl)
        new_c *= 1 + m * (tc / max(fc, 1e-6) - 1)
        new_h += m * np.angle(np.exp(1j * (th - fh)))
    new_lab = np.stack([new_l, new_c * np.cos(new_h), new_c * np.sin(new_h)], 1).reshape(h, w, 3)
    out = np.array(from_lab(new_lab), dtype=np.float64)
    blend = (amount * np.clip(member.sum(0), 0, 1)).reshape(h, w, 1)
    result = src + blend * (out - src)
    return Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))


def parse_colours(value: str) -> list[tuple[int, int, int]]:
    colours = []
    for part in value.split(","):
        part = part.strip()
        try:
            colours.append(ImageColor.getrgb(part)[:3])
        except ValueError:
            raise argparse.ArgumentTypeError(f"not a colour: '{part}' (use hex like #ec4899 or a name like pink)")
    if not colours:
        raise argparse.ArgumentTypeError("give at least one colour")
    return colours


def main() -> None:
    parser = argparse.ArgumentParser(description="Repaint the most prevalent colours with the colours you give.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--colors", type=parse_colours, default=parse_colours("#ec4899"),
                        help="Comma-separated colours, most prevalent first, e.g. '#ec4899,#1e3a8a' (default: #ec4899)")
    parser.add_argument("--amount", type=float, default=1.0, help="Strength, 0 (original) to 1 (full swap) (default: 1.0)")
    parser.add_argument("--clusters", type=int, default=6, help="Colour families to find, 2 to 16 (default: 6)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")
    if not 2 <= args.clusters <= 16:
        parser.error("--clusters must be between 2 and 16")
    if len(args.colors) >= args.clusters:
        parser.error("give fewer colours than --clusters")

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
