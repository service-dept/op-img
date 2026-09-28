---
title: new-patches-2
kind: plan
target: op-img
topic: new-patches-2
status: draft
written: 2026-09-27T04:19:55Z
by: claude
---

# op-img New Patches 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task, inline (do not use subagent-driven-development). Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the sixteen patches from op-img's second brainstorm, each with tests, a README entry and an example image generated from its defaults.

**Architecture:** Sixteen independent Python patch directories under `patches/`, each following the conventions of the existing patches, discovered by `op` by name. Each milestone ends by adding its patches to the shared input checks in `tests/test_new_patch_inputs.py`.

**Tech Stack:** Python 3.10+, Pillow, NumPy, SciPy; pytest with the `run_tool` and `tmp_workdir` fixtures in `tests/conftest.py`; the `paced` CPU cap (`~/.local/bin/paced`).

**Spec:** the second brainstorm report, `/home/jmo/.local/state/handoffs/op-img/20260926-150225-claude-new-patch-brainstorm-3/last-message.md` (16 ranked ideas). Every script, test and README entry below is complete and was run by the planning session on a scratch copy of op-img `origin/main` at `54fcc03`: the full suite showed `689 passed` under `paced`, and each default was checked by eye on the README photo.

**Executor:** a headless Claude build worker, one milestone per run (Josh's choice for this plan).

## Review site

To look at the new examples in a browser, bring the joshosborne.info review site back:

1. From `/home/jmo/repos/joshosborne.info`, start the server in the background: `node run/review/serve.mjs run/review 4190`. It serves `run/review/` (gitignored) on port 4190, and the existing devlink `joshosborne-review` already exposes it at https://joshosborne-review.linda.sh/.
2. Put the page in a new folder under `run/review/`, for example `run/review/op-img-new-patches-2/`, with an `index.html` and copies of the example images (resize them to 1000 px wide with `paced magick <in> -resize 1000x -quality 85 <out>`).
3. Check it: `curl -s -o /dev/null -w '%{http_code}' https://joshosborne-review.linda.sh/op-img-new-patches-2/`. Expect `200`.
4. Stop the server when done by its PID (note it when you start it, or find it with `ss -ltnp | grep 4190`), with `kill <pid>`. Never use `pkill -f` or `pgrep -f` on the command line: the pattern also matches the shell running the command, and kills or finds it.

## Global Constraints

- **Options that take an X,Y pair (op-img PR #12):** when a pair can start with a minus, pass it to argparse through the `join_pair_values` helper (see droste, ripple and prism below): before Python 3.14, argparse reads `--center -0.2,0.5` as two options. Pairs limited to 0 to 1 cannot start with a minus and do not need it. The Tests workflow runs every pull request on Python 3.10, 3.12 and 3.14, so a missed case fails there.
- **Test conventions (op-img PR #8):** `tests/test_conventions.py` checks every patch in `ALL_PATCHES` for its exact default output name (from `DEFAULT_NAMES`), an explicit output, `Error: file not found` with exit 1 for a missing input, and usage with no arguments. Each patch's own test file holds only its effect, option and edge-case tests. `tests/test_new_patch_inputs.py` is marked `slow`: iterate with `-m "not slow"` and run the full suite before each commit. Test counts printed in the task steps were measured before PR #8 and are higher than you will see; the requirement is no failures.
- **Base:** op-img `main` after PRs #7 (README layout, `assets/`), #8 (test conventions), #10 (ImageMagick patches ported to Python) and #11 (the command is `op-img`, a Python dispatcher in `op_img/cli.py`, PyPI packaging) are merged. The dispatcher at the repository root is `./op-img`; the README's commands read `op-img`.
- Python 3.10+, Pillow, NumPy and SciPy only.
- **CPU cap:** run every pytest and every example render through `paced`; never run them unpaced. The commands are `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q <tests>` and `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img <patch> assets/mclaren.jpg patches/<patch>/example.jpg`. `paced` waits while the CPU package is at or above 80°C or the load average is above half the threads, then caps the command and everything it starts at four cores (`PACED_QUOTA`). If it waits and exits 75, stop and report rather than run unpaced. Run the one task's tests while working and the full suite before each commit.
- If `/tmp/opimg-venv` is missing, create it with `python3 -m venv /tmp/opimg-venv`, then `/tmp/opimg-venv/bin/pip install pytest numpy Pillow scipy`, one command per call.
- **Base:** `main` after the `readme-tweaks` pull request has merged. That PR renames the README's `## Tools` section to `## Patches`, drops `Example:` lines (defaults are the showcase), moves example images into each patch's own directory as `patches/<name>/example.jpg`, and moves the README photo to `assets/mclaren.jpg`. If `assets/mclaren.jpg` does not exist, stop and report: the base is wrong.
- One directory per patch, `patches/<name>/`, holding `<name>.py` (executable) and `requirements.txt`, plus `example.jpg` generated from the defaults.
- Argument style: positional `input`, optional positional `output`, kebab-case options whose help ends `(default: X)`. Default output `f"{base}-{suffix}{ext or '.png'}"` with the suffix named in each task. One status line on stderr. A missing input prints `Error: file not found: <path>` and exits 1; invalid options go through `parser.error` (exit 2). Output is RGB and the same size as the input.
- US spelling everywhere: color, gray, center, neighboring, artifact. Never colour, grey, centre.
- **Baseline:** at the start of every milestone, run the full suite and record the count. The milestone is green when the full suite shows no failure.
- Headless worker: run one simple command per shell call. Do not chain commands with `&&`, `;` or `|`.
- Commit once per task, staging files by path. Never `git add -A` or `git add .`.
- README placement: patches marked "main group" go directly before the line `### isolate-threshold` (the start of the color group), in plan order. Color patches go directly before the line `### dot-halftone` (the end of the color group). Drawing patches go directly after the line `![stipple example](patches/stipple/example.jpg)` (the end of the drawing group), each followed by one blank line.

## Review Focus

1. Transparent, grayscale and palette inputs, as people drop in screenshots and GIF frames: every patch writes an RGB image the same size. Pinned by the milestone input-check tasks (`test_accepts_other_modes`).
2. Tiny images (1×1, 2×2, 5×5), smaller than a shard, a strip, a kernel or a simulation cell: every patch runs and keeps the size. Pinned by `test_tiny_images`.
3. An input with no extension and an explicit `.jpg` output: pinned by `test_input_without_extension_defaults_to_png` and `test_explicit_jpeg_output`.
4. Zero strength returns the exact original for every patch that ramps (all but papercut, whose flat colors never equal the photo). Pinned by each patch's identity test.
5. Running through the dispatcher by name: pinned by the `ALL_PATCHES` entry each task adds and by the input checks' dispatcher test.

## File Structure

- `patches/reeded-glass/reeded-glass.py`, `patches/reeded-glass/requirements.txt`, `patches/reeded-glass/example.jpg`, `tests/test_reeded_glass.py`
- `patches/droste/droste.py`, `patches/droste/requirements.txt`, `patches/droste/example.jpg`, `tests/test_droste.py`
- `patches/mode7/mode7.py`, `patches/mode7/requirements.txt`, `patches/mode7/example.jpg`, `tests/test_mode7.py`
- `patches/ripple/ripple.py`, `patches/ripple/requirements.txt`, `patches/ripple/example.jpg`, `tests/test_ripple.py`
- `patches/smear/smear.py`, `patches/smear/requirements.txt`, `patches/smear/example.jpg`, `tests/test_smear.py`
- `patches/shatter/shatter.py`, `patches/shatter/requirements.txt`, `patches/shatter/example.jpg`, `tests/test_shatter.py`
- `patches/prism/prism.py`, `patches/prism/requirements.txt`, `patches/prism/example.jpg`, `tests/test_prism.py`
- `patches/bokeh/bokeh.py`, `patches/bokeh/requirements.txt`, `patches/bokeh/example.jpg`, `tests/test_bokeh.py`
- `patches/relief/relief.py`, `patches/relief/requirements.txt`, `patches/relief/example.jpg`, `tests/test_relief.py`
- `patches/solarize/solarize.py`, `patches/solarize/requirements.txt`, `patches/solarize/example.jpg`, `tests/test_solarize.py`
- `patches/hue-wave/hue-wave.py`, `patches/hue-wave/requirements.txt`, `patches/hue-wave/example.jpg`, `tests/test_hue_wave.py`
- `patches/papercut/papercut.py`, `patches/papercut/requirements.txt`, `patches/papercut/example.jpg`, `tests/test_papercut.py`
- `patches/weave/weave.py`, `patches/weave/requirements.txt`, `patches/weave/example.jpg`, `tests/test_weave.py`
- `patches/ridgeline/ridgeline.py`, `patches/ridgeline/requirements.txt`, `patches/ridgeline/example.jpg`, `tests/test_ridgeline.py`
- `patches/sketch/sketch.py`, `patches/sketch/requirements.txt`, `patches/sketch/example.jpg`, `tests/test_sketch.py`
- `patches/reaction-diffusion/reaction-diffusion.py`, `patches/reaction-diffusion/requirements.txt`, `patches/reaction-diffusion/example.jpg`, `tests/test_reaction_diffusion.py`
- Modified: `tests/test_op_cli.py` (`ALL_PATCHES`), `tests/test_new_patch_inputs.py` (`NEW_PATCHES`), `README.md`

---

## M1: Warps

**Start of milestone:** run `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests` and record the result as the baseline.

### Task 1: reeded-glass

**Files:**
- Create: `patches/reeded-glass/reeded-glass.py`, `patches/reeded-glass/requirements.txt`, `tests/test_reeded_glass.py`, `patches/reeded-glass/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `reeded-glass` patch, default output suffix `-reeded`, README entry (main group).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_reeded_glass.py` with exactly:

```python
"""Tests for reeded-glass tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestReededGlass:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        r = run_tool("reeded-glass", "reeded-glass.py", [img, out, "--width", "8", "--direction", "horizontal"])
        assert r.returncode == 0, r.stderr
        assert "direction=horizontal" in r.stderr
        assert_valid_image(out)

    def test_zero_strength_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        assert run_tool("reeded-glass", "reeded-glass.py", [img, out, "--strength", "0"]).returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_full_strength_mirrors_each_strip(self, run_tool, tmp_path):
        """A left-to-right ramp runs right-to-left inside each strip at strength 1."""
        arr = np.tile(np.arange(64, dtype=np.uint8)[None, :, None] * 4, (8, 1, 3))
        img = str(tmp_path / "ramp.png")
        Image.fromarray(arr).save(img)
        out = str(tmp_path / "out.png")
        assert run_tool("reeded-glass", "reeded-glass.py", [img, out, "--width", "16", "--strength", "1"]).returncode == 0
        row = _pixels(out)[4, :, 0]
        assert row[2] > row[13], "inside a strip the ramp should run backwards"

    def test_bad_width_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        assert run_tool("reeded-glass", "reeded-glass.py", [img, "--width", "2"]).returncode == 2
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_reeded_glass.py`. Expected: the tests fail because `patches/reeded-glass/reeded-glass.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/reeded-glass/requirements.txt` with these lines:

```
Pillow
numpy
scipy
```

Create `patches/reeded-glass/reeded-glass.py` with exactly this, then run `chmod +x patches/reeded-glass/reeded-glass.py`:

```python
#!/usr/bin/env python3
"""Show the image through fluted glass: each strip refracts a magnified, flipped slice of what is behind it."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates


def reed(arr: np.ndarray, width: int, strength: float) -> np.ndarray:
    """Refract vertical strips of the given width. strength 0 is the original, 1 mirrors each strip."""
    h, w, _ = arr.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    center = (np.floor(xx / width) + 0.5) * width
    src_x = center + (xx - center) * (1.0 - 2.0 * strength)
    out = np.stack([map_coordinates(arr[:, :, c], [yy, src_x], order=1, mode="reflect") for c in range(3)], axis=2)
    # Rounded glass: each strip darkens a little toward its edges.
    u = (xx - center) / width
    return out * (1.0 - 0.25 * strength * (2.0 * u) ** 2)[:, :, None]


def main() -> None:
    parser = argparse.ArgumentParser(description="Refract the image through fluted glass.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--width", type=int, default=40, help="Strip width in pixels, 4 to 200 (default: 40)")
    parser.add_argument("--strength", type=float, default=0.8, help="Refraction, 0 (original) to 1 (mirrored strips) (default: 0.8)")
    parser.add_argument("--direction", choices=["vertical", "horizontal"], default="vertical", help="Strip direction (default: vertical)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 4 <= args.width <= 200:
        parser.error("--width must be between 4 and 200")
    if not 0.0 <= args.strength <= 1.0:
        parser.error("--strength must be between 0 and 1")

    img = Image.open(args.input).convert("RGB")
    arr = np.array(img, dtype=np.float64)
    if args.direction == "horizontal":
        result = reed(arr.transpose(1, 0, 2), args.width, args.strength).transpose(1, 0, 2)
    else:
        result = reed(arr, args.width, args.strength)
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-reeded{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved reeded-glass image to {out_path} (width={args.width}, strength={args.strength}, direction={args.direction})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "reeded-glass",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "reeded-glass": "input-reeded.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_reeded_glass.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_reeded_glass.py`).

- [ ] **Step 6: README entry.** Insert this directly before the line `### isolate-threshold`, followed by one blank line:

````markdown
### reeded-glass

Show the image through fluted glass: the frame splits into strips, and each strip refracts a magnified, flipped slice of what is behind it.

```bash
python3 ./patches/reeded-glass/reeded-glass.py <input> [output] [--width PX] [--strength N] [--direction vertical|horizontal]
```

Default: `--width 40 --strength 0.8 --direction vertical`

![reeded-glass example](patches/reeded-glass/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img reeded-glass assets/mclaren.jpg patches/reeded-glass/example.jpg`, then `ls -la patches/reeded-glass/example.jpg` (expect more than 10 KB). Open it and check it matches: the car reads through a comb of vertical strips, each a mirrored, shaded sliver.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/reeded-glass/reeded-glass.py`, `patches/reeded-glass/requirements.txt`, `patches/reeded-glass/example.jpg`, `tests/test_reeded_glass.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(reeded-glass): add reeded-glass patch` and the trailer the build note gives.

### Task 2: droste

**Files:**
- Create: `patches/droste/droste.py`, `patches/droste/requirements.txt`, `tests/test_droste.py`, `patches/droste/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `droste` patch, default output suffix `-droste`, README entry (main group).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_droste.py` with exactly:

```python
"""Tests for droste tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestDroste:
    def test_zero_depth_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        assert run_tool("droste", "droste.py", [img, out, "--depth", "0"]).returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_outer_ring_untouched_and_center_changed(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        assert run_tool("droste", "droste.py", [img, out, "--scale", "0.5"]).returncode == 0
        a, b = _pixels(img), _pixels(out)
        assert np.array_equal(a[:4], b[:4]), "the outermost ring is the original frame"
        assert not np.array_equal(a[24:40, 24:40], b[24:40, 24:40]), "the center holds a smaller copy"

    def test_bad_options_are_errors(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        for opts in (["--scale", "0.99"], ["--depth", "13"], ["--center", "0.5"]):
            assert run_tool("droste", "droste.py", [img] + opts).returncode == 2, opts

    def test_center_that_starts_with_a_minus(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        r = run_tool("droste", "droste.py", [img, out, "--center", "-0.2,0.5"])
        assert r.returncode == 0, r.stderr
        assert_valid_image(out)
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_droste.py`. Expected: the tests fail because `patches/droste/droste.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/droste/requirements.txt` with these lines:

```
Pillow
numpy
scipy
```

Create `patches/droste/droste.py` with exactly this, then run `chmod +x patches/droste/droste.py`:

```python
#!/usr/bin/env python3
"""Nest smaller copies of the whole frame inside itself, a picture-in-picture tunnel that can spiral."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates


def parse_center(value: str) -> tuple[float, float]:
    try:
        x, y = (float(v) for v in value.split(","))
    except ValueError:
        raise argparse.ArgumentTypeError("use two numbers, X,Y (for example 0.5,0.5)")
    return x, y


def droste(arr: np.ndarray, scale: float, depth: int, rotate: float, center: tuple[float, float]) -> np.ndarray:
    h, w, _ = arr.shape
    if depth == 0:
        return arr.copy()
    cx, cy = center[0] * w, center[1] * h
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    dx, dy = xx - cx, yy - cy
    # How far out a pixel is, as a fraction of the frame; each level inward is `scale` smaller.
    q = np.maximum(np.abs(dx) / max(w / 2.0, 1e-9), np.abs(dy) / max(h / 2.0, 1e-9))
    with np.errstate(divide="ignore"):
        level = np.floor(np.log(np.maximum(q, 1e-12)) / np.log(scale))
    level = np.clip(np.nan_to_num(level, nan=depth, posinf=depth), 0, depth)
    angle = -np.radians(rotate) * level
    zoom = scale ** level
    rx = (dx * np.cos(angle) - dy * np.sin(angle)) / zoom
    ry = (dx * np.sin(angle) + dy * np.cos(angle)) / zoom
    src_x, src_y = cx + rx, cy + ry
    return np.stack([map_coordinates(arr[:, :, c], [src_y, src_x], order=1, mode="nearest") for c in range(3)], axis=2)


def join_pair_values(argv: list[str], options: set[str]) -> list[str]:
    """Pass each X,Y option as --opt=VALUE. Before Python 3.14, argparse reads a value that
    starts with a minus, such as -0.2,0.5, as another option rather than as the value."""
    out, i = [], 0
    while i < len(argv):
        if argv[i] in options and i + 1 < len(argv):
            out.append(f"{argv[i]}={argv[i + 1]}")
            i += 2
        else:
            out.append(argv[i])
            i += 1
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Nest copies of the frame inside itself.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--scale", type=float, default=0.7, help="Size of each copy relative to the one around it, 0.3 to 0.95 (default: 0.7)")
    parser.add_argument("--depth", type=int, default=6, help="Levels of copies, 0 (original) to 12 (default: 6)")
    parser.add_argument("--rotate", type=float, default=0.0, help="Rotation per level in degrees; copies past the frame edge repeat its border (default: 0.0)")
    parser.add_argument("--center", type=parse_center, default=(0.5, 0.5), help="Tunnel center as X,Y fractions of the image (default: 0.5,0.5)")
    args = parser.parse_args(join_pair_values(sys.argv[1:], {"--center"}))

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.3 <= args.scale <= 0.95:
        parser.error("--scale must be between 0.3 and 0.95")
    if not 0 <= args.depth <= 12:
        parser.error("--depth must be between 0 and 12")

    img = Image.open(args.input).convert("RGB")
    result = droste(np.array(img, dtype=np.float64), args.scale, args.depth, args.rotate, args.center)
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-droste{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved droste image to {out_path} (scale={args.scale}, depth={args.depth}, rotate={args.rotate})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "droste",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "droste": "input-droste.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_droste.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_droste.py`).

- [ ] **Step 6: README entry.** Insert this directly before the line `### isolate-threshold`, followed by one blank line:

````markdown
### droste

Nest smaller copies of the whole frame inside itself, a picture-in-picture tunnel that can spiral with `--rotate`.

```bash
python3 ./patches/droste/droste.py <input> [output] [--scale N] [--depth N] [--rotate DEG] [--center X,Y]
```

Default: `--scale 0.7 --depth 6 --rotate 0 --center 0.5,0.5`

![droste example](patches/droste/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img droste assets/mclaren.jpg patches/droste/example.jpg`, then `ls -la patches/droste/example.jpg` (expect more than 10 KB). Open it and check it matches: a smaller copy of the frame sits inside the frame, then another inside that, down to the center.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/droste/droste.py`, `patches/droste/requirements.txt`, `patches/droste/example.jpg`, `tests/test_droste.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(droste): add droste patch` and the trailer the build note gives.

### Task 3: mode7

**Files:**
- Create: `patches/mode7/mode7.py`, `patches/mode7/requirements.txt`, `tests/test_mode7.py`, `patches/mode7/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `mode7` patch, default output suffix `-mode7`, README entry (main group).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_mode7.py` with exactly:

```python
"""Tests for mode7 tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestMode7:
    def test_zero_tilt_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        assert run_tool("mode7", "mode7.py", [img, out, "--tilt", "0"]).returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_steep_tilt_has_black_sky(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        assert run_tool("mode7", "mode7.py", [img, out, "--tilt", "80"]).returncode == 0
        px = _pixels(out)
        assert px[0].max() == 0, "the top row is above the horizon"
        assert px[-1].max() > 0, "the bottom row is floor"

    def test_bad_tilt_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        assert run_tool("mode7", "mode7.py", [img, "--tilt", "90"]).returncode == 2
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_mode7.py`. Expected: the tests fail because `patches/mode7/mode7.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/mode7/requirements.txt` with these lines:

```
Pillow
numpy
scipy
```

Create `patches/mode7/mode7.py` with exactly this, then run `chmod +x patches/mode7/mode7.py`:

```python
#!/usr/bin/env python3
"""Tilt the image back into a floor that tiles to a horizon, like SNES Mode 7."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates


def mode7(arr: np.ndarray, tilt: float, fog: float) -> np.ndarray:
    """Lay the image down as a plane tilted by `tilt` degrees about the middle row.

    The horizon sits at h/2 - h*cot(tilt) from the top, so it enters the frame as the tilt passes
    about 63 degrees. Above it is black sky.
    """
    h, w, _ = arr.shape
    if tilt == 0:
        return arr.copy()
    t = np.radians(tilt)
    f = float(h)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    xp, yp = xx - w / 2.0, yy - h / 2.0
    den = f * np.cos(t) + yp * np.sin(t)
    ground = den > 1e-6
    safe = np.where(ground, den, 1.0)
    src_x = f * xp / safe + w / 2.0
    src_y = f * yp / safe + h / 2.0
    out = np.stack([map_coordinates(arr[:, :, c], [src_y, src_x], order=1, mode="grid-wrap") for c in range(3)], axis=2)
    # Fog: fade toward black as the floor recedes.
    fade = 1.0 - fog * np.clip(1.0 - safe / f, 0.0, 1.0)
    out *= fade[:, :, None]
    out[~ground] = 0.0
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Tilt the image into a Mode 7 floor.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--tilt", type=float, default=72.0, help="Tilt in degrees, 0 (original) to 85 (default: 72.0)")
    parser.add_argument("--fog", type=float, default=0.5, help="Fade toward the horizon, 0 to 1 (default: 0.5)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.tilt <= 85.0:
        parser.error("--tilt must be between 0 and 85")
    if not 0.0 <= args.fog <= 1.0:
        parser.error("--fog must be between 0 and 1")

    img = Image.open(args.input).convert("RGB")
    result = mode7(np.array(img, dtype=np.float64), args.tilt, args.fog)
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-mode7{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved mode7 image to {out_path} (tilt={args.tilt}, fog={args.fog})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "mode7",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "mode7": "input-mode7.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_mode7.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_mode7.py`).

- [ ] **Step 6: README entry.** Insert this directly before the line `### isolate-threshold`, followed by one blank line:

````markdown
### mode7

Tilt the image back into a floor that tiles to a horizon, like SNES Mode 7. Above the horizon is black sky.

```bash
python3 ./patches/mode7/mode7.py <input> [output] [--tilt DEG] [--fog N]
```

Default: `--tilt 72 --fog 0.5`

![mode7 example](patches/mode7/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img mode7 assets/mclaren.jpg patches/mode7/example.jpg`, then `ls -la patches/mode7/example.jpg` (expect more than 10 KB). Open it and check it matches: black sky over the top sixth; below it the photo lies down as a floor of repeating rows that shrink toward the horizon.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/mode7/mode7.py`, `patches/mode7/requirements.txt`, `patches/mode7/example.jpg`, `tests/test_mode7.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(mode7): add mode7 patch` and the trailer the build note gives.

### Task 4: ripple

**Files:**
- Create: `patches/ripple/ripple.py`, `patches/ripple/requirements.txt`, `tests/test_ripple.py`, `patches/ripple/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `ripple` patch, default output suffix `-ripple`, README entry (main group).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_ripple.py` with exactly:

```python
"""Tests for ripple tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestRipple:
    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        assert run_tool("ripple", "ripple.py", [img, out, "--amount", "0"]).returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_changes_the_image(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        assert run_tool("ripple", "ripple.py", [img, out, "--wavelength", "12"]).returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).mean() > 2

    def test_bad_options_are_errors(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        for opts in (["--amount", "61"], ["--wavelength", "0"], ["--damping", "4"]):
            assert run_tool("ripple", "ripple.py", [img] + opts).returncode == 2, opts

    def test_center_that_starts_with_a_minus(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        r = run_tool("ripple", "ripple.py", [img, out, "--center", "-0.2,0.5"])
        assert r.returncode == 0, r.stderr
        assert_valid_image(out)
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_ripple.py`. Expected: the tests fail because `patches/ripple/ripple.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/ripple/requirements.txt` with these lines:

```
Pillow
numpy
scipy
```

Create `patches/ripple/ripple.py` with exactly this, then run `chmod +x patches/ripple/ripple.py`:

```python
#!/usr/bin/env python3
"""Drop a stone at a point: concentric water rings refract the image and die away with distance."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates


def parse_center(value: str) -> tuple[float, float]:
    try:
        x, y = (float(v) for v in value.split(","))
    except ValueError:
        raise argparse.ArgumentTypeError("use two numbers, X,Y (for example 0.5,0.5)")
    return x, y


def ripple(arr: np.ndarray, amount: float, wavelength: float, damping: float, center: tuple[float, float]) -> np.ndarray:
    h, w, _ = arr.shape
    if amount == 0:
        return arr.copy()
    cx, cy = center[0] * w, center[1] * h
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    dx, dy = xx - cx, yy - cy
    r = np.hypot(dx, dy)
    half_diag = max(np.hypot(w, h) / 2.0, 1.0)
    envelope = np.exp(-damping * r / half_diag)
    disp = amount * np.sin(2 * np.pi * r / wavelength) * envelope
    grow = 1.0 + disp / np.maximum(r, 1.0)
    src_x, src_y = cx + dx * grow, cy + dy * grow
    out = np.stack([map_coordinates(arr[:, :, c], [src_y, src_x], order=1, mode="reflect") for c in range(3)], axis=2)
    # A faint highlight on each crest.
    return out * (1.0 + 0.2 * (amount / 60.0) * np.cos(2 * np.pi * r / wavelength) * envelope)[:, :, None]


def join_pair_values(argv: list[str], options: set[str]) -> list[str]:
    """Pass each X,Y option as --opt=VALUE. Before Python 3.14, argparse reads a value that
    starts with a minus, such as -0.2,0.5, as another option rather than as the value."""
    out, i = [], 0
    while i < len(argv):
        if argv[i] in options and i + 1 < len(argv):
            out.append(f"{argv[i]}={argv[i + 1]}")
            i += 2
        else:
            out.append(argv[i])
            i += 1
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Ripple the image with concentric water rings.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=14.0, help="Ring height in pixels, 0 (original) to 60 (default: 14.0)")
    parser.add_argument("--wavelength", type=float, default=40.0, help="Distance between rings in pixels (default: 40.0)")
    parser.add_argument("--damping", type=float, default=1.0, help="How fast the rings die away, 0 to 3 (default: 1.0)")
    parser.add_argument("--center", type=parse_center, default=(0.5, 0.5), help="Where the stone lands, X,Y fractions of the image (default: 0.5,0.5)")
    args = parser.parse_args(join_pair_values(sys.argv[1:], {"--center"}))

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 60.0:
        parser.error("--amount must be between 0 and 60")
    if args.wavelength <= 0:
        parser.error("--wavelength must be greater than 0")
    if not 0.0 <= args.damping <= 3.0:
        parser.error("--damping must be between 0 and 3")

    img = Image.open(args.input).convert("RGB")
    result = ripple(np.array(img, dtype=np.float64), args.amount, args.wavelength, args.damping, args.center)
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-ripple{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved ripple image to {out_path} (amount={args.amount}, wavelength={args.wavelength}, damping={args.damping})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "ripple",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "ripple": "input-ripple.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_ripple.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_ripple.py`).

- [ ] **Step 6: README entry.** Insert this directly before the line `### isolate-threshold`, followed by one blank line:

````markdown
### ripple

Drop a stone at a point: concentric water rings refract the image and die away with distance.

```bash
python3 ./patches/ripple/ripple.py <input> [output] [--amount PX] [--wavelength PX] [--damping N] [--center X,Y]
```

Default: `--amount 14 --wavelength 40 --damping 1 --center 0.5,0.5`

![ripple example](patches/ripple/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img ripple assets/mclaren.jpg patches/ripple/example.jpg`, then `ls -la patches/ripple/example.jpg` (expect more than 10 KB). Open it and check it matches: rings spread from the center; the bodywork, wheels and lawn bend into wavy bands with faint crest highlights.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/ripple/ripple.py`, `patches/ripple/requirements.txt`, `patches/ripple/example.jpg`, `tests/test_ripple.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(ripple): add ripple patch` and the trailer the build note gives.

### Task 5: smear

**Files:**
- Create: `patches/smear/smear.py`, `patches/smear/requirements.txt`, `tests/test_smear.py`, `patches/smear/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `smear` patch, default output suffix `-smear`, README entry (main group).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_smear.py` with exactly:

```python
"""Tests for smear tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestSmear:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        r = run_tool("smear", "smear.py", [img, out, "--position", "0.3", "--length", "0.5", "--direction", "up"])
        assert r.returncode == 0, r.stderr
        assert "direction=up" in r.stderr
        assert_valid_image(out)

    def test_zero_length_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        assert run_tool("smear", "smear.py", [img, out, "--length", "0"]).returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_right_copies_one_column_to_the_edge(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        assert run_tool("smear", "smear.py", [img, out]).returncode == 0
        a, b = _pixels(img), _pixels(out)
        assert np.array_equal(b[:, :32], a[:, :32]), "left of the slice is untouched"
        assert (b[:, 32:] == a[:, 32:33]).all(), "every column from the slice on is the slice"

    def test_bad_position_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        assert run_tool("smear", "smear.py", [img, "--position", "1.5"]).returncode == 2
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_smear.py`. Expected: the tests fail because `patches/smear/smear.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/smear/requirements.txt` with these lines:

```
Pillow
numpy
```

Create `patches/smear/smear.py` with exactly this, then run `chmod +x patches/smear/smear.py`:

```python
#!/usr/bin/env python3
"""Stretch one column or row of the image to the edge of the frame, the classic pixel-stretch glitch."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def orient(arr: np.ndarray, direction: str) -> np.ndarray:
    """Rotate the array so the smear runs down axis 0."""
    if direction == "down":
        return arr
    if direction == "up":
        return arr[::-1]
    if direction == "right":
        return arr.transpose(1, 0, 2)
    return arr.transpose(1, 0, 2)[::-1]


def unorient(arr: np.ndarray, direction: str) -> np.ndarray:
    if direction == "down":
        return arr
    if direction == "up":
        return arr[::-1]
    if direction == "right":
        return arr.transpose(1, 0, 2)
    return arr[::-1].transpose(1, 0, 2)


def smear(arr: np.ndarray, position: float, length: float, direction: str) -> np.ndarray:
    work = orient(arr, direction).copy()
    size = work.shape[0]
    start = min(int(position * size), size - 1)
    count = int(length * (size - start))
    work[start:start + count] = work[start:start + 1]
    return unorient(work, direction)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stretch one slice of the image to the edge.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--position", type=float, default=0.5, help="Where the stretched slice sits, 0 to 1 along the direction (default: 0.5)")
    parser.add_argument("--length", type=float, default=1.0, help="Share of the rest of the frame covered, 0 (original) to 1 (default: 1.0)")
    parser.add_argument("--direction", choices=["right", "left", "up", "down"], default="right", help="Direction of the stretch (default: right)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.position <= 1.0:
        parser.error("--position must be between 0 and 1")
    if not 0.0 <= args.length <= 1.0:
        parser.error("--length must be between 0 and 1")

    img = Image.open(args.input).convert("RGB")
    result = smear(np.array(img), args.position, args.length, args.direction)
    result_img = Image.fromarray(result)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-smear{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved smeared image to {out_path} (position={args.position}, length={args.length}, direction={args.direction})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "smear",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "smear": "input-smear.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_smear.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_smear.py`).

- [ ] **Step 6: README entry.** Insert this directly before the line `### isolate-threshold`, followed by one blank line:

````markdown
### smear

Stretch one column or row to the edge of the frame, the classic pixel-stretch glitch.

```bash
python3 ./patches/smear/smear.py <input> [output] [--position N] [--length N] [--direction right|left|up|down]
```

Default: `--position 0.5 --length 1 --direction right`

![smear example](patches/smear/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img smear assets/mclaren.jpg patches/smear/example.jpg`, then `ls -la patches/smear/example.jpg` (expect more than 10 KB). Open it and check it matches: the left half is untouched; from the middle column rightward, straight streaks of that one column run to the edge.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/smear/smear.py`, `patches/smear/requirements.txt`, `patches/smear/example.jpg`, `tests/test_smear.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(smear): add smear patch` and the trailer the build note gives.

### Task 6: input checks for reeded-glass, droste, mode7, ripple, smear

**Files:**
- Modify: `tests/test_new_patch_inputs.py`

- [ ] **Step 1: Add the milestone's patches.** In `tests/test_new_patch_inputs.py`, add these lines as the last entries of `NEW_PATCHES`, directly before its closing `]`:

```python
    ("reeded-glass", "reeded"),
    ("droste", "droste"),
    ("mode7", "mode7"),
    ("ripple", "ripple"),
    ("smear", "smear"),
```

- [ ] **Step 2: Run the input checks.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_new_patch_inputs.py`. Expected: all pass (45 new checks). If a patch fails a check, fix the patch (not the check) and note the change in the closing report.

- [ ] **Step 3: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: no failures.

- [ ] **Step 4: Commit.** Stage `tests/test_new_patch_inputs.py` (and any patch fixed in Step 2) by path, and commit with the subject `test(new-patches): input edge cases for reeded-glass, droste, mode7, ripple, smear` and the trailer the build note gives.

## M2: Shards, light and depth

**Start of milestone:** run `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests` and record the result as the baseline.

### Task 7: shatter

**Files:**
- Create: `patches/shatter/shatter.py`, `patches/shatter/requirements.txt`, `tests/test_shatter.py`, `patches/shatter/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `shatter` patch, default output suffix `-shatter`, README entry (main group).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_shatter.py` with exactly:

```python
"""Tests for shatter tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestShatter:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        r = run_tool("shatter", "shatter.py", [img, out, "--size", "16", "--amount", "5", "--cracks", "1", "--seed", "3"])
        assert r.returncode == 0, r.stderr
        assert "seed=3" in r.stderr
        assert_valid_image(out)

    def test_no_amount_no_cracks_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        assert run_tool("shatter", "shatter.py", [img, out, "--amount", "0", "--cracks", "0"]).returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_seed_is_reproducible_and_cracks_are_dark(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        a, b = str(tmp_path / "a.png"), str(tmp_path / "b.png")
        assert run_tool("shatter", "shatter.py", [img, a, "--size", "16", "--seed", "7"]).returncode == 0
        assert run_tool("shatter", "shatter.py", [img, b, "--size", "16", "--seed", "7"]).returncode == 0
        pa = _pixels(a)
        assert np.array_equal(pa, _pixels(b))
        assert (pa == 20).all(axis=2).sum() > 20, "crack pixels are (20, 20, 20)"

    def test_bad_size_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        assert run_tool("shatter", "shatter.py", [img, "--size", "4"]).returncode == 2
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_shatter.py`. Expected: the tests fail because `patches/shatter/shatter.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/shatter/requirements.txt` with these lines:

```
Pillow
numpy
scipy
```

Create `patches/shatter/shatter.py` with exactly this, then run `chmod +x patches/shatter/shatter.py`:

```python
#!/usr/bin/env python3
"""Break the image into shards that slide and turn slightly, with dark cracks between them."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, map_coordinates
from scipy.spatial import cKDTree


def shatter(arr: np.ndarray, size: int, amount: float, cracks: int, seed: int) -> np.ndarray:
    h, w, _ = arr.shape
    rng = np.random.default_rng(seed)
    # Shard seeds on a jittered grid, one per `size` pixels.
    gy, gx = np.mgrid[size / 2:max(h, 1):size, size / 2:max(w, 1):size].astype(np.float64)
    if gy.size == 0:
        gy, gx = np.array([[h / 2.0]]), np.array([[w / 2.0]])
    seeds = np.stack([gy.ravel(), gx.ravel()], axis=1)
    seeds += rng.uniform(-0.5, 0.5, seeds.shape) * size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    _, labels = cKDTree(seeds).query(np.stack([yy.ravel(), xx.ravel()], axis=1))
    labels = labels.reshape(h, w)

    shift = rng.uniform(-1.0, 1.0, seeds.shape) * amount
    turn = rng.uniform(-1.0, 1.0, len(seeds)) * amount * 0.004
    sy, sx = seeds[labels, 0], seeds[labels, 1]
    ry, rx = yy - sy, xx - sx
    cos, sin = np.cos(-turn[labels]), np.sin(-turn[labels])
    src_y = sy + sin * rx + cos * ry - shift[labels, 0]
    src_x = sx + cos * rx - sin * ry - shift[labels, 1]
    out = np.stack([map_coordinates(arr[:, :, c], [src_y, src_x], order=1, mode="reflect") for c in range(3)], axis=2)

    if cracks > 0:
        edge = np.zeros((h, w), dtype=bool)
        edge[:, 1:] |= labels[:, 1:] != labels[:, :-1]
        edge[1:, :] |= labels[1:, :] != labels[:-1, :]
        if cracks > 1:
            edge = binary_dilation(edge, iterations=cracks - 1)
        # A one-pixel glassy rim below and right of each crack.
        rim = np.zeros_like(edge)
        rim[1:, 1:] = edge[:-1, :-1] & ~edge[1:, 1:]
        out[rim] = np.minimum(out[rim] + 60.0, 255.0)
        out[edge] = 20.0
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Shatter the image into sliding shards.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--size", type=int, default=80, help="Shard spacing in pixels, 8 to 300 (default: 80)")
    parser.add_argument("--amount", type=float, default=22.0, help="Largest shard shift in pixels, 0 to 100 (default: 22.0)")
    parser.add_argument("--cracks", type=int, default=2, help="Crack width in pixels, 0 for none (default: 2)")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for the shard layout (default: 0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 8 <= args.size <= 300:
        parser.error("--size must be between 8 and 300")
    if not 0.0 <= args.amount <= 100.0:
        parser.error("--amount must be between 0 and 100")
    if args.cracks < 0:
        parser.error("--cracks must be 0 or more")

    img = Image.open(args.input).convert("RGB")
    result = shatter(np.array(img, dtype=np.float64), args.size, args.amount, args.cracks, args.seed)
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-shatter{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved shattered image to {out_path} (size={args.size}, amount={args.amount}, cracks={args.cracks}, seed={args.seed})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "shatter",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "shatter": "input-shatter.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_shatter.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_shatter.py`).

- [ ] **Step 6: README entry.** Insert this directly before the line `### isolate-threshold`, followed by one blank line:

````markdown
### shatter

Break the image into shards that slide and turn slightly, with dark cracks between them.

```bash
python3 ./patches/shatter/shatter.py <input> [output] [--size PX] [--amount PX] [--cracks PX] [--seed N]
```

Default: `--size 80 --amount 22 --cracks 2 --seed 0`

![shatter example](patches/shatter/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img shatter assets/mclaren.jpg patches/shatter/example.jpg`, then `ls -la patches/shatter/example.jpg` (expect more than 10 KB). Open it and check it matches: the car behind smashed glass: jagged shards that don't quite line up, with dark cracks.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/shatter/shatter.py`, `patches/shatter/requirements.txt`, `patches/shatter/example.jpg`, `tests/test_shatter.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(shatter): add shatter patch` and the trailer the build note gives.

### Task 8: prism

**Files:**
- Create: `patches/prism/prism.py`, `patches/prism/requirements.txt`, `tests/test_prism.py`, `patches/prism/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `prism` patch, default output suffix `-prism`, README entry (main group).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_prism.py` with exactly:

```python
"""Tests for prism tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestPrism:
    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        assert run_tool("prism", "prism.py", [img, out, "--amount", "0"]).returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_white_edge_splits_into_color(self, run_tool, tmp_path):
        """A white square on black gains colored fringes at its edges; gray stays gray at the center."""
        arr = np.zeros((64, 64, 3), dtype=np.uint8)
        arr[8:56, 8:56] = 255
        img = str(tmp_path / "square.png")
        Image.fromarray(arr).save(img)
        out = str(tmp_path / "out.png")
        assert run_tool("prism", "prism.py", [img, out, "--amount", "0.1"]).returncode == 0
        px = _pixels(out)
        spread = px.max(axis=2) - px.min(axis=2)
        assert spread.max() > 40, "edges should carry color"
        assert spread[32, 32] <= 2, "the flat center stays neutral"

    def test_bad_samples_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        assert run_tool("prism", "prism.py", [img, "--samples", "2"]).returncode == 2

    def test_center_that_starts_with_a_minus(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        r = run_tool("prism", "prism.py", [img, out, "--center", "-0.2,0.5"])
        assert r.returncode == 0, r.stderr
        assert_valid_image(out)
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_prism.py`. Expected: the tests fail because `patches/prism/prism.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/prism/requirements.txt` with these lines:

```
Pillow
numpy
scipy
```

Create `patches/prism/prism.py` with exactly this, then run `chmod +x patches/prism/prism.py`:

```python
#!/usr/bin/env python3
"""Disperse the image into a rainbow of copies scaled out from the center, like a cheap lens splitting light."""

import argparse
import colorsys
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates


def parse_center(value: str) -> tuple[float, float]:
    try:
        x, y = (float(v) for v in value.split(","))
    except ValueError:
        raise argparse.ArgumentTypeError("use two numbers, X,Y (for example 0.5,0.5)")
    return x, y


def spectral_weights(n: int) -> np.ndarray:
    """n RGB weights from violet (smallest copy) to red (largest), each channel summing to 1."""
    weights = np.array([colorsys.hsv_to_rgb(0.78 * (1 - i / (n - 1)), 1.0, 1.0) for i in range(n)])
    return weights / weights.sum(axis=0, keepdims=True)


def prism(arr: np.ndarray, amount: float, samples: int, center: tuple[float, float]) -> np.ndarray:
    h, w, _ = arr.shape
    if amount == 0:
        return arr.copy()
    cx, cy = center[0] * w, center[1] * h
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    weights = spectral_weights(samples)
    out = np.zeros_like(arr)
    for i in range(samples):
        s = 1.0 + amount * (i / (samples - 1) - 0.5)
        src_x, src_y = cx + (xx - cx) / s, cy + (yy - cy) / s
        for c in range(3):
            out[:, :, c] += weights[i, c] * map_coordinates(arr[:, :, c], [src_y, src_x], order=1, mode="nearest")
    return out


def join_pair_values(argv: list[str], options: set[str]) -> list[str]:
    """Pass each X,Y option as --opt=VALUE. Before Python 3.14, argparse reads a value that
    starts with a minus, such as -0.2,0.5, as another option rather than as the value."""
    out, i = [], 0
    while i < len(argv):
        if argv[i] in options and i + 1 < len(argv):
            out.append(f"{argv[i]}={argv[i + 1]}")
            i += 2
        else:
            out.append(argv[i])
            i += 1
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Split the image into rainbow fringes.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=0.08, help="Spread between the red and violet copies, 0 (original) to 0.1 (default: 0.08)")
    parser.add_argument("--samples", type=int, default=7, help="Number of colored copies, 3 to 16 (default: 7)")
    parser.add_argument("--center", type=parse_center, default=(0.5, 0.5), help="Lens center as X,Y fractions of the image (default: 0.5,0.5)")
    args = parser.parse_args(join_pair_values(sys.argv[1:], {"--center"}))

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 0.1:
        parser.error("--amount must be between 0 and 0.1")
    if not 3 <= args.samples <= 16:
        parser.error("--samples must be between 3 and 16")

    img = Image.open(args.input).convert("RGB")
    result = prism(np.array(img, dtype=np.float64), args.amount, args.samples, args.center)
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-prism{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved prism image to {out_path} (amount={args.amount}, samples={args.samples})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "prism",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "prism": "input-prism.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_prism.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_prism.py`).

- [ ] **Step 6: README entry.** Insert this directly before the line `### isolate-threshold`, followed by one blank line:

````markdown
### prism

Disperse the image into a rainbow of copies scaled out from the center, like a cheap lens splitting light.

```bash
python3 ./patches/prism/prism.py <input> [output] [--amount N] [--samples N] [--center X,Y]
```

Default: `--amount 0.08 --samples 7 --center 0.5,0.5`

![prism example](patches/prism/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img prism assets/mclaren.jpg patches/prism/example.jpg`, then `ls -la patches/prism/example.jpg` (expect more than 10 KB). Open it and check it matches: the center stays sharp; toward the edges the outline splits into rainbow fringes.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/prism/prism.py`, `patches/prism/requirements.txt`, `patches/prism/example.jpg`, `tests/test_prism.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(prism): add prism patch` and the trailer the build note gives.

### Task 9: bokeh

**Files:**
- Create: `patches/bokeh/bokeh.py`, `patches/bokeh/requirements.txt`, `tests/test_bokeh.py`, `patches/bokeh/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `bokeh` patch, default output suffix `-bokeh`, README entry (main group).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_bokeh.py` with exactly:

```python
"""Tests for bokeh tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _dot(path):
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[31:33, 31:33] = 255
    Image.fromarray(arr).save(path)
    return path


class TestBokeh:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        r = run_tool("bokeh", "bokeh.py", [img, out, "--radius", "5", "--shape", "disc", "--boost", "0"])
        assert r.returncode == 0, r.stderr
        assert "shape=disc" in r.stderr
        assert_valid_image(out)

    def test_zero_radius_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        assert run_tool("bokeh", "bokeh.py", [img, out, "--radius", "0"]).returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_a_bright_dot_becomes_a_hard_edged_disc(self, run_tool, tmp_path):
        img = _dot(str(tmp_path / "dot.png"))
        out = str(tmp_path / "out.png")
        assert run_tool("bokeh", "bokeh.py", [img, out, "--radius", "10", "--shape", "disc"]).returncode == 0
        lit = _pixels(out)[:, :, 0] > 20
        assert lit[32, 32 + 7] and lit[32 - 7, 32], "the disc reaches most of its radius"
        assert not lit[32, 32 + 14], "nothing beyond the radius"

    def test_bad_radius_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        assert run_tool("bokeh", "bokeh.py", [img, "--radius", "41"]).returncode == 2
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_bokeh.py`. Expected: the tests fail because `patches/bokeh/bokeh.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/bokeh/requirements.txt` with these lines:

```
Pillow
numpy
scipy
```

Create `patches/bokeh/bokeh.py` with exactly this, then run `chmod +x patches/bokeh/bokeh.py`:

```python
#!/usr/bin/env python3
"""Defocus with a hard-edged disc or hexagon, so every highlight becomes a crisp ball of light."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.signal import fftconvolve


def kernel(radius: int, shape: str) -> np.ndarray:
    yy, xx = np.mgrid[-radius:radius + 1, -radius:radius + 1].astype(np.float64)
    if shape == "hexagon":
        ax, ay = np.abs(xx), np.abs(yy)
        mask = (ay <= radius * np.sqrt(3) / 2) & (ay / np.sqrt(3) + ax <= radius)
    else:
        mask = xx ** 2 + yy ** 2 <= radius ** 2
    k = mask.astype(np.float64)
    return k / k.sum()


def bokeh(arr: np.ndarray, radius: int, shape: str, boost: float) -> np.ndarray:
    if radius == 0:
        return arr.copy()
    lum = arr @ np.array([0.299, 0.587, 0.114])
    # Work in linear light, and push the highlights so they bloom into shapes.
    lin = (arr / 255.0) ** 2.2
    lin *= (1.0 + boost * np.clip((lum - 160.0) / 95.0, 0.0, 1.0))[:, :, None]
    padded = np.pad(lin, ((radius, radius), (radius, radius), (0, 0)), mode="symmetric")
    k = kernel(radius, shape)
    out = np.stack([fftconvolve(padded[:, :, c], k, mode="valid") for c in range(3)], axis=2)
    return np.clip(out, 0.0, 1.0) ** (1 / 2.2) * 255.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Defocus with a hard-edged lens shape.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--radius", type=int, default=14, help="Blur radius in pixels, 0 (original) to 40 (default: 14)")
    parser.add_argument("--shape", choices=["disc", "hexagon"], default="hexagon", help="Lens shape (default: hexagon)")
    parser.add_argument("--boost", type=float, default=4.0, help="Extra brightness for highlights, 0 to 4 (default: 4.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0 <= args.radius <= 40:
        parser.error("--radius must be between 0 and 40")
    if not 0.0 <= args.boost <= 4.0:
        parser.error("--boost must be between 0 and 4")

    img = Image.open(args.input).convert("RGB")
    result = bokeh(np.array(img, dtype=np.float64), args.radius, args.shape, args.boost)
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-bokeh{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved bokeh image to {out_path} (radius={args.radius}, shape={args.shape}, boost={args.boost})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "bokeh",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "bokeh": "input-bokeh.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_bokeh.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_bokeh.py`).

- [ ] **Step 6: README entry.** Insert this directly before the line `### isolate-threshold`, followed by one blank line:

````markdown
### bokeh

Defocus with a hard-edged hexagon or disc, so highlights become crisp shapes of light.

```bash
python3 ./patches/bokeh/bokeh.py <input> [output] [--radius PX] [--shape disc|hexagon] [--boost N]
```

Default: `--radius 14 --shape hexagon --boost 4`

![bokeh example](patches/bokeh/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img bokeh assets/mclaren.jpg patches/bokeh/example.jpg`, then `ls -la patches/bokeh/example.jpg` (expect more than 10 KB). Open it and check it matches: the whole frame goes soft and the windscreen glints bloom; this photo has few point highlights, so it reads mainly as a lens defocus.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/bokeh/bokeh.py`, `patches/bokeh/requirements.txt`, `patches/bokeh/example.jpg`, `tests/test_bokeh.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(bokeh): add bokeh patch` and the trailer the build note gives.

### Task 10: relief

**Files:**
- Create: `patches/relief/relief.py`, `patches/relief/requirements.txt`, `tests/test_relief.py`, `patches/relief/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `relief` patch, default output suffix `-relief`, README entry (main group).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_relief.py` with exactly:

```python
"""Tests for relief tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestRelief:
    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        assert run_tool("relief", "relief.py", [img, out, "--amount", "0"]).returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_flat_gray_is_unchanged_and_a_step_is_lit_on_one_side(self, run_tool, tmp_path):
        arr = np.full((64, 64, 3), 128, dtype=np.uint8)
        arr[:, 32:] = 200
        img = str(tmp_path / "step.png")
        Image.fromarray(arr).save(img)
        out = str(tmp_path / "out.png")
        lit, shaded = str(tmp_path / "lit.png"), str(tmp_path / "shaded.png")
        assert run_tool("relief", "relief.py", [img, lit, "--angle", "180"]).returncode == 0
        assert run_tool("relief", "relief.py", [img, shaded, "--angle", "0"]).returncode == 0
        a, b = _pixels(lit), _pixels(shaded)
        assert abs(a[32, 8, 0] - 128) <= 1 and abs(a[32, 56, 0] - 200) <= 1, "flat ground keeps its color"
        # The step rises to the right, so it faces a light from the left and turns away from one on the right.
        assert a[32, 31:34, 0].max() > 230
        assert b[32, 30:33, 0].min() < 60

    def test_bad_depth_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        assert run_tool("relief", "relief.py", [img, "--depth", "0.1"]).returncode == 2
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_relief.py`. Expected: the tests fail because `patches/relief/relief.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/relief/requirements.txt` with these lines:

```
Pillow
numpy
scipy
```

Create `patches/relief/relief.py` with exactly this, then run `chmod +x patches/relief/relief.py`:

```python
#!/usr/bin/env python3
"""Light the image as a surface whose height is its brightness, embossing it while keeping its color."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage


def relief(arr: np.ndarray, amount: float, angle: float, depth: float) -> np.ndarray:
    if amount == 0:
        return arr.copy()
    lum = arr @ np.array([0.299, 0.587, 0.114])
    height = ndimage.gaussian_filter(lum / 255.0, 1.0) * depth
    # Sobel is eight times the per-pixel slope.
    gx = ndimage.sobel(height, axis=1) / 8.0
    gy = ndimage.sobel(height, axis=0) / 8.0
    norm = np.sqrt(gx ** 2 + gy ** 2 + 1.0)
    a = np.radians(angle)
    # Light from `angle` degrees (counterclockwise from the right, so 135 is top left), 45 degrees up.
    lx, ly, lz = np.cos(a) * np.cos(np.pi / 4), -np.sin(a) * np.cos(np.pi / 4), np.sin(np.pi / 4)
    shade = np.clip((-gx * lx - gy * ly + lz) / norm, 0.0, None) / lz
    return arr * (1.0 - amount + amount * shade)[:, :, None]


def main() -> None:
    parser = argparse.ArgumentParser(description="Emboss the image under a directional light.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=1.0, help="Strength, 0 (original) to 1 (default: 1.0)")
    parser.add_argument("--angle", type=float, default=135.0, help="Light direction in degrees, 135 is top left (default: 135.0)")
    parser.add_argument("--depth", type=float, default=12.0, help="Surface height, 0.5 to 20 (default: 12.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")
    if not 0.5 <= args.depth <= 20.0:
        parser.error("--depth must be between 0.5 and 20")

    img = Image.open(args.input).convert("RGB")
    result = relief(np.array(img, dtype=np.float64), args.amount, args.angle, args.depth)
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-relief{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved relief image to {out_path} (amount={args.amount}, angle={args.angle}, depth={args.depth})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "relief",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "relief": "input-relief.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_relief.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_relief.py`).

- [ ] **Step 6: README entry.** Insert this directly before the line `### isolate-threshold`, followed by one blank line:

````markdown
### relief

Light the image as a surface whose height is its brightness, embossing it under a directional light while keeping its color.

```bash
python3 ./patches/relief/relief.py <input> [output] [--amount N] [--angle DEG] [--depth N]
```

Default: `--amount 1 --angle 135 --depth 12`

![relief example](patches/relief/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img relief assets/mclaren.jpg patches/relief/example.jpg`, then `ls -la patches/relief/example.jpg` (expect more than 10 KB). Open it and check it matches: the car looks pressed from sheet metal: panel gaps are grooves and highlights stand up, lit from the top left.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/relief/relief.py`, `patches/relief/requirements.txt`, `patches/relief/example.jpg`, `tests/test_relief.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(relief): add relief patch` and the trailer the build note gives.

### Task 11: input checks for shatter, prism, bokeh, relief

**Files:**
- Modify: `tests/test_new_patch_inputs.py`

- [ ] **Step 1: Add the milestone's patches.** In `tests/test_new_patch_inputs.py`, add these lines as the last entries of `NEW_PATCHES`, directly before its closing `]`:

```python
    ("shatter", "shatter"),
    ("prism", "prism"),
    ("bokeh", "bokeh"),
    ("relief", "relief"),
```

- [ ] **Step 2: Run the input checks.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_new_patch_inputs.py`. Expected: all pass (36 new checks). If a patch fails a check, fix the patch (not the check) and note the change in the closing report.

- [ ] **Step 3: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: no failures.

- [ ] **Step 4: Commit.** Stage `tests/test_new_patch_inputs.py` (and any patch fixed in Step 2) by path, and commit with the subject `test(new-patches): input edge cases for shatter, prism, bokeh, relief` and the trailer the build note gives.

## M3: Color and craft

**Start of milestone:** run `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests` and record the result as the baseline.

### Task 12: solarize

**Files:**
- Create: `patches/solarize/solarize.py`, `patches/solarize/requirements.txt`, `tests/test_solarize.py`, `patches/solarize/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `solarize` patch, default output suffix `-solar`, README entry (color patch).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_solarize.py` with exactly:

```python
"""Tests for solarize tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestSolarize:
    def test_explicit_output_lightness(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        r = run_tool("solarize", "solarize.py", [img, out, "--folds", "2", "--mode", "lightness"])
        assert r.returncode == 0, r.stderr
        assert "mode=lightness" in r.stderr
        assert_valid_image(out)

    def test_zero_folds_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        for mode in ("rgb", "lightness"):
            out = str(tmp_path / f"same-{mode}.png")
            assert run_tool("solarize", "solarize.py", [img, out, "--folds", "0", "--mode", mode]).returncode == 0
            assert np.array_equal(_pixels(out), _pixels(img)), mode

    def test_one_fold_turns_white_black_and_keeps_mid_gray_bright(self, run_tool, tmp_path):
        arr = np.zeros((4, 3, 3), dtype=np.uint8)
        arr[:, 0], arr[:, 1], arr[:, 2] = 0, 128, 255
        img = str(tmp_path / "steps.png")
        Image.fromarray(arr).save(img)
        out = str(tmp_path / "out.png")
        assert run_tool("solarize", "solarize.py", [img, out, "--folds", "1"]).returncode == 0
        px = _pixels(out)[0, :, 0]
        assert px[0] == 0 and px[2] == 0 and px[1] > 250

    def test_bad_folds_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        assert run_tool("solarize", "solarize.py", [img, "--folds", "9"]).returncode == 2
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_solarize.py`. Expected: the tests fail because `patches/solarize/solarize.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/solarize/requirements.txt` with these lines:

```
Pillow
numpy
```

Create `patches/solarize/solarize.py` with exactly this, then run `chmod +x patches/solarize/solarize.py`:

```python
#!/usr/bin/env python3
"""Fold the tone curve so bright tones turn back toward dark, like the Sabattier darkroom effect."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def fold(values: np.ndarray, folds: float) -> np.ndarray:
    """Triangle-wave tone curve over 0-255. folds 0 is the identity; each fold turns the curve back once more."""
    t = values / 255.0 * (folds + 1.0)
    phase = t % 2.0
    return np.where(phase <= 1.0, phase, 2.0 - phase) * 255.0


def solarize(img: Image.Image, folds: float, mode: str) -> Image.Image:
    if folds == 0:
        return img.copy()
    if mode == "lightness":
        lab = np.array(img.convert("LAB"))
        lab[:, :, 0] = np.clip(np.rint(fold(lab[:, :, 0].astype(np.float64), folds)), 0, 255).astype(np.uint8)
        # Image.merge("LAB", ...) corrupts the image on Pillow 12; build the LAB image directly.
        return Image.fromarray(lab, "LAB").convert("RGB")
    arr = np.array(img, dtype=np.float64)
    return Image.fromarray(np.clip(np.rint(fold(arr, folds)), 0, 255).astype(np.uint8))


def main() -> None:
    parser = argparse.ArgumentParser(description="Solarize the image by folding its tone curve.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--folds", type=float, default=1.5, help="How many times the tone curve folds back, 0 (original) to 8 (default: 1.5)")
    parser.add_argument("--mode", choices=["rgb", "lightness"], default="rgb", help="Fold each RGB channel, or only lightness, keeping hue (default: rgb)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.folds <= 8.0:
        parser.error("--folds must be between 0 and 8")

    img = Image.open(args.input).convert("RGB")
    result_img = solarize(img, args.folds, args.mode)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-solar{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved solarized image to {out_path} (folds={args.folds}, mode={args.mode})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "solarize",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "solarize": "input-solar.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_solarize.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_solarize.py`).

- [ ] **Step 6: README entry.** Insert this directly before the line `### dot-halftone`, followed by one blank line:

````markdown
### solarize

Fold the tone curve so bright tones turn back toward dark, like the Sabattier darkroom effect. More folds give psychedelic bands.

```bash
python3 ./patches/solarize/solarize.py <input> [output] [--folds N] [--mode rgb|lightness]
```

Default: `--folds 1.5 --mode rgb`

![solarize example](patches/solarize/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img solarize assets/mclaren.jpg patches/solarize/example.jpg`, then `ls -la patches/solarize/example.jpg` (expect more than 10 KB). Open it and check it matches: the orange body turns green and the whites fold to dark with glowing rims; the lawn turns violet.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/solarize/solarize.py`, `patches/solarize/requirements.txt`, `patches/solarize/example.jpg`, `tests/test_solarize.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(solarize): add solarize patch` and the trailer the build note gives.

### Task 13: hue-wave

**Files:**
- Create: `patches/hue-wave/hue-wave.py`, `patches/hue-wave/requirements.txt`, `tests/test_hue_wave.py`, `patches/hue-wave/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `hue-wave` patch, default output suffix `-huewave`, README entry (color patch).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_hue_wave.py` with exactly:

```python
"""Tests for hue-wave tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestHueWave:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        for by in ("x", "y", "radius"):
            out = str(tmp_path / f"out-{by}.png")
            r = run_tool("hue-wave", "hue-wave.py", [img, out, "--amount", "180", "--by", by])
            assert r.returncode == 0, r.stderr
            assert_valid_image(out)

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        assert run_tool("hue-wave", "hue-wave.py", [img, out, "--amount", "0"]).returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_grays_stay_gray_and_color_shifts(self, run_tool, tmp_path):
        arr = np.zeros((8, 16, 3), dtype=np.uint8)
        arr[:, :8] = 128
        arr[:, 8:] = (200, 60, 20)
        img = str(tmp_path / "mix.png")
        Image.fromarray(arr).save(img)
        out = str(tmp_path / "out.png")
        assert run_tool("hue-wave", "hue-wave.py", [img, out, "--amount", "180"]).returncode == 0
        px = _pixels(out)
        assert (px[:, :8].max(axis=2) - px[:, :8].min(axis=2)).max() <= 2, "gray has no hue to turn"
        assert np.abs(px[:, 8:] - arr[:, 8:].astype(np.int64)).max() > 40, "the orange turns"

    def test_bad_amount_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        assert run_tool("hue-wave", "hue-wave.py", [img, "--amount", "800"]).returncode == 2
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_hue_wave.py`. Expected: the tests fail because `patches/hue-wave/hue-wave.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/hue-wave/requirements.txt` with these lines:

```
Pillow
numpy
```

Create `patches/hue-wave/hue-wave.py` with exactly this, then run `chmod +x patches/hue-wave/hue-wave.py`:

```python
#!/usr/bin/env python3
"""Rotate each pixel's hue by an amount set by its brightness or its position, for a flowing rainbow."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def hue_wave(img: Image.Image, amount: float, by: str) -> Image.Image:
    if amount == 0:
        return img.copy()
    hsv = np.array(img.convert("HSV"))
    h, w = hsv.shape[:2]
    if by == "brightness":
        driver = np.array(img.convert("L"), dtype=np.float64) / 255.0
    else:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
        if by == "x":
            driver = xx / max(w - 1, 1)
        elif by == "y":
            driver = yy / max(h - 1, 1)
        else:
            driver = np.hypot(xx - (w - 1) / 2.0, yy - (h - 1) / 2.0) / max(np.hypot(w, h) / 2.0, 1.0)
    shifted = hsv[:, :, 0].astype(np.float64) + amount / 360.0 * 256.0 * driver
    hsv[:, :, 0] = (np.rint(shifted) % 256).astype(np.uint8)
    # Build the HSV image directly; Image.merge of single bands is unreliable on Pillow 12.
    return Image.fromarray(hsv, "HSV").convert("RGB")


def main() -> None:
    parser = argparse.ArgumentParser(description="Shift hue across the image in a rainbow wave.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=360.0, help="Largest hue shift in degrees, 0 (original) to 720 (default: 360.0)")
    parser.add_argument("--by", choices=["brightness", "x", "y", "radius"], default="brightness", help="What sets each pixel's shift (default: brightness)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 720.0:
        parser.error("--amount must be between 0 and 720")

    img = Image.open(args.input).convert("RGB")
    result_img = hue_wave(img, args.amount, args.by)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-huewave{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved hue-wave image to {out_path} (amount={args.amount}, by={args.by})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "hue-wave",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "hue-wave": "input-huewave.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_hue_wave.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_hue_wave.py`).

- [ ] **Step 6: README entry.** Insert this directly before the line `### dot-halftone`, followed by one blank line:

````markdown
### hue-wave

Rotate each pixel's hue by an amount set by its brightness or its position, for a flowing rainbow. Grays stay gray.

```bash
python3 ./patches/hue-wave/hue-wave.py <input> [output] [--amount DEG] [--by brightness|x|y|radius]
```

Default: `--amount 360 --by brightness`

![hue-wave example](patches/hue-wave/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img hue-wave assets/mclaren.jpg patches/hue-wave/example.jpg`, then `ls -la patches/hue-wave/example.jpg` (expect more than 10 KB). Open it and check it matches: shadows, mid-tones and highlights each turn a different hue: green and cyan body, magenta highlights.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/hue-wave/hue-wave.py`, `patches/hue-wave/requirements.txt`, `patches/hue-wave/example.jpg`, `tests/test_hue_wave.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(hue-wave): add hue-wave patch` and the trailer the build note gives.

### Task 14: papercut

**Files:**
- Create: `patches/papercut/papercut.py`, `patches/papercut/requirements.txt`, `tests/test_papercut.py`, `patches/papercut/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `papercut` patch, default output suffix `-papercut`, README entry (main group).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_papercut.py` with exactly:

```python
"""Tests for papercut tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestPapercut:
    def test_no_shadow_gives_at_most_layers_colors(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "flat.png")
        assert run_tool("papercut", "papercut.py", [img, out, "--layers", "4", "--shadow", "0"]).returncode == 0
        colors = np.unique(_pixels(out).reshape(-1, 3), axis=0)
        assert len(colors) <= 4

    def test_shadow_darkens_below_a_raised_layer(self, run_tool, tmp_path):
        arr = np.full((64, 64, 3), 40, dtype=np.uint8)
        arr[16:32, 16:32] = 230
        img = str(tmp_path / "block.png")
        Image.fromarray(arr).save(img)
        flat, shaded = str(tmp_path / "flat.png"), str(tmp_path / "shaded.png")
        assert run_tool("papercut", "papercut.py", [img, flat, "--layers", "2", "--shadow", "0", "--blur", "0"]).returncode == 0
        assert run_tool("papercut", "papercut.py", [img, shaded, "--layers", "2", "--shadow", "6", "--blur", "0"]).returncode == 0
        assert _pixels(shaded)[36, 30].sum() < _pixels(flat)[36, 30].sum(), "the shadow falls below and right of the light square"

    def test_bad_layers_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        assert run_tool("papercut", "papercut.py", [img, "--layers", "1"]).returncode == 2
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_papercut.py`. Expected: the tests fail because `patches/papercut/papercut.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/papercut/requirements.txt` with these lines:

```
Pillow
numpy
scipy
```

Create `patches/papercut/papercut.py` with exactly this, then run `chmod +x patches/papercut/papercut.py`:

```python
#!/usr/bin/env python3
"""Cut the image into paper layers by brightness, each a flat color casting a soft shadow on the layer below."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage


def shift_down_right(mask: np.ndarray, px: int) -> np.ndarray:
    out = np.zeros_like(mask)
    h, w = mask.shape
    if px < h and px < w:
        out[px:, px:] = mask[:h - px, :w - px]
    return out


def papercut(arr: np.ndarray, layers: int, shadow: int, blur: float) -> np.ndarray:
    h, w, _ = arr.shape
    lum = ndimage.gaussian_filter(arr @ np.array([0.299, 0.587, 0.114]), blur)
    band = np.clip((lum * layers / 256.0).astype(int), 0, layers - 1)
    flat = np.empty_like(arr)
    counts = np.bincount(band.ravel(), minlength=layers)
    for c in range(3):
        sums = np.bincount(band.ravel(), weights=arr[:, :, c].ravel(), minlength=layers)
        flat[:, :, c] = (sums / np.maximum(counts, 1))[band]
    # Each lighter layer sits on top and casts a soft shadow onto the layers below it.
    dark = np.zeros((h, w))
    if shadow > 0:
        for k in range(1, layers):
            top = band >= k
            cast = ndimage.gaussian_filter(shift_down_right(top, shadow).astype(np.float64), shadow / 2.0)
            dark += cast * ~top
    return flat * (1.0 - 0.45 * np.clip(dark, 0.0, 1.0))[:, :, None]


def main() -> None:
    parser = argparse.ArgumentParser(description="Turn the image into layered cut paper.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--layers", type=int, default=6, help="Number of paper layers, 2 to 12 (default: 6)")
    parser.add_argument("--shadow", type=int, default=6, help="Shadow offset and softness in pixels, 0 for none (default: 6)")
    parser.add_argument("--blur", type=float, default=3.0, help="Edge smoothness of the cuts (default: 3.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 2 <= args.layers <= 12:
        parser.error("--layers must be between 2 and 12")
    if args.shadow < 0:
        parser.error("--shadow must be 0 or more")
    if args.blur < 0:
        parser.error("--blur must be 0 or more")

    img = Image.open(args.input).convert("RGB")
    result = papercut(np.array(img, dtype=np.float64), args.layers, args.shadow, args.blur)
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-papercut{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved papercut image to {out_path} (layers={args.layers}, shadow={args.shadow}, blur={args.blur})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "papercut",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "papercut": "input-papercut.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_papercut.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_papercut.py`).

- [ ] **Step 6: README entry.** Insert this directly before the line `### isolate-threshold`, followed by one blank line:

````markdown
### papercut

Cut the image into paper layers by brightness, each a flat color casting a soft shadow onto the layer below.

```bash
python3 ./patches/papercut/papercut.py <input> [output] [--layers N] [--shadow PX] [--blur N]
```

Default: `--layers 6 --shadow 6 --blur 3`

![papercut example](patches/papercut/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img papercut assets/mclaren.jpg patches/papercut/example.jpg`, then `ls -la patches/papercut/example.jpg` (expect more than 10 KB). Open it and check it matches: a layered paper diorama in a few flat colors with soft shadows under every cut edge.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/papercut/papercut.py`, `patches/papercut/requirements.txt`, `patches/papercut/example.jpg`, `tests/test_papercut.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(papercut): add papercut patch` and the trailer the build note gives.

### Task 15: weave

**Files:**
- Create: `patches/weave/weave.py`, `patches/weave/requirements.txt`, `tests/test_weave.py`, `patches/weave/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `weave` patch, default output suffix `-weave`, README entry (main group).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_weave.py` with exactly:

```python
"""Tests for weave tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestWeave:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        r = run_tool("weave", "weave.py", [img, out, "--strip", "8", "--cross", "negative", "--shade", "0.2", "--gap", "1"])
        assert r.returncode == 0, r.stderr
        assert "cross=negative" in r.stderr
        assert_valid_image(out)

    def test_same_without_shade_or_gap_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        assert run_tool("weave", "weave.py", [img, out, "--cross", "same", "--shade", "0", "--gap", "0"]).returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_crossing_squares_show_the_mirror(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        assert run_tool("weave", "weave.py", [img, out, "--strip", "16", "--shade", "0", "--gap", "0"]).returncode == 0
        a, b = _pixels(img), _pixels(out)
        assert np.array_equal(b[0:16, 0:16], a[0:16, 0:16]), "over squares show the image"
        assert np.array_equal(b[0:16, 16:32], a[0:16, ::-1][:, 16:32]), "under squares show the mirror"

    def test_gap_must_be_smaller_than_strip(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        assert run_tool("weave", "weave.py", [img, "--strip", "8", "--gap", "8"]).returncode == 2
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_weave.py`. Expected: the tests fail because `patches/weave/weave.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/weave/requirements.txt` with these lines:

```
Pillow
numpy
```

Create `patches/weave/weave.py` with exactly this, then run `chmod +x patches/weave/weave.py`:

```python
#!/usr/bin/env python3
"""Cut the image into ribbons and weave them over and under, with a mirrored or negative copy running across."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def weave(arr: np.ndarray, strip: int, cross: str, shade: float, gap: int) -> np.ndarray:
    h, w, _ = arr.shape
    if cross == "mirror":
        weft = arr[:, ::-1]
    elif cross == "negative":
        weft = 255.0 - arr
    else:
        weft = arr
    yy, xx = np.mgrid[0:h, 0:w]
    over = ((xx // strip) + (yy // strip)) % 2 == 0
    out = np.where(over[:, :, None], arr, weft).astype(np.float64)
    # Ribbons are rounded: darker toward their edges across the ribbon.
    across = np.where(over, xx % strip, yy % strip)
    out *= (1.0 - shade * (1.0 - np.sin(np.pi * (across + 0.5) / strip)))[:, :, None]
    # Dark slits between neighboring ribbons.
    slit = np.where(over, xx % strip < gap, yy % strip < gap)
    out[slit] *= 0.4
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Weave the image into ribbons.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--strip", type=int, default=24, help="Ribbon width in pixels, 4 to 200 (default: 24)")
    parser.add_argument("--cross", choices=["mirror", "negative", "same"], default="mirror", help="What the crossing ribbons show (default: mirror)")
    parser.add_argument("--shade", type=float, default=0.4, help="Ribbon shading, 0 to 1 (default: 0.4)")
    parser.add_argument("--gap", type=int, default=2, help="Slit between ribbons in pixels (default: 2)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 4 <= args.strip <= 200:
        parser.error("--strip must be between 4 and 200")
    if not 0.0 <= args.shade <= 1.0:
        parser.error("--shade must be between 0 and 1")
    if not 0 <= args.gap < args.strip:
        parser.error("--gap must be 0 or more and smaller than --strip")

    img = Image.open(args.input).convert("RGB")
    result = weave(np.array(img, dtype=np.float64), args.strip, args.cross, args.shade, args.gap)
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-weave{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved woven image to {out_path} (strip={args.strip}, cross={args.cross}, shade={args.shade}, gap={args.gap})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "weave",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "weave": "input-weave.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_weave.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_weave.py`).

- [ ] **Step 6: README entry.** Insert this directly before the line `### isolate-threshold`, followed by one blank line:

````markdown
### weave

Cut the image into ribbons and weave them over and under, with a mirrored or negative copy running across.

```bash
python3 ./patches/weave/weave.py <input> [output] [--strip PX] [--cross mirror|negative|same] [--shade N] [--gap PX]
```

Default: `--strip 24 --cross mirror --shade 0.4 --gap 2`

![weave example](patches/weave/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img weave assets/mclaren.jpg patches/weave/example.jpg`, then `ls -la patches/weave/example.jpg` (expect more than 10 KB). Open it and check it matches: a basket of shaded ribbons; every other square shows the mirrored car.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/weave/weave.py`, `patches/weave/requirements.txt`, `patches/weave/example.jpg`, `tests/test_weave.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(weave): add weave patch` and the trailer the build note gives.

### Task 16: input checks for solarize, hue-wave, papercut, weave

**Files:**
- Modify: `tests/test_new_patch_inputs.py`

- [ ] **Step 1: Add the milestone's patches.** In `tests/test_new_patch_inputs.py`, add these lines as the last entries of `NEW_PATCHES`, directly before its closing `]`:

```python
    ("solarize", "solar"),
    ("hue-wave", "huewave"),
    ("papercut", "papercut"),
    ("weave", "weave"),
```

- [ ] **Step 2: Run the input checks.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_new_patch_inputs.py`. Expected: all pass (36 new checks). If a patch fails a check, fix the patch (not the check) and note the change in the closing report.

- [ ] **Step 3: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: no failures.

- [ ] **Step 4: Commit.** Stage `tests/test_new_patch_inputs.py` (and any patch fixed in Step 2) by path, and commit with the subject `test(new-patches): input edge cases for solarize, hue-wave, papercut, weave` and the trailer the build note gives.

## M4: Drawing and growth

**Start of milestone:** run `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests` and record the result as the baseline.

### Task 17: ridgeline

**Files:**
- Create: `patches/ridgeline/ridgeline.py`, `patches/ridgeline/requirements.txt`, `tests/test_ridgeline.py`, `patches/ridgeline/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `ridgeline` patch, default output suffix `-ridge`, README entry (drawing patch).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_ridgeline.py` with exactly:

```python
"""Tests for ridgeline tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestRidgeline:
    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        assert run_tool("ridgeline", "ridgeline.py", [img, out, "--amount", "0"]).returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_lines_in_the_chosen_color_on_black(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        assert run_tool("ridgeline", "ridgeline.py", [img, out, "--lines", "20", "--width", "1", "--color", "#00ff00"]).returncode == 0
        colors = {tuple(c) for c in np.unique(_pixels(out).reshape(-1, 3), axis=0)}
        assert (0, 0, 0) in colors and (0, 255, 0) in colors
        assert all(c[0] == 0 and c[2] == 0 for c in colors), "only black and shades of the line color"

    def test_bad_color_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("ridgeline", "ridgeline.py", [img, "--color", "#12345z"])
        assert r.returncode == 2
        assert "not a color" in r.stderr
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_ridgeline.py`. Expected: the tests fail because `patches/ridgeline/ridgeline.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/ridgeline/requirements.txt` with these lines:

```
Pillow
numpy
scipy
```

Create `patches/ridgeline/ridgeline.py` with exactly this, then run `chmod +x patches/ridgeline/ridgeline.py`:

```python
#!/usr/bin/env python3
"""Draw the image as stacked lines lifted by brightness, hiding the lines behind, like the Unknown Pleasures cover."""

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageColor, ImageDraw
from scipy import ndimage


def ridgeline(arr: np.ndarray, lines: int, height: float, width: int, color: tuple, amount: float) -> np.ndarray:
    if amount == 0:
        return arr.copy()
    h, w, _ = arr.shape
    lum = ndimage.gaussian_filter(arr @ np.array([0.299, 0.587, 0.114]), 1.5)
    canvas = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    xs = np.arange(w, dtype=np.float64)
    # Back to front: each ridge's filled underside hides the ridges behind it.
    for y0 in np.unique(np.linspace(0, h - 1, max(1, min(lines, h))).round().astype(int)):
        profile = y0 - height * lum[y0] / 255.0
        points = list(zip(xs.tolist(), profile.tolist()))
        draw.polygon(points + [(w - 1, h - 1), (0, h - 1)], fill=(0, 0, 0))
        if w > 1:
            draw.line(points, fill=color, width=width)
        else:
            draw.point(points, fill=color)
    drawn = np.array(canvas, dtype=np.float64)
    return arr * (1.0 - amount) + drawn * amount


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw the image as ridge lines.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--lines", type=int, default=60, help="Number of ridge lines, 20 to 300 (default: 60)")
    parser.add_argument("--height", type=float, default=50.0, help="How far brightness lifts a line, in pixels (default: 50.0)")
    parser.add_argument("--width", type=int, default=2, help="Line width in pixels (default: 2)")
    parser.add_argument("--color", default="#ec4899", help="Line color (default: #ec4899)")
    parser.add_argument("--amount", type=float, default=1.0, help="Fade from the image to the ridges, 0 (original) to 1 (default: 1.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 20 <= args.lines <= 300:
        parser.error("--lines must be between 20 and 300")
    if args.height < 0:
        parser.error("--height must be 0 or more")
    if args.width < 1:
        parser.error("--width must be 1 or more")
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")
    try:
        color = ImageColor.getrgb(args.color)[:3]
    except ValueError:
        parser.error(f"--color is not a color: '{args.color}'")

    img = Image.open(args.input).convert("RGB")
    result = ridgeline(np.array(img, dtype=np.float64), args.lines, args.height, args.width, color, args.amount)
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-ridge{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved ridgeline image to {out_path} (lines={args.lines}, height={args.height}, amount={args.amount})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "ridgeline",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "ridgeline": "input-ridge.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_ridgeline.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_ridgeline.py`).

- [ ] **Step 6: README entry.** Insert this directly after the line `![stipple example](patches/stipple/example.jpg)` (after any drawing patch this plan already added there), followed by one blank line:

````markdown
### ridgeline

Draw the image as stacked lines lifted by brightness, hiding the lines behind, like the *Unknown Pleasures* cover.

```bash
python3 ./patches/ridgeline/ridgeline.py <input> [output] [--lines N] [--height PX] [--width PX] [--color C] [--amount N]
```

Default: `--lines 60 --height 50 --width 2 --color "#ec4899" --amount 1`

![ridgeline example](patches/ridgeline/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img ridgeline assets/mclaren.jpg patches/ridgeline/example.jpg`, then `ls -la patches/ridgeline/example.jpg` (expect more than 10 KB). Open it and check it matches: pink ridge lines on black that rise into the car's silhouette.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/ridgeline/ridgeline.py`, `patches/ridgeline/requirements.txt`, `patches/ridgeline/example.jpg`, `tests/test_ridgeline.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(ridgeline): add ridgeline patch` and the trailer the build note gives.

### Task 18: sketch

**Files:**
- Create: `patches/sketch/sketch.py`, `patches/sketch/requirements.txt`, `tests/test_sketch.py`, `patches/sketch/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `sketch` patch, default output suffix `-sketch`, README entry (drawing patch).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_sketch.py` with exactly:

```python
"""Tests for sketch tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestSketch:
    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        assert run_tool("sketch", "sketch.py", [img, out, "--amount", "0"]).returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_flat_areas_are_paper_and_edges_are_dark(self, run_tool, tmp_path):
        arr = np.full((64, 64, 3), 150, dtype=np.uint8)
        arr[:, 32:] = 60
        img = str(tmp_path / "edge.png")
        Image.fromarray(arr).save(img)
        out = str(tmp_path / "out.png")
        assert run_tool("sketch", "sketch.py", [img, out, "--radius", "4"]).returncode == 0
        px = _pixels(out)
        assert px[32, 4].min() > 240, "flat ground is white paper"
        assert px[32, 30:34].min() < 200, "the edge is drawn"
        assert (px.max(axis=2) - px.min(axis=2)).max() == 0, "graphite is gray"

    def test_bad_radius_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        assert run_tool("sketch", "sketch.py", [img, "--radius", "0.5"]).returncode == 2
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_sketch.py`. Expected: the tests fail because `patches/sketch/sketch.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/sketch/requirements.txt` with these lines:

```
Pillow
numpy
scipy
```

Create `patches/sketch/sketch.py` with exactly this, then run `chmod +x patches/sketch/sketch.py`:

```python
#!/usr/bin/env python3
"""A pencil drawing, made by color-dodging the image with its own blurred negative."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage


def sketch(arr: np.ndarray, radius: float, amount: float) -> np.ndarray:
    if amount == 0:
        return arr.copy()
    gray = arr @ np.array([0.299, 0.587, 0.114])
    blurred_negative = ndimage.gaussian_filter(255.0 - gray, radius)
    dodge = np.clip(gray * 255.0 / np.maximum(255.0 - blurred_negative, 1.0), 0.0, 255.0)
    # A power curve deepens the graphite.
    drawn = 255.0 * (dodge / 255.0) ** 2.5
    return arr * (1.0 - amount) + drawn[:, :, None] * amount


def main() -> None:
    parser = argparse.ArgumentParser(description="Turn the image into a pencil sketch.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--radius", type=float, default=8.0, help="Stroke softness, the blur sigma, 1 to 30 (default: 8.0)")
    parser.add_argument("--amount", type=float, default=1.0, help="Fade from the image to the sketch, 0 (original) to 1 (default: 1.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 1.0 <= args.radius <= 30.0:
        parser.error("--radius must be between 1 and 30")
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")

    img = Image.open(args.input).convert("RGB")
    result = sketch(np.array(img, dtype=np.float64), args.radius, args.amount)
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-sketch{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved sketch image to {out_path} (radius={args.radius}, amount={args.amount})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "sketch",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "sketch": "input-sketch.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_sketch.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_sketch.py`).

- [ ] **Step 6: README entry.** Insert this directly after the line `![stipple example](patches/stipple/example.jpg)` (after any drawing patch this plan already added there), followed by one blank line:

````markdown
### sketch

A pencil drawing: color-dodge the image with its own blurred negative for graphite lines on white paper.

```bash
python3 ./patches/sketch/sketch.py <input> [output] [--radius N] [--amount N]
```

Default: `--radius 8 --amount 1`

![sketch example](patches/sketch/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img sketch assets/mclaren.jpg patches/sketch/example.jpg`, then `ls -la patches/sketch/example.jpg` (expect more than 10 KB). Open it and check it matches: white paper with gray graphite lines tracing the car's outline and panels.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/sketch/sketch.py`, `patches/sketch/requirements.txt`, `patches/sketch/example.jpg`, `tests/test_sketch.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(sketch): add sketch patch` and the trailer the build note gives.

### Task 19: reaction-diffusion

**Files:**
- Create: `patches/reaction-diffusion/reaction-diffusion.py`, `patches/reaction-diffusion/requirements.txt`, `tests/test_reaction_diffusion.py`, `patches/reaction-diffusion/example.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md`

**Interfaces:**
- Produces: the `reaction-diffusion` patch, default output suffix `-rd`, README entry (main group).

- [ ] **Step 1: Write the failing tests.** Create `tests/test_reaction_diffusion.py` with exactly:

```python
"""Tests for reaction-diffusion tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path):
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestReactionDiffusion:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        r = run_tool("reaction-diffusion", "reaction-diffusion.py", [img, out, "--steps", "200", "--scale", "1", "--amount", "0.5", "--seed", "4"])
        assert r.returncode == 0, r.stderr
        assert "seed=4" in r.stderr
        assert_valid_image(out)

    def test_zero_steps_or_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        for opts in (["--steps", "0"], ["--amount", "0"]):
            out = str(tmp_path / f"same{opts[0]}.png")
            assert run_tool("reaction-diffusion", "reaction-diffusion.py", [img, out] + opts).returncode == 0
            assert np.array_equal(_pixels(out), _pixels(img)), opts

    def test_pattern_only_darkens_and_is_reproducible(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        a, b = str(tmp_path / "a.png"), str(tmp_path / "b.png")
        assert run_tool("reaction-diffusion", "reaction-diffusion.py", [img, a, "--steps", "300"]).returncode == 0
        assert run_tool("reaction-diffusion", "reaction-diffusion.py", [img, b, "--steps", "300"]).returncode == 0
        pa = _pixels(a)
        assert np.array_equal(pa, _pixels(b))
        assert (pa <= _pixels(img)).all()
        assert (pa < _pixels(img)).any()

    def test_bad_steps_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        assert run_tool("reaction-diffusion", "reaction-diffusion.py", [img, "--steps", "6000"]).returncode == 2
```

- [ ] **Step 2: Run them and confirm they fail.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_reaction_diffusion.py`. Expected: the tests fail because `patches/reaction-diffusion/reaction-diffusion.py` does not exist (`test_no_args` may already pass, since a missing script also exits non-zero).

- [ ] **Step 3: Write the patch.** Create `patches/reaction-diffusion/requirements.txt` with these lines:

```
Pillow
numpy
scipy
```

Create `patches/reaction-diffusion/reaction-diffusion.py` with exactly this, then run `chmod +x patches/reaction-diffusion/reaction-diffusion.py`:

```python
#!/usr/bin/env python3
"""Grow Gray-Scott Turing patterns across the image, with the feed rate set by brightness."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

DU, DV, KILL = 0.16, 0.08, 0.06


def grow(lum: np.ndarray, steps: int, seed: int) -> np.ndarray:
    """Run Gray-Scott on a brightness map (0 to 1) and return V, the pattern chemical."""
    rng = np.random.default_rng(seed)
    h, w = lum.shape
    u = np.ones((h, w))
    v = np.zeros((h, w))
    patches = rng.random((h, w)) < 0.04
    v[patches] = 0.5
    u[patches] = 0.5
    # Bright areas feed faster (spots), dark areas slower (worms and mazes).
    feed = 0.022 + 0.035 * lum
    for _ in range(steps):
        uvv = u * v * v
        u += DU * ndimage.laplace(u, mode="wrap") - uvv + feed * (1.0 - u)
        v += DV * ndimage.laplace(v, mode="wrap") + uvv - (feed + KILL) * v
    return v


def reaction_diffusion(img: Image.Image, steps: int, scale: int, amount: float, seed: int) -> np.ndarray:
    arr = np.array(img, dtype=np.float64)
    if steps == 0 or amount == 0:
        return arr.copy()
    w, h = img.size
    small = img.convert("L").resize((max(1, w // scale), max(1, h // scale)), Image.BOX)
    v = grow(np.array(small, dtype=np.float64) / 255.0, steps, seed)
    span = v.max() - v.min()
    norm = (v - v.min()) / span if span > 0 else np.zeros_like(v)
    pattern = Image.fromarray((norm * 255.0).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    mask = np.array(pattern, dtype=np.float64) / 255.0
    return arr * (1.0 - amount * mask)[:, :, None]


def main() -> None:
    parser = argparse.ArgumentParser(description="Grow reaction-diffusion patterns across the image.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--steps", type=int, default=1500, help="Simulation steps, 0 (original) to 5000 (default: 1500)")
    parser.add_argument("--scale", type=int, default=2, help="Downsample factor that sets the pattern size, 1 to 4 (default: 2)")
    parser.add_argument("--amount", type=float, default=1.0, help="Pattern strength, 0 (original) to 1 (default: 1.0)")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for where patterns start (default: 0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0 <= args.steps <= 5000:
        parser.error("--steps must be between 0 and 5000")
    if not 1 <= args.scale <= 4:
        parser.error("--scale must be between 1 and 4")
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")

    img = Image.open(args.input).convert("RGB")
    result = reaction_diffusion(img, args.steps, args.scale, args.amount, args.seed)
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-rd{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved reaction-diffusion image to {out_path} (steps={args.steps}, scale={args.scale}, amount={args.amount}, seed={args.seed})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Register it.** In `tests/test_op_cli.py`, add the line `    "reaction-diffusion",` as the last entry of `ALL_PATCHES`, directly before its closing `]`. Also add `    "reaction-diffusion": "input-rd.png",` to `DEFAULT_NAMES` in `tests/test_conventions.py`, in alphabetical order; the shared conventions (default name, explicit output, missing input, no arguments) are tested there, so this patch's own test file does not repeat them.

- [ ] **Step 5: Run the tests.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_reaction_diffusion.py tests/test_op_cli.py`. Expected: all pass (7 in `tests/test_reaction_diffusion.py`).

- [ ] **Step 6: README entry.** Insert this directly before the line `### isolate-threshold`, followed by one blank line:

````markdown
### reaction-diffusion

Grow Gray-Scott Turing patterns across the image, with the feed rate set by brightness: spots in bright areas, mazes in dark ones.

```bash
python3 ./patches/reaction-diffusion/reaction-diffusion.py <input> [output] [--steps N] [--scale N] [--amount N] [--seed N]
```

Default: `--steps 1500 --scale 2 --amount 1 --seed 0`

![reaction-diffusion example](patches/reaction-diffusion/example.jpg)
````

- [ ] **Step 7: Generate the example.** `PATH="/tmp/opimg-venv/bin:$PATH" paced ./op-img reaction-diffusion assets/mclaren.jpg patches/reaction-diffusion/example.jpg`, then `ls -la patches/reaction-diffusion/example.jpg` (expect more than 10 KB). Open it and check it matches: the paint fills with a labyrinth of dark worms; the lawn becomes a dense maze.

- [ ] **Step 8: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: the previous count plus 7, no failures.

- [ ] **Step 9: Commit.** Stage `patches/reaction-diffusion/reaction-diffusion.py`, `patches/reaction-diffusion/requirements.txt`, `patches/reaction-diffusion/example.jpg`, `tests/test_reaction_diffusion.py`, `tests/test_op_cli.py` and `README.md` by path, and commit with the subject `feat(reaction-diffusion): add reaction-diffusion patch` and the trailer the build note gives.

### Task 20: input checks for ridgeline, sketch, reaction-diffusion

**Files:**
- Modify: `tests/test_new_patch_inputs.py`

- [ ] **Step 1: Add the milestone's patches.** In `tests/test_new_patch_inputs.py`, add these lines as the last entries of `NEW_PATCHES`, directly before its closing `]`:

```python
    ("ridgeline", "ridge"),
    ("sketch", "sketch"),
    ("reaction-diffusion", "rd"),
```

- [ ] **Step 2: Run the input checks.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests/test_new_patch_inputs.py`. Expected: all pass (27 new checks). If a patch fails a check, fix the patch (not the check) and note the change in the closing report.

- [ ] **Step 3: Run the full suite.** `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests`. Expected: no failures.

- [ ] **Step 4: Commit.** Stage `tests/test_new_patch_inputs.py` (and any patch fixed in Step 2) by path, and commit with the subject `test(new-patches): input edge cases for ridgeline, sketch, reaction-diffusion` and the trailer the build note gives.

---

## Related work, not in this plan's milestones

Recorded here so it isn't lost; each is its own small PR, before or after this build.

- **Long default suffixes in bit-crush and res-crush.** They write `-crush-1bit` and `-pixelate-64`, not the short, hyphen-free suffix the other patches use, so stacks get names like `photo-crush-1bit-fold.jpg`. Changing them changes output names: update `DEFAULT_NAMES` in `tests/test_conventions.py` and the README, and say so in the PR.
- **Help strings that don't end `(default: X)`.** `scan-glitch --seed`, `stipple --seed`, `slit-scan --slits`, and `pixel-sort --threshold` (which reads `(0-255, default: 200)`). The four drawing patches label the input "Source image path" where the others say "Input image path".
- **Drawing patches mid-stack.** dot-halftone, line-halftone, cross-hatch and stipple write RGBA with a transparent background; a later patch in a stack calls `.convert("RGB")`, which turns the transparency black. Options: give them a `--background` color (default transparent) and have `op-img`'s stacking pass `--background white` when a drawing patch isn't the last step, or document "draw last" in the README.
- **Faster tests.** The suite takes about two minutes under a 50% CPU cap, almost all of it spent starting a Python process (and importing numpy and scipy) per test. Import each patch's module once and call its function in-process for the effect and option tests, keeping one subprocess test per patch in `tests/test_conventions.py` for the command-line contract. Expect the suite to drop to well under a minute.

## Self-review

- Spec coverage: all sixteen ideas have a task (Tasks 1–5, 7–10, 12–15, 17–19), and every milestone ends with its input checks (Tasks 6, 11, 16, 20).
- Placeholders: none; every code step carries its code, copied from the files that passed.
- Names: suffixes match the brainstorm (`-reeded`, `-droste`, `-mode7`, `-ripple`, `-smear`, `-shatter`, `-prism`, `-bokeh`, `-relief`, `-solar`, `-huewave`, `-papercut`, `-weave`, `-ridge`, `-sketch`, `-rd`), and the `NEW_PATCHES` entries use the same suffixes.
- After the pre-check, `join_pair_values` and one test each were added to droste, ripple and prism (op-img PR #12). Those three tasks' code and tests were re-run on op-img `main` at `be6e0f8`: `12 passed`.
- Pre-checked: on a scratch copy of `origin/main` at `54fcc03`, with these exact scripts and tests and all sixteen registered, `PATH="/tmp/opimg-venv/bin:$PATH" paced python3 -m pytest -q tests` showed `689 passed in 219.31s` (433 existing, 112 patch tests, 144 input checks).
