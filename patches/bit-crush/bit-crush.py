#!/usr/bin/env python3
"""Reduce color depth to a few levels per channel, with dithering."""

import argparse
import os
import sys

import numpy as np
from PIL import Image

QUEUE = 16    # how many past errors the dither remembers
RATIO = 16.0  # how much stronger the newest error weighs than the oldest
GAIN = 0.3    # how much of the remembered error is carried forward


def hilbert_order(w: int, h: int) -> tuple[np.ndarray, np.ndarray]:
    """Row and column of every pixel, in the order a Hilbert curve visits them."""
    n = 1
    while n < max(w, h):
        n *= 2
    t = np.arange(n * n, dtype=np.int64)
    x = np.zeros_like(t)
    y = np.zeros_like(t)
    s = 1
    while s < n:
        rx = 1 & (t // 2)
        ry = 1 & (t ^ rx)
        swap = ry == 0
        flip = swap & (rx == 1)
        x = np.where(flip, s - 1 - x, x)
        y = np.where(flip, s - 1 - y, y)
        x, y = np.where(swap, y, x), np.where(swap, x, y)
        x += s * rx
        y += s * ry
        t //= 4
        s *= 2
    keep = (x < w) & (y < h)
    return y[keep], x[keep]


def bit_crush(image: Image.Image, bits: int) -> Image.Image:
    """Posterize each channel to 2**bits levels with a light Riemersma dither: the quantizing
    error is carried along a Hilbert curve with a 16-step, fading memory. The light touch keeps
    flat, saturated blotches with speckle only in the midtones."""
    arr = np.asarray(image, dtype=np.float64)
    h, w, _ = arr.shape
    ys, xs = hilbert_order(w, h)
    order = (ys * w + xs).tolist()
    step = 255.0 / ((1 << bits) - 1)
    raw = [RATIO ** (-(QUEUE - 1 - k) / (QUEUE - 1)) for k in range(QUEUE)]
    weights = [GAIN * r / sum(raw) for r in raw]
    out = np.empty((h * w, 3))
    for c in range(3):
        values = arr[:, :, c].reshape(-1).tolist()
        result = [0.0] * len(values)
        history = [0.0] * QUEUE
        for idx in order:
            v = values[idx] + sum(e * wt for e, wt in zip(history, weights))
            q = min(255.0, max(0.0, round(v / step) * step))
            result[idx] = q
            history.pop(0)
            history.append(v - q)
        out[:, c] = result
    return Image.fromarray(out.reshape(h, w, 3).astype(np.uint8))


def main() -> None:
    parser = argparse.ArgumentParser(description="Reduce color depth by posterizing each channel.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--bits", type=int, default=1, help="Bits per channel, 1 to 8 (default: 1)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 1 <= args.bits <= 8:
        parser.error("--bits must be between 1 and 8")

    result = bit_crush(Image.open(args.input).convert("RGB"), args.bits)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-crush-{args.bits}bit{ext or '.png'}"

    result.save(out_path)
    print(f"{args.bits}-bit crush ({1 << args.bits} levels) → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
