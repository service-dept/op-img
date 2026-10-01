#!/usr/bin/env python3
"""Treat pixel data as a raw audio-like signal and apply distortion effects."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser(prog=os.environ.get("OP_IMG_PROG"), description="Raw-bend image data with audio-style effects.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument(
        "--echo-strength",
        type=float,
        default=0.8,
        help="Echo mix amount 0-1 (default: 0.8)",
    )
    parser.add_argument(
        "--echo-delay",
        type=int,
        default=2000,
        help="Echo delay in samples/bytes (default: 2000)",
    )
    parser.add_argument(
        "--chorus",
        type=float,
        default=0.7,
        help="Chorus effect amount 0-1 (default: 0.7)",
    )
    parser.add_argument(
        "--bitcrush",
        type=int,
        default=0,
        help="If >0, reduce bit depth of signal (default: 0 = off)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    img = Image.open(args.input).convert("RGB")
    pixels = np.array(img)
    original_shape = pixels.shape

    # Convert to flat byte array, then to float signal in -1 to 1 range
    raw = pixels.flatten().astype(np.float64)
    signal = (raw / 127.5) - 1.0

    # 1. Echo: signal[i] += echo_strength * signal[i - echo_delay]
    if args.echo_strength > 0 and args.echo_delay > 0:
        delay = min(args.echo_delay, len(signal) - 1)
        echo = np.zeros_like(signal)
        echo[delay:] = signal[:-delay] * args.echo_strength
        signal = signal + echo

    # 2. Chorus: mix signal with a pitch-shifted copy (offset by sin wave)
    if args.chorus > 0:
        n = len(signal)
        indices = np.arange(n, dtype=np.float64)
        # Create a sinusoidal offset for chorus effect
        offset = np.sin(indices * 2.0 * np.pi / 1000.0) * 20.0
        shifted_indices = np.clip((indices + offset).astype(np.int64), 0, n - 1)
        chorus_signal = signal[shifted_indices]
        signal = signal * (1.0 - args.chorus) + chorus_signal * args.chorus

    # 3. Bitcrush: quantize to fewer levels
    if args.bitcrush > 0:
        levels = 2 ** args.bitcrush
        signal = np.round(signal * levels) / levels

    # Clip to valid range and convert back to uint8
    signal = np.clip(signal, -1.0, 1.0)
    raw_out = ((signal + 1.0) * 127.5).astype(np.uint8)

    # Reshape back to original image dimensions
    result_pixels = raw_out.reshape(original_shape)
    result = Image.fromarray(result_pixels)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-rawbend{ext or '.png'}"

    result.save(out_path)
    print(
        f"Saved raw-bent image to {out_path} (echo={args.echo_strength}, delay={args.echo_delay}, chorus={args.chorus}, bitcrush={args.bitcrush})",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
