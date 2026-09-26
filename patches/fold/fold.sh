#!/bin/bash
# fold.sh — Fold an image along an axis by mirroring or repeating one half
#
# Usage: ./fold.sh <input> [output] [--axis x|y] [--position N] [--mode mirror|repeat]
#   input     - Source image (GIF, PNG, JPG, etc.)
#   output    - Output PNG path (default: <input>-fold.png)
#   --axis     - Fold axis: x (vertical fold) or y (horizontal fold) (default: x)
#   --position - Pixel position of fold line (default: center)
#   --mode     - mirror or repeat (default: mirror)
#
# Example:
#   ./fold.sh ~/Desktop/photo.png
#   ./fold.sh ~/Desktop/photo.png --axis y --position 200 --mode repeat

set -euo pipefail

INPUT=""
OUTPUT=""
AXIS="x"
POSITION=""
MODE="mirror"

while [ $# -gt 0 ]; do
  case "$1" in
    --axis)     AXIS="$2"; shift 2 ;;
    --position) POSITION="$2"; shift 2 ;;
    --mode)     MODE="$2"; shift 2 ;;
    -h|--help) sed -n '2,/^$/s/^# \{0,1\}//p' "$0"; exit 0 ;;
    -*)         echo "Unknown option: $1" >&2; exit 1 ;;
    *)
      if [ -z "$INPUT" ]; then INPUT="$1"
      elif [ -z "$OUTPUT" ]; then OUTPUT="$1"
      fi
      shift ;;
  esac
done

if [ -z "$INPUT" ]; then
  echo "Usage: $0 <input> [output] [--axis x|y] [--position N] [--mode mirror|repeat]" >&2
  exit 1
fi

if [ ! -f "$INPUT" ]; then
  echo "Error: File not found: $INPUT" >&2
  exit 1
fi

DIMS=$(magick identify -format "%wx%h" "$INPUT[0]")
W=$(echo "$DIMS" | cut -dx -f1)
H=$(echo "$DIMS" | cut -dx -f2)

if [ "$AXIS" = "x" ]; then
  POSITION="${POSITION:-$(( W / 2 ))}"
elif [ "$AXIS" = "y" ]; then
  POSITION="${POSITION:-$(( H / 2 ))}"
else
  echo "Error: --axis must be x or y" >&2
  exit 1
fi

if [ -z "$OUTPUT" ]; then
  DIR=$(dirname "$INPUT")
  BASE=$(basename "$INPUT" | sed 's/\.[^.]*$//')
  OUTPUT="${DIR}/${BASE}-fold.png"
fi

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

if [ "$AXIS" = "x" ]; then
  # Vertical fold: crop left half, flip/tile to fill right
  magick "$INPUT" -crop "${POSITION}x${H}+0+0" +repage "${TMPDIR}/left.png"

  if [ "$MODE" = "mirror" ]; then
    magick "${TMPDIR}/left.png" -flop "${TMPDIR}/right.png"
  else
    magick "${TMPDIR}/left.png" "${TMPDIR}/right.png"
  fi

  # Composite: left half at origin, right half at fold position
  magick -size "${W}x${H}" xc:black \
    "${TMPDIR}/left.png" -geometry "+0+0" -composite \
    "${TMPDIR}/right.png" -geometry "+${POSITION}+0" -composite \
    "$OUTPUT"
else
  # Horizontal fold: crop top half, flip/tile to fill bottom
  magick "$INPUT" -crop "${W}x${POSITION}+0+0" +repage "${TMPDIR}/top.png"

  if [ "$MODE" = "mirror" ]; then
    magick "${TMPDIR}/top.png" -flip "${TMPDIR}/bottom.png"
  else
    magick "${TMPDIR}/top.png" "${TMPDIR}/bottom.png"
  fi

  magick -size "${W}x${H}" xc:black \
    "${TMPDIR}/top.png" -geometry "+0+0" -composite \
    "${TMPDIR}/bottom.png" -geometry "+0+${POSITION}" -composite \
    "$OUTPUT"
fi

echo "Fold ${AXIS}-axis at ${POSITION}px (${MODE}) → $OUTPUT" >&2
