#!/bin/bash
# res-crush.sh — Pixelate an image by downscaling and upscaling with nearest-neighbor
#
# Usage: ./res-crush.sh <input> [output] [--size N]
#   input  - Source image (GIF, PNG, JPG, etc.)
#   output - Output PNG path (default: <input>-pixelate-N.png)
#   --size  - Downscale target in pixels (default: 64)
#
# Example:
#   ./res-crush.sh ~/Desktop/photo.png
#   ./res-crush.sh ~/Desktop/photo.png ~/output/result.png --size 64

set -euo pipefail

SIZE=64
INPUT=""
OUTPUT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --size) SIZE="$2"; shift 2 ;;
    -h|--help) sed -n '2,/^$/s/^# \{0,1\}//p' "$0"; exit 0 ;;
    -*)     echo "Unknown option: $1" >&2; exit 1 ;;
    *)
      if [ -z "$INPUT" ]; then INPUT="$1"
      elif [ -z "$OUTPUT" ]; then OUTPUT="$1"
      fi
      shift ;;
  esac
done

if [ -z "$INPUT" ]; then
  echo "Usage: $0 <input> [output] [--size N]" >&2
  exit 1
fi

if [ ! -f "$INPUT" ]; then
  echo "Error: File not found: $INPUT" >&2
  exit 1
fi

if [ -z "$OUTPUT" ]; then
  DIR=$(dirname "$INPUT")
  BASE=$(basename "$INPUT" | sed 's/\.[^.]*$//')
  OUTPUT="${DIR}/${BASE}-pixelate-${SIZE}.png"
fi

DIMS=$(magick identify -format "%wx%h" "$INPUT[0]")

magick "$INPUT" \
  -sample "${SIZE}x${SIZE}" \
  -filter point -resize "${DIMS}!" \
  "$OUTPUT"

echo "Pixelated to ${SIZE}px → $OUTPUT" >&2
