#!/bin/bash
# channel-offset.sh — Shift RGB channels by independent pixel offsets
#
# Usage: ./channel-offset.sh <input> [output] [--r X,Y] [--g X,Y] [--b X,Y]
#   input  - Source image (GIF, PNG, JPG, etc.)
#   output - Output PNG path (default: <input>-offset.png)
#   --r     - Red channel offset in pixels (default: 140,50)
#   --g     - Green channel offset in pixels (default: -20,40)
#   --b     - Blue channel offset in pixels (default: -120,-40)
#
# Example:
#   ./channel-offset.sh ~/Desktop/photo.png --r 10,0 --b -10,0
#   ./channel-offset.sh ~/Desktop/photo.png ~/output/result.png --g 0,5

set -euo pipefail

INPUT=""
OUTPUT=""
R_OFF="140,50"
G_OFF="-20,40"
B_OFF="-120,-40"

while [ $# -gt 0 ]; do
  case "$1" in
    --r) R_OFF="$2"; shift 2 ;;
    --g) G_OFF="$2"; shift 2 ;;
    --b) B_OFF="$2"; shift 2 ;;
    -h|--help) sed -n '2,/^$/s/^# \{0,1\}//p' "$0"; exit 0 ;;
    -*)  echo "Unknown option: $1" >&2; exit 1 ;;
    *)
      if [ -z "$INPUT" ]; then INPUT="$1"
      elif [ -z "$OUTPUT" ]; then OUTPUT="$1"
      fi
      shift ;;
  esac
done

if [ -z "$INPUT" ]; then
  echo "Usage: $0 <input> [output] [--r X,Y] [--g X,Y] [--b X,Y]" >&2
  exit 1
fi

if [ ! -f "$INPUT" ]; then
  echo "Error: file not found: $INPUT" >&2
  exit 1
fi

if [ -z "$OUTPUT" ]; then
  DIR=$(dirname "$INPUT")
  BASE=$(basename "$INPUT" | sed 's/\.[^.]*$//')
  OUTPUT="${DIR}/${BASE}-offset.png"
fi

parse_offset() {
  local off="$1"
  local x="${off%%,*}"
  local y="${off##*,}"
  echo "${x:=0}+${y:=0}"
}

RX="${R_OFF%%,*}"; RY="${R_OFF##*,}"
GX="${G_OFF%%,*}"; GY="${G_OFF##*,}"
BX="${B_OFF%%,*}"; BY="${B_OFF##*,}"

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# Separate into channels, roll each, recombine
magick "$INPUT" -channel R -separate "${TMPDIR}/r.png"
magick "$INPUT" -channel G -separate "${TMPDIR}/g.png"
magick "$INPUT" -channel B -separate "${TMPDIR}/b.png"

magick "${TMPDIR}/r.png" -roll "+${RX}+${RY}" "${TMPDIR}/r.png"
magick "${TMPDIR}/g.png" -roll "+${GX}+${GY}" "${TMPDIR}/g.png"
magick "${TMPDIR}/b.png" -roll "+${BX}+${BY}" "${TMPDIR}/b.png"

magick "${TMPDIR}/r.png" "${TMPDIR}/g.png" "${TMPDIR}/b.png" -combine "$OUTPUT"

echo "Channel offset (r:${R_OFF} g:${G_OFF} b:${B_OFF}) → $OUTPUT" >&2
