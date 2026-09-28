---
title: nest-patches
kind: spec
target: op-img
topic: nest-patches
status: approved
written: 2026-09-26T20:01:25Z
by: claude
---

# nest-patches

Move every op-img patch directory into one `patches/` directory, so the repository's root listing on GitHub is short.

## Why
Josh, 2026-09-26: "the directory list on the github page is too long. could we nest the patches in a directory and update the plumbing to allow for it?" With 41 patch directories at the root, the README is far below the fold on the repository page.

## Behaviour
- Every patch directory moves from `<root>/<patch>/` to `<root>/patches/<patch>/`, with history kept (`git mv`). The root keeps `op`, `README.md`, `pyproject.toml`, `_output/`, `tests/` and `patches/`.
- `op` finds patches in `patches/` next to itself: running a patch, stacking with `+`, `--list`, `--info`, the random three, and unknown-patch errors all work as before. A symlink to `op` on the PATH still works.
- Nothing a user types changes: `op <patch> ...` is the same command.
- The tests call scripts from their new place; the suite passes with the same count plus a layout test.
- The README's per-patch usage lines point at `./patches/<patch>/<script>`, and a short "Adding a patch" section says a new patch is a new directory under `patches/`.

## Out of scope
Grouping patches into category subdirectories (colour, geometry, glitch); `op` would need to search recursively and names could collide. Flat under `patches/` keeps discovery by name.

## Approval
Josh asked for spec, plan and implementation without waiting for his approval on each step; review happens on the pull request.
