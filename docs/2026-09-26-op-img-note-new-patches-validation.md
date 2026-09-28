---
title: new-patches-validation
kind: note
target: op-img
topic: new-patches-validation
status: draft
written: 2026-09-26T07:16:28Z
by: claude
---

# new-patches-validation

Validation of the plan `/home/jmo/linda/docs/2026-09-26-op-img-plan-new-patches.md` against its spec, the brainstorm report `/home/jmo/.local/state/handoffs/op-img/20260926-004700-claude-new-patch-brainstorm/last-message.md`.

## Branch and tip
- Integration branch `new-patches`, checked out at `/home/jmo/repos/op-img/.worktrees/new-patches`, tip `0656df4 test(new-patches): input edge cases for crt, dither, jpeg-rot, ascii`.
- `main` (`2a830c4`, PR #2: pink drawing, missing-input errors, shell `--help`, fixed default-name tests) merged in at `27e7674`.
- Built by Grok in four runs: M1 `20260926-013446-grok-new-patches-m1-build-2`, M2 `20260926-015747-grok-new-patches-m2-build`, M3 `20260926-022408-grok-new-patches-m3-build`, M4 `20260926-024625-grok-new-patches-m4-build`. Each closed `exit:0`, reported no deviation from the plan, and fast-forwarded cleanly.

## Reviews
- Waived by Josh on 2026-09-26: the plan's document review ("codex isn't available. let's just skip to the build step") and every milestone code review ("skip reviews"). No findings exist to check off.

## Checks
- Fresh detached worktree of `0656df4`, `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`: `402 passed in 62.40s`, no failures. Python 3.14.4, Pillow 12.3.0, numpy 2.5.3, scipy 1.18.1.
- No typecheck exists for this Python repository; the plan's Global Constraints name only the pytest suite.

## Acceptance
Each of the 17 ideas, checked end to end through `./op <patch> <McLaren PNG> <out>` in the validation worktree:

| Patch | Files, README section, example, op_cli entry | Runs via op: RGB 1200×596 | Zero strength = original | Look on the McLaren vs the spec |
|---|---|---|---|---|
| fft-phase | met | met, 0.4 s | `--amount 0`, max diff 0 | met |
| zoom-blur | met | met, 1.6 s | `--amount 0`, max diff 0 | met |
| swirl | met | met, 0.4 s | `--angle 0`, max diff 0 | met |
| displace | met | met, 0.4 s | `--amount 0`, max diff 0 | met after fix `fc9d78f` (default 150 px; was 60, barely visible) |
| drip | met | met, 0.2 s | `--length 0`, max diff 0 | met |
| edge-glow | met | met, 0.4 s | `--amount 0`, max diff 0 | met |
| contour | met | met, 0.3 s | `--amount 0`, max diff 0 | met (pink lines) |
| hue-isolate | met | met, 0.2 s | `--amount 0`, max diff 0 | met |
| bloom | met | met, 1.0 s | `--amount 0`, max diff 0 | subtle, as the spec says ("the subtlest idea here") |
| voronoi-mosaic | met | met, 0.4 s | `--size 1 --jitter 0`, max diff 0 | met |
| oil-paint | met | met, 0.3 s | `--radius 0`, max diff 0 | met, subtle at thumbnail size |
| tilt-shift | met | met, 0.3 s | `--blur 0`, max diff 0 | met |
| flow-streak | met | met, 1.9 s | `--length 0`, max diff 0 | met after fix `bc59b67` (default length 36, sigma 6; brushed strokes visible) |
| crt | met | met, 0.4 s | `--amount 0`, max diff 0 | met |
| dither | met | met, 0.2 s | `--levels 256`, max diff 0 | met, fine grain at thumbnail size |
| jpeg-rot | met | met, 0.2 s | `--generations 0`, max diff 0 | met |
| ascii | met | met, 0.2 s | n/a, the spec says it does not ramp | met after fix `b84c99e` (bold glyphs, brightness stretched to the image's range; example mean 56/255, was 14; new test `test_output_is_not_near_black`) |

- Review Focus inputs (transparent, greyscale and palette input; 1, 2 and 5 px images; no extension; JPEG output; dispatcher): met, pinned by `tests/test_new_patch_inputs.py`, which passes in the run above.
- Evidence for the look column: a labelled sheet of the 17 README examples and full-size crops of ascii and flow-streak against the source, viewed in this session.

## Running app
- No user interface; the CLI was exercised through `op` for every new patch (table above), and `./op --list` lists all 41 patches.

## Fixes after first validation
- Josh chose to retune before shipping. Fixes run `20260926-111123-grok-new-patches-fixes` (note `2026-09-26-op-img-handoff-new-patches-fixes.md`) made three commits, `b84c99e`, `bc59b67`, `fc9d78f`, fast-forwarded into `new-patches`. One accepted deviation: ascii keeps absolute brightness for a flat image (no range to stretch), which the existing `test_brightness_picks_glyph` required.
- Re-check in a fresh detached worktree of `fc9d78f`: `403 passed in 57.90s`; flow-streak `--length 0` and displace `--amount 0` still return the original exactly (max diff 0); ascii keeps the 1200×596 size. The three new examples were viewed in this session.

## Verdict
Ready to ship, pending Josh's yes. Every criterion is met with evidence: 403 tests pass, 17 of 17 patches run through `op`, 16 of 16 ramps are exact at zero, and every README example shows its effect. Reviews were waived by Josh.
