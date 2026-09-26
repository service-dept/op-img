#!/bin/bash
# isolate-threshold.sh — Extract dark pixels with transparent background
# Uses nearest-neighbor upscaling for a crisp, pixelated aesthetic
#
# Usage: ./isolate-threshold.sh <input> [output] [--scale N] [--threshold N] [--color "#hex"]
#   input      - Source image (GIF, PNG, JPG, etc.)
#   output     - Output PNG path (default: <input>-threshold.png)
#   --scale     - Upscale multiplier (default: 1)
#   --threshold - Black/white cutoff percentage (default: 50)
#   --color     - Fill color for dark pixels (default: black)
#
# Example:
#   ./isolate-threshold.sh ~/Desktop/sketch.gif
#   ./isolate-threshold.sh ~/Desktop/sketch.gif --scale 4 --color "#ff0000"

set -euo pipefail

SCALE=1
THRESHOLD=50
COLOR="#ff0000"
INPUT=""
OUTPUT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --scale)     SCALE="$2"; shift 2 ;;
    --threshold) THRESHOLD="$2"; shift 2 ;;
    --color)     COLOR="$2"; shift 2 ;;
    -h|--help) sed -n '2,/^$/s/^# \{0,1\}//p' "$0"; exit 0 ;;
    -*)          echo "Unknown option: $1" >&2; exit 1 ;;
    *)
      if [ -z "$INPUT" ]; then INPUT="$1"
      elif [ -z "$OUTPUT" ]; then OUTPUT="$1"
      fi
      shift ;;
  esac
done

if [ -z "$INPUT" ]; then
  echo "Usage: $0 <input> [output] [--scale N] [--threshold N] [--color \"#hex\"]" >&2
  exit 1
fi

if [ ! -f "$INPUT" ]; then
  echo "Error: File not found: $INPUT" >&2
  exit 1
fi

if [ -z "$OUTPUT" ]; then
  DIR=$(dirname "$INPUT")
  BASE=$(basename "$INPUT" | sed 's/\.[^.]*$//')
  OUTPUT="${DIR}/${BASE}-threshold.png"
fi

# Get original dimensions
DIMS=$(magick identify -format "%wx%h" "$INPUT")
W=$(echo "$DIMS" | cut -dx -f1)
H=$(echo "$DIMS" | cut -dx -f2)
NEW_W=$((W * SCALE))
NEW_H=$((H * SCALE))

if [ -n "$COLOR" ]; then
  # Threshold → use dark pixels as mask → fill with color
  magick "$INPUT" \
    -threshold "${THRESHOLD}%" \
    \( +clone -negate \) \
    -alpha off -compose copy-opacity -composite \
    \( +clone -fill "$COLOR" -colorize 100% \) \
    +swap -compose copy-opacity -composite \
    -filter point -resize "${NEW_W}x${NEW_H}" \
    "$OUTPUT"
else
  # Original behavior: black on transparent
  magick "$INPUT" \
    -threshold "${THRESHOLD}%" \
    \( +clone -negate \) \
    -alpha off -compose copy-opacity -composite \
    -filter point -resize "${NEW_W}x${NEW_H}" \
    "$OUTPUT"
fi

COLOR_LABEL="${COLOR:-black}"
echo "Isolate threshold ${THRESHOLD}% ${COLOR_LABEL} at ${SCALE}x (${NEW_W}x${NEW_H}) → $OUTPUT" >&2
