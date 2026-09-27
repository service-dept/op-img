#!/bin/bash
# bit-crush.sh — Reduce color depth by posterizing an image
#
# Usage: ./bit-crush.sh <input> [output] [--bits N]
#   input  - Source image (GIF, PNG, JPG, etc.)
#   output - Output PNG path (default: <input>-crush-Nbit.png)
#   --bits  - Bit depth per channel (default: 3)
#
# Example:
#   ./bit-crush.sh ~/Desktop/photo.png
#   ./bit-crush.sh ~/Desktop/photo.png ~/output/result.png --bits 2

set -euo pipefail

BITS=3
INPUT=""
OUTPUT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --bits) BITS="$2"; shift 2 ;;
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
  echo "Usage: $0 <input> [output] [--bits N]" >&2
  exit 1
fi

if [ ! -f "$INPUT" ]; then
  echo "Error: File not found: $INPUT" >&2
  exit 1
fi

LEVELS=$(( 1 << BITS ))

if [ -z "$OUTPUT" ]; then
  DIR=$(dirname "$INPUT")
  BASE=$(basename "$INPUT" | sed 's/\.[^.]*$//')
  OUTPUT="${DIR}/${BASE}-crush-${BITS}bit.png"
fi

magick "$INPUT" -posterize "$LEVELS" "$OUTPUT"

echo "${BITS}-bit crush (${LEVELS} levels) → $OUTPUT" >&2
