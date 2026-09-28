---
title: recolor
kind: spec
target: op-img
topic: recolor
status: approved
written: 2026-09-26T19:52:44Z
by: claude
---

# recolor

A new op-img patch that repaints an image's most prevalent colours with colours the user gives.

## Why
`channel-swap` only reorders the R, G and B channels (`--map B,G,R`), so it can never bring in a colour that is not already there. Josh asked (2026-09-26) for a patch that "accepts color values and replaces the most prevalent color channels with them. If there are two color values, swap in for the two most prevalent channels. If there's one, just swap the top one." He confirmed "most prevalent colour channels" means the image's dominant colours (on the README photo, the orange paint and the green grass), not the R, G and B channels.

## Behaviour
- `op recolor <input> [output] --colors "<c1>[,<c2>...]"` repaints the most prevalent colour with `c1`, the second with `c2`, and so on. One colour changes only the top colour.
- Colours are hex (`#ec4899`, `#f0f`) or CSS names (`pink`), comma-separated, most prevalent first. Default `#ec4899`, the rack's pink.
- "Prevalent" is by pixel count, over colour families found in the image. Light and shadow of one colour count as one family (a lit and a shaded orange are both "orange"). Greys, black and white are not colours here and are never replaced.
- Each replaced colour keeps its light and shade: a glossy car stays glossy, grass keeps its texture. Hue and chroma move to the target; lightness shifts with the target but keeps each pixel's variation.
- Every shade of a replaced colour moves together; near-greys barely move, and edges between colours blend rather than step.
- `--amount` 0 to 1 (default 1): 0 returns the exact original, so the patch ramps and layers in stacks and in the hero loop.
- `--clusters` 2 to 16 (default 6): how many colour families to look for. Fewer colours than clusters must be given.
- A grey image, or one with no colourful family, comes out unchanged.
- Errors: an unreadable colour exits 2 with `not a colour: '<value>'`; too many colours for `--clusters` exits 2; a missing input prints `Error: file not found: <path>` and exits 1.
- Conventions as every Python patch: default output `<base>-recolor<ext>`, one status line on stderr, `requirements.txt` with Pillow and numpy, tests in `tests/test_recolor.py`, an entry in `ALL_PATCHES` and in the new-patch input checks, and a README section in the colour group with an example on the README photo.

## Out of scope
Choosing which family gets which colour by hue (for example "turn the greens blue"); that would be a separate option later.

## Approval
Josh approved building this in the same message that asked for the spec ("write the spec and go ahead and write a plan and hand off to grok headless"), and said no step needs his approval; document review is skipped (Codex unavailable).
