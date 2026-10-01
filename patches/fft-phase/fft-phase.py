#!/usr/bin/env python3
"""Blend random phase into each channel's Fourier transform, dissolving the image into texture with the same spectrum."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser(prog=os.environ.get("OP_IMG_PROG"), description="Dissolve an image by randomising its Fourier phase.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=0.35, help="Phase randomisation, 0 to 1 (default: 0.35)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (default: None)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    h, w, _ = arr.shape

    # The phase of real noise is Hermitian, so the inverse transform stays real.
    # One noise field for all channels keeps color coherent; zeroing the DC term keeps the mean.
    rng = np.random.default_rng(args.seed)
    noise = np.angle(np.fft.fft2(rng.standard_normal((h, w))))
    noise[0, 0] = 0.0

    result = np.empty_like(arr)
    for c in range(3):
        spectrum = np.fft.fft2(arr[:, :, c])
        shifted = np.abs(spectrum) * np.exp(1j * (np.angle(spectrum) + args.amount * noise))
        result[:, :, c] = np.real(np.fft.ifft2(shifted))

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-fftphase{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved phase-randomised image to {out_path} (amount={args.amount}, seed={args.seed})", file=sys.stderr)


if __name__ == "__main__":
    main()
