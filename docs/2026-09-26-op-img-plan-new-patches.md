---
title: new-patches
kind: plan
target: op-img
topic: new-patches
status: approved
written: 2026-09-26T05:22:30Z
by: claude
---

# op-img New Patches Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task by task. Steps use checkbox (`- [ ]`) syntax for tracking. One milestone per build run.

**Goal:** Add seventeen new patches to op-img, each a self-contained directory the `op` dispatcher discovers by name, with tests, a README section and a README example image.

**Architecture:** Every patch follows the rack's existing contract and needs no change to `op`: a directory `<patch>/` holding `<patch>.py` and `requirements.txt`, called as `<patch> <input> [output] [options]`, saving `<base>-<suffix><ext or .png>` beside the input when no output is given, and printing a one-line `Saved ...` summary to stderr. Each patch reads RGB with Pillow, works in NumPy (and SciPy where named), and writes RGB. Where the idea ramps, a zero-strength setting reproduces the input, so the patches can be layered and animated.

**Tech Stack:** Python 3.10+, Pillow, NumPy, SciPy; pytest with the fixtures in `tests/conftest.py`.

**Spec:** the brainstorm report `/home/jmo/.local/state/handoffs/op-img/20260926-004700-claude-new-patch-brainstorm/last-message.md` (17 ranked ideas). This plan is self-contained: every script, test and README section below is complete and was run against op-img at `38f0fd8` before this plan was written (249 tests passing, plus the 150 input checks; only the two known failures listed below).

## Global Constraints

- Python 3.10+, Pillow, NumPy and SciPy only. `ascii` needs Pillow 10.1 or later for `ImageFont.load_default(size=...)`.
- One directory per patch, named in kebab-case, holding `<patch>.py` and `requirements.txt`. Do not change `op`.
- Argument style: positional `input`, optional positional `output` (`nargs="?"`), then kebab-case options whose help text ends `(default: X)`.
- Default output name: `f"{base}-{suffix}{ext or '.png'}"`, with the short hyphen-free suffix named in each task.
- A missing input prints `Error: file not found: <path>` to stderr and exits 1. Invalid option values go through `parser.error` (exit 2).
- Every patch writes an RGB image the same size as its input.
- Drawn marks use pink `#ec4899` (236, 72, 153), the rack's drawing colour; it is `contour`'s default line colour.
- Tests run with `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`. If `/tmp/opimg-venv` is missing, create it with `python3 -m venv /tmp/opimg-venv`, then `/tmp/opimg-venv/bin/pip install pytest numpy Pillow scipy`.
- Known baseline failures when this plan was written: `tests/test_bit_crush.py::TestBitCrush::test_default_args` and `tests/test_res_crush.py::TestResCrush::test_default_args`. Other work may fix them before this runs, so re-measure the baseline at the start of every milestone and record it. A milestone is green when the full suite shows no failure outside that recorded baseline. Do not edit those two tests.
- Headless build worker: run one simple command per shell call. Do not chain commands with `&&`, `;` or `|`; a chained command can cancel the whole run.
- Commit once per task, staging files by path. Never `git add -A` or `git add .`.

## Review Focus

These are the inputs the brainstorm implies but no single patch's tests exercise. `tests/test_new_patch_inputs.py` (the last task of each milestone) pins each one for every new patch.

1. Transparent, greyscale and palette inputs (RGBA, L and P PNGs, as people drop in screenshots and GIF frames): the patch runs and writes an RGB image the same size.
2. Tiny images (1×1, 2×2, 5×5), smaller than a Voronoi cell, a blur radius or a Kuwahara window: the patch still runs and keeps the size. `ascii` is the exception and refuses an image smaller than one cell with a clear error; its own tests pin that.
3. An input file with no extension (`photo`): the default output is `photo-<suffix>.png`.
4. An explicit `.jpg` output path: the result is a valid JPEG, since every patch writes RGB.
5. Running through the dispatcher (`op <patch> <input>`) rather than the script directly: the patch is found by name and writes its default output.

## File Structure

Each task creates `<patch>/<patch>.py`, `<patch>/requirements.txt`, `tests/test_<patch_with_underscores>.py` and `_output/mclaren-<suffix>.jpg`, and appends to `tests/test_op_cli.py` (`ALL_PATCHES`) and `README.md`. Milestone 1 also creates `tests/test_new_patch_inputs.py`, which later milestones extend.

| Milestone | Patches (brainstorm rank) |
|---|---|

| M1 · Continuous warps and frequency | fft-phase (1), zoom-blur (2), swirl (3), displace (8) |

| M2 · Light, edges and colour | drip (4), edge-glow (5), contour (12), hue-isolate (11), bloom (15) |

| M3 · Cells, paint and depth | voronoi-mosaic (6), oil-paint (7), tilt-shift (9), flow-streak (16) |

| M4 · Display, codec and glyph | crt (10), dither (13), jpeg-rot (14), ascii (17) |


The brainstorm ranked the ideas by visual distinctiveness, then how well they ramp, then effort. Milestones follow that order where related patches allow: M1 holds ranks 1 to 3, and each later milestone groups a family so its reviewer compares like with like.

---


## M1: Continuous warps and frequency

Four patches that each open a family the rack lacks and ramp from an exact identity: the brainstorm's top three plus displace, which shares their sampling approach.

**Start of milestone:** run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests` and record the failing tests as this milestone's baseline.


### Task 1: fft-phase

Brainstorm rank 1. On `_output/mclaren.jpg`: At 0.35 the car is intact under ringing ghost outlines; at 1 it is an orange-on-green haze with no object left.

**Files:**
- Create: `fft-phase/fft-phase.py`, `fft-phase/requirements.txt`, `tests/test_fft_phase.py`, `_output/mclaren-fftphase.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `fft-phase <input> [output] [--amount N] [--seed N]`, default output `<base>-fftphase<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_fft_phase.py`:

```python
"""Tests for fft-phase tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestFftPhase:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("fft-phase", "fft-phase.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-fftphase.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("fft-phase", "fft-phase.py", [img, out, "--amount", "0.8", "--seed", "3"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "amount=0.8" in r.stderr
        assert "seed=3" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("fft-phase", "fft-phase.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_full_amount_dissolves(self, run_tool, tmp_workdir):
        """Full phase noise moves the image far from the source."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "full.png")
        r = run_tool("fft-phase", "fft-phase.py", [img, out, "--amount", "1", "--seed", "1"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).mean() > 10

    def test_seed_is_repeatable(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        a, b = str(tmp_path / "a.png"), str(tmp_path / "b.png")
        assert run_tool("fft-phase", "fft-phase.py", [img, a, "--seed", "7"]).returncode == 0
        assert run_tool("fft-phase", "fft-phase.py", [img, b, "--seed", "7"]).returncode == 0
        assert np.array_equal(_pixels(a), _pixels(b))

    def test_amount_out_of_range(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("fft-phase", "fft-phase.py", [img, "--amount", "2"])
        assert r.returncode != 0

    def test_missing_input(self, run_tool):
        r = run_tool("fft-phase", "fft-phase.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("fft-phase", "fft-phase.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_fft_phase.py`. Expected: FAIL, because `fft-phase/fft-phase.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `fft-phase/requirements.txt` with exactly:

```text
Pillow
numpy
```

- [ ] **Step 4: Write the patch.** Create `fft-phase/fft-phase.py`:

```python
#!/usr/bin/env python3
"""Blend random phase into each channel's Fourier transform, dissolving the image into texture with the same spectrum."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser(description="Dissolve an image by randomising its Fourier phase.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=0.35, help="Phase randomisation, 0 to 1 (default: 0.35)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (default: None)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    h, w, _ = arr.shape

    # The phase of real noise is Hermitian, so the inverse transform stays real.
    # One noise field for all channels keeps colour coherent; zeroing the DC term keeps the mean.
    rng = np.random.default_rng(args.seed)
    noise = np.angle(np.fft.fft2(rng.standard_normal((h, w))))
    noise[0, 0] = 0.0

    result = np.empty_like(arr)
    for c in range(3):
        spectrum = np.fft.fft2(arr[:, :, c])
        shifted = np.abs(spectrum) * np.exp(1j * (np.angle(spectrum) + args.amount * noise))
        result[:, :, c] = np.real(np.fft.ifft2(shifted))

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-fftphase{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved phase-randomised image to {out_path} (amount={args.amount}, seed={args.seed})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_fft_phase.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"fft-phase",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### fft-phase

Keep each channel's Fourier magnitude and blend in random phase, so the image dissolves into a texture with the same spectrum.

```bash
python3 ./fft-phase/fft-phase.py <input> [output] [--amount N] [--seed N]
```

Default: `--amount 0.35`

![fft-phase example](_output/mclaren-fftphase.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op fft-phase _output/mclaren.jpg _output/mclaren-fftphase.jpg --seed 1`. Then run `ls -la _output/mclaren-fftphase.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add fft-phase/fft-phase.py fft-phase/requirements.txt tests/test_fft_phase.py tests/test_op_cli.py README.md _output/mclaren-fftphase.jpg`, then commit with the message `feat(fft-phase): add fft-phase patch` and the trailer the build note gives.


### Task 2: zoom-blur

Brainstorm rank 2. On `_output/mclaren.jpg`: The door at the centre stays sharp while the nose, wheels and grass stretch outward into rays.

**Files:**
- Create: `zoom-blur/zoom-blur.py`, `zoom-blur/requirements.txt`, `tests/test_zoom_blur.py`, `_output/mclaren-zoomblur.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `zoom-blur <input> [output] [--amount N] [--center X,Y] [--samples N]`, default output `<base>-zoomblur<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_zoom_blur.py`:

```python
"""Tests for zoom-blur tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestZoomBlur:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("zoom-blur", "zoom-blur.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-zoomblur.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("zoom-blur", "zoom-blur.py", [img, out, "--amount", "0.6", "--center", "0.25,0.75", "--samples", "8"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "amount=0.6" in r.stderr
        assert "center=0.25,0.75" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("zoom-blur", "zoom-blur.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_edges_blur_more_than_centre(self, run_tool, tmp_workdir):
        """Streaks grow with distance from the centre."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "zoom.png")
        r = run_tool("zoom-blur", "zoom-blur.py", [img, out, "--amount", "1"])
        assert r.returncode == 0
        diff = np.abs(_pixels(out) - _pixels(img)).mean(axis=2)
        assert diff[28:36, 28:36].mean() < diff[:8, :8].mean()

    def test_bad_center(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("zoom-blur", "zoom-blur.py", [img, "--center", "2,0.5"])
        assert r.returncode != 0

    def test_missing_input(self, run_tool):
        r = run_tool("zoom-blur", "zoom-blur.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("zoom-blur", "zoom-blur.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_zoom_blur.py`. Expected: FAIL, because `zoom-blur/zoom-blur.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `zoom-blur/requirements.txt` with exactly:

```text
Pillow
numpy
scipy
```

- [ ] **Step 4: Write the patch.** Create `zoom-blur/zoom-blur.py`:

```python
#!/usr/bin/env python3
"""Average copies of the image scaled up about a centre point, for radial warp-speed streaks."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates


def parse_center(value: str) -> tuple[float, float]:
    try:
        fx, fy = (float(v) for v in value.split(","))
    except ValueError:
        raise argparse.ArgumentTypeError("--center must be X,Y fractions, for example 0.5,0.5")
    if not (0.0 <= fx <= 1.0 and 0.0 <= fy <= 1.0):
        raise argparse.ArgumentTypeError("--center fractions must be between 0 and 1")
    return fx, fy


def main() -> None:
    parser = argparse.ArgumentParser(description="Radial zoom blur about a centre point.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=0.3, help="Zoom strength, 0 to 1; the largest copy is scaled by 1 + amount (default: 0.3)")
    parser.add_argument("--center", type=parse_center, default=(0.5, 0.5), help="Zoom centre as X,Y fractions (default: 0.5,0.5)")
    parser.add_argument("--samples", type=int, default=32, help="Number of scaled copies averaged (default: 32)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")
    if args.samples < 1:
        parser.error("--samples must be at least 1")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    h, w, _ = arr.shape
    cx, cy = args.center[0] * (w - 1), args.center[1] * (h - 1)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)

    acc = np.zeros_like(arr)
    for i in range(args.samples):
        scale = 1.0 + args.amount * i / max(args.samples - 1, 1)
        src_x = cx + (xx - cx) / scale
        src_y = cy + (yy - cy) / scale
        for c in range(3):
            acc[:, :, c] += map_coordinates(arr[:, :, c], [src_y, src_x], order=1, mode="nearest")

    result_img = Image.fromarray(np.clip(np.rint(acc / args.samples), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-zoomblur{ext or '.png'}"

    result_img.save(out_path)
    center = f"{args.center[0]},{args.center[1]}"
    print(f"Saved zoom-blurred image to {out_path} (amount={args.amount}, center={center}, samples={args.samples})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_zoom_blur.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"zoom-blur",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### zoom-blur

Average copies of the image scaled up about a centre point, for radial warp-speed streaks.

```bash
python3 ./zoom-blur/zoom-blur.py <input> [output] [--amount N] [--center X,Y] [--samples N]
```

Default: `--amount 0.3 --center 0.5,0.5 --samples 32`

![zoom-blur example](_output/mclaren-zoomblur.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op zoom-blur _output/mclaren.jpg _output/mclaren-zoomblur.jpg`. Then run `ls -la _output/mclaren-zoomblur.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add zoom-blur/zoom-blur.py zoom-blur/requirements.txt tests/test_zoom_blur.py tests/test_op_cli.py README.md _output/mclaren-zoomblur.jpg`, then commit with the message `feat(zoom-blur): add zoom-blur patch` and the trailer the build note gives.


### Task 3: swirl

Brainstorm rank 3. On `_output/mclaren.jpg`: The door and wheel arch twist into an orange vortex; the rim of the frame barely moves.

**Files:**
- Create: `swirl/swirl.py`, `swirl/requirements.txt`, `tests/test_swirl.py`, `_output/mclaren-swirl.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `swirl <input> [output] [--angle DEG] [--radius N] [--center X,Y]`, default output `<base>-swirl<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_swirl.py`:

```python
"""Tests for swirl tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestSwirl:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("swirl", "swirl.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-swirl.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("swirl", "swirl.py", [img, out, "--angle", "-180", "--radius", "0.5", "--center", "0.4,0.6"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "angle=-180.0" in r.stderr
        assert "radius=0.5" in r.stderr

    def test_zero_angle_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("swirl", "swirl.py", [img, out, "--angle", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_outside_radius_is_untouched(self, run_tool, tmp_workdir):
        """Pixels beyond the radius do not move; pixels inside do."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "swirl.png")
        r = run_tool("swirl", "swirl.py", [img, out, "--angle", "360", "--radius", "0.5"])
        assert r.returncode == 0
        diff = np.abs(_pixels(out) - _pixels(img)).max(axis=2)
        assert diff[:4, :4].max() <= 1
        assert diff[:4, -4:].max() <= 1
        assert diff[20:44, 20:44].mean() > 5

    def test_angle_out_of_range(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("swirl", "swirl.py", [img, "--angle", "5000"])
        assert r.returncode != 0

    def test_missing_input(self, run_tool):
        r = run_tool("swirl", "swirl.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("swirl", "swirl.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_swirl.py`. Expected: FAIL, because `swirl/swirl.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `swirl/requirements.txt` with exactly:

```text
Pillow
numpy
scipy
```

- [ ] **Step 4: Write the patch.** Create `swirl/swirl.py`:

```python
#!/usr/bin/env python3
"""Twist the image around a centre, with the rotation falling off toward a radius."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates


def parse_center(value: str) -> tuple[float, float]:
    try:
        fx, fy = (float(v) for v in value.split(","))
    except ValueError:
        raise argparse.ArgumentTypeError("--center must be X,Y fractions, for example 0.5,0.5")
    if not (0.0 <= fx <= 1.0 and 0.0 <= fy <= 1.0):
        raise argparse.ArgumentTypeError("--center fractions must be between 0 and 1")
    return fx, fy


def main() -> None:
    parser = argparse.ArgumentParser(description="Swirl the image around a centre point.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--angle", type=float, default=360.0, help="Rotation at the centre in degrees, -1080 to 1080 (default: 360.0)")
    parser.add_argument("--radius", type=float, default=1.0, help="Swirl radius as a fraction of the half-diagonal, 0.1 to 1.5 (default: 1.0)")
    parser.add_argument("--center", type=parse_center, default=(0.5, 0.5), help="Swirl centre as X,Y fractions (default: 0.5,0.5)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not -1080.0 <= args.angle <= 1080.0:
        parser.error("--angle must be between -1080 and 1080")
    if not 0.1 <= args.radius <= 1.5:
        parser.error("--radius must be between 0.1 and 1.5")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    h, w, _ = arr.shape
    cx, cy = args.center[0] * (w - 1), args.center[1] * (h - 1)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)

    dx, dy = xx - cx, yy - cy
    r = np.hypot(dx, dy)
    theta = np.arctan2(dy, dx)
    limit = args.radius * np.hypot(w / 2.0, h / 2.0)
    falloff = np.clip(1.0 - r / limit, 0.0, 1.0)
    theta_src = theta - np.radians(args.angle) * falloff ** 2

    src_x = cx + r * np.cos(theta_src)
    src_y = cy + r * np.sin(theta_src)

    result = np.zeros_like(arr)
    for c in range(3):
        result[:, :, c] = map_coordinates(arr[:, :, c], [src_y, src_x], order=1, mode="reflect")

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-swirl{ext or '.png'}"

    result_img.save(out_path)
    center = f"{args.center[0]},{args.center[1]}"
    print(f"Saved swirled image to {out_path} (angle={args.angle}, radius={args.radius}, center={center})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_swirl.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"swirl",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### swirl

Twist the image around a centre, with the rotation fading out toward a radius.

```bash
python3 ./swirl/swirl.py <input> [output] [--angle DEG] [--radius N] [--center X,Y]
```

Default: `--angle 360 --radius 1.0 --center 0.5,0.5`

![swirl example](_output/mclaren-swirl.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op swirl _output/mclaren.jpg _output/mclaren-swirl.jpg`. Then run `ls -la _output/mclaren-swirl.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add swirl/swirl.py swirl/requirements.txt tests/test_swirl.py tests/test_op_cli.py README.md _output/mclaren-swirl.jpg`, then commit with the message `feat(swirl): add swirl patch` and the trailer the build note gives.


### Task 4: displace

Brainstorm rank 8. On `_output/mclaren.jpg`: Bright bonnet and windscreen slide one way, dark tyres and intakes the other; the car tears along its panel lines.

**Files:**
- Create: `displace/displace.py`, `displace/requirements.txt`, `tests/test_displace.py`, `_output/mclaren-displace.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `displace <input> [output] [--amount PX] [--angle DEG] [--blur N]`, default output `<base>-displace<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_displace.py`:

```python
"""Tests for displace tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _horizontal_stripes(path: str) -> str:
    """Rows alternate between dark and light; every row is constant along x."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    for y in range(64):
        arr[y, :] = (230, 200, 40) if (y // 8) % 2 == 0 else (20, 40, 90)
    Image.fromarray(arr).save(path)
    return path


class TestDisplace:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("displace", "displace.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-displace.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("displace", "displace.py", [img, out, "--amount", "20", "--angle", "45", "--blur", "1"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "amount=20.0" in r.stderr
        assert "angle=45.0" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("displace", "displace.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_displacement_follows_angle(self, run_tool, tmp_path):
        """Horizontal displacement cannot change rows that are constant along x; vertical can."""
        img = _horizontal_stripes(str(tmp_path / "stripes.png"))
        across = str(tmp_path / "across.png")
        down = str(tmp_path / "down.png")
        assert run_tool("displace", "displace.py", [img, across, "--amount", "40", "--angle", "0"]).returncode == 0
        assert run_tool("displace", "displace.py", [img, down, "--amount", "40", "--angle", "90"]).returncode == 0
        assert np.abs(_pixels(across) - _pixels(img)).max() <= 1
        assert np.abs(_pixels(down) - _pixels(img)).mean() > 5

    def test_amount_out_of_range(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("displace", "displace.py", [img, "--amount", "500"])
        assert r.returncode != 0

    def test_missing_input(self, run_tool):
        r = run_tool("displace", "displace.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("displace", "displace.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_displace.py`. Expected: FAIL, because `displace/displace.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `displace/requirements.txt` with exactly:

```text
Pillow
numpy
scipy
```

- [ ] **Step 4: Write the patch.** Create `displace/displace.py`:

```python
#!/usr/bin/env python3
"""Move each pixel along an angle by an amount taken from its own blurred brightness."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates


def main() -> None:
    parser = argparse.ArgumentParser(description="Displace pixels by their own brightness.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=60.0, help="Maximum displacement in pixels, 0 to 300 (default: 60.0)")
    parser.add_argument("--angle", type=float, default=0.0, help="Displacement direction in degrees (default: 0.0)")
    parser.add_argument("--blur", type=float, default=3.0, help="Blur sigma of the brightness map (default: 3.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 300.0:
        parser.error("--amount must be between 0 and 300")
    if args.blur < 0:
        parser.error("--blur must be 0 or more")

    img = Image.open(args.input).convert("RGB")
    arr = np.array(img, dtype=np.float64)
    h, w, _ = arr.shape

    # Centred on mid-grey, so mid-tones stay put while light and dark move in opposite directions.
    brightness = gaussian_filter(np.array(img.convert("L"), dtype=np.float64), args.blur) / 255.0 - 0.5
    rad = np.radians(args.angle)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    src_x = xx + args.amount * brightness * np.cos(rad)
    src_y = yy + args.amount * brightness * np.sin(rad)

    result = np.zeros_like(arr)
    for c in range(3):
        result[:, :, c] = map_coordinates(arr[:, :, c], [src_y, src_x], order=1, mode="reflect")

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-displace{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved displaced image to {out_path} (amount={args.amount}, angle={args.angle}, blur={args.blur})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_displace.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"displace",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### displace

Move each pixel along an angle by an amount taken from its own blurred brightness, so light and dark areas tear apart in opposite directions.

```bash
python3 ./displace/displace.py <input> [output] [--amount PX] [--angle DEG] [--blur N]
```

Default: `--amount 60 --angle 0 --blur 3`

![displace example](_output/mclaren-displace.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op displace _output/mclaren.jpg _output/mclaren-displace.jpg`. Then run `ls -la _output/mclaren-displace.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add displace/displace.py displace/requirements.txt tests/test_displace.py tests/test_op_cli.py README.md _output/mclaren-displace.jpg`, then commit with the message `feat(displace): add displace patch` and the trailer the build note gives.


### Task 5: shared input checks for fft-phase, zoom-blur, swirl, displace

**Files:**
- Create: `tests/test_new_patch_inputs.py`

**Interfaces:**
- Consumes: every patch in this milestone; `run_tool`, `run_op`, `tmp_workdir`, `assert_valid_image` from `tests/conftest.py`.
- Produces: `NEW_PATCHES`, a list of `(patch directory, output suffix)` pairs that later milestones extend.

This file pins the Review Focus cases for every new patch: transparent, greyscale and palette input; images of 1, 2 and 5 pixels; an input with no extension; explicit JPEG output; and running through `op`.

- [ ] **Step 1: Write the test.** Create `tests/test_new_patch_inputs.py`:

```python
"""Input edge cases shared by the patches added in the new-patches plan."""

import os

import numpy as np
import pytest
from PIL import Image

from conftest import assert_valid_image

# (patch directory, output suffix). Each milestone appends its patches here.
NEW_PATCHES = [
    ("fft-phase", "fftphase"),
    ("zoom-blur", "zoomblur"),
    ("swirl", "swirl"),
    ("displace", "displace"),
]
NAMES = [name for name, _ in NEW_PATCHES]


def _gradient_array(size: int = 64) -> np.ndarray:
    yy, xx = np.mgrid[0:size, 0:size]
    return np.stack([xx * 4, yy * 4, (xx + yy) * 2], axis=2).clip(0, 255).astype(np.uint8)


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("mode", ["RGBA", "L", "P"])
def test_accepts_other_modes(run_tool, tmp_path, name, mode):
    """Transparent, greyscale and palette inputs all produce an RGB image the same size."""
    src = str(tmp_path / f"in-{mode}.png")
    img = Image.fromarray(_gradient_array())
    if mode == "RGBA":
        img = img.convert("RGBA")
        img.putalpha(128)
    else:
        img = img.convert(mode)
    img.save(src)
    out = str(tmp_path / "out.png")
    r = run_tool(name, f"{name}.py", [src, out])
    assert r.returncode == 0, r.stderr
    result = Image.open(out)
    assert result.mode == "RGB"
    assert result.size == (64, 64)


@pytest.mark.parametrize("name", [n for n in NAMES if n != "ascii"])
@pytest.mark.parametrize("size", [1, 2, 5])
def test_tiny_images(run_tool, tmp_path, name, size):
    src = str(tmp_path / "tiny.png")
    Image.fromarray(_gradient_array(64)[:size, :size]).save(src)
    out = str(tmp_path / "out.png")
    r = run_tool(name, f"{name}.py", [src, out])
    assert r.returncode == 0, r.stderr
    assert Image.open(out).size == (size, size)


@pytest.mark.parametrize("name,suffix", NEW_PATCHES)
def test_input_without_extension_defaults_to_png(run_tool, tmp_path, name, suffix):
    src = str(tmp_path / "photo")
    Image.fromarray(_gradient_array()).save(src, format="PNG")
    r = run_tool(name, f"{name}.py", [src])
    assert r.returncode == 0, r.stderr
    assert_valid_image(str(tmp_path / f"photo-{suffix}.png"))


@pytest.mark.parametrize("name", NAMES)
def test_explicit_jpeg_output(run_tool, tmp_workdir, name):
    tmp_path, img = tmp_workdir
    out = str(tmp_path / "out.jpg")
    r = run_tool(name, f"{name}.py", [img, out])
    assert r.returncode == 0, r.stderr
    assert Image.open(out).format == "JPEG"


@pytest.mark.parametrize("name,suffix", NEW_PATCHES)
def test_runs_through_op(run_op, tmp_workdir, name, suffix):
    tmp_path, img = tmp_workdir
    r = run_op([name, img])
    assert r.returncode == 0, r.stderr
    assert os.path.isfile(str(tmp_path / f"input-{suffix}.png"))
```

- [ ] **Step 2: Run it.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_new_patch_inputs.py`. Expected: every test passes. If a patch fails on a tiny or non-RGB image, fix that patch (the scripts above pass as written) and rerun.

- [ ] **Step 3: Commit.** Run `git add tests/test_new_patch_inputs.py`, then commit with the message `test(new-patches): input edge cases for fft-phase, zoom-blur, swirl, displace` and the trailer the build note gives.


**End of milestone:** run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`. Expected: no failure outside the baseline recorded at the start of M1. Record the pass count in the closing report.

---


## M2: Light, edges and colour

Patches that add light or draw structure over the photo.

**Start of milestone:** run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests` and record the failing tests as this milestone's baseline.


### Task 6: drip

Brainstorm rank 4. On `_output/mclaren.jpg`: Windscreen reflections and the white fence run down over the bonnet and lawn; dark tyres stay put.

**Files:**
- Create: `drip/drip.py`, `drip/requirements.txt`, `tests/test_drip.py`, `_output/mclaren-drip.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `drip <input> [output] [--length PX] [--threshold N] [--direction down|up|left|right]`, default output `<base>-drip<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_drip.py`:

```python
"""Tests for drip tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _white_spot(path: str) -> str:
    """Black 64x64 with a 2x2 white spot at rows 10-11, columns 30-31."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[10:12, 30:32] = 255
    Image.fromarray(arr).save(path)
    return path


class TestDrip:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("drip", "drip.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-drip.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("drip", "drip.py", [img, out, "--length", "30", "--threshold", "100", "--direction", "left"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "direction=left" in r.stderr

    def test_zero_length_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("drip", "drip.py", [img, out, "--length", "0"])
        assert r.returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_only_brightens(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "drip.png")
        r = run_tool("drip", "drip.py", [img, out, "--threshold", "100"])
        assert r.returncode == 0
        assert (_pixels(out) >= _pixels(img)).all()

    def test_drips_in_direction(self, run_tool, tmp_path):
        """A white spot trails below itself when dripping down, and nothing appears above."""
        img = _white_spot(str(tmp_path / "spot.png"))
        down = str(tmp_path / "down.png")
        up = str(tmp_path / "up.png")
        assert run_tool("drip", "drip.py", [img, down, "--length", "20", "--direction", "down"]).returncode == 0
        assert run_tool("drip", "drip.py", [img, up, "--length", "20", "--direction", "up"]).returncode == 0
        d, u = _pixels(down), _pixels(up)
        assert d[20, 30].min() > 0 and d[5, 30].max() == 0
        assert u[5, 30].min() > 0 and u[20, 30].max() == 0

    def test_missing_input(self, run_tool):
        r = run_tool("drip", "drip.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("drip", "drip.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_drip.py`. Expected: FAIL, because `drip/drip.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `drip/requirements.txt` with exactly:

```text
Pillow
numpy
```

- [ ] **Step 4: Write the patch.** Create `drip/drip.py`:

```python
#!/usr/bin/env python3
"""Bleed bright pixels in one direction with an exponential tail, like wet paint running."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def orient(arr: np.ndarray, direction: str) -> np.ndarray:
    """Rotate the array so the drip runs down axis 0."""
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Drip bright pixels like running paint.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--length", type=float, default=120.0, help="Tail length in pixels; 0 leaves the image unchanged (default: 120.0)")
    parser.add_argument("--threshold", type=int, default=180, help="Brightness above which pixels drip, 0 to 255 (default: 180)")
    parser.add_argument("--direction", choices=["down", "up", "left", "right"], default="down", help="Drip direction (default: down)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if args.length < 0:
        parser.error("--length must be 0 or more")
    if not 0 <= args.threshold <= 255:
        parser.error("--threshold must be between 0 and 255")

    img = Image.open(args.input).convert("RGB")
    arr = np.array(img, dtype=np.float64)
    lum = np.array(img.convert("L"), dtype=np.float64)

    if args.length == 0:
        result = arr
    else:
        gate = np.clip((lum - args.threshold) / max(255 - args.threshold, 1), 0.0, 1.0)
        light = orient(arr * gate[:, :, None], args.direction)
        base = orient(arr, args.direction)
        decay = np.exp(-1.0 / args.length)
        tail = np.zeros(base.shape[1:])
        out = np.empty_like(base)
        for y in range(base.shape[0]):
            tail = np.maximum(light[y], tail * decay)
            out[y] = np.maximum(base[y], tail)
        result = unorient(out, args.direction)

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base_name, ext = os.path.splitext(args.input)
        out_path = f"{base_name}-drip{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved dripped image to {out_path} (length={args.length}, threshold={args.threshold}, direction={args.direction})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_drip.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"drip",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### drip

Bleed bright pixels in one direction with a fading tail, like wet paint running.

```bash
python3 ./drip/drip.py <input> [output] [--length PX] [--threshold N] [--direction down|up|left|right]
```

Default: `--length 120 --threshold 180 --direction down`

![drip example](_output/mclaren-drip.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op drip _output/mclaren.jpg _output/mclaren-drip.jpg`. Then run `ls -la _output/mclaren-drip.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add drip/drip.py drip/requirements.txt tests/test_drip.py tests/test_op_cli.py README.md _output/mclaren-drip.jpg`, then commit with the message `feat(drip): add drip patch` and the trailer the build note gives.


### Task 7: edge-glow

Brainstorm rank 5. On `_output/mclaren.jpg`: The outline, panel gaps and wheel spokes glow orange on black; the grass fizzes with green sparks.

**Files:**
- Create: `edge-glow/edge-glow.py`, `edge-glow/requirements.txt`, `tests/test_edge_glow.py`, `_output/mclaren-edgeglow.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `edge-glow <input> [output] [--amount N] [--radius N]`, default output `<base>-edgeglow<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_edge_glow.py`:

```python
"""Tests for edge-glow tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _split(path: str) -> str:
    """Left half dark blue, right half light orange: one vertical edge at x=32."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[:, :32] = (10, 20, 60)
    arr[:, 32:] = (240, 150, 60)
    Image.fromarray(arr).save(path)
    return path


class TestEdgeGlow:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("edge-glow", "edge-glow.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-edgeglow.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("edge-glow", "edge-glow.py", [img, out, "--amount", "0.5", "--radius", "3"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "amount=0.5" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("edge-glow", "edge-glow.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_glow_sits_on_the_edge(self, run_tool, tmp_path):
        img = _split(str(tmp_path / "split.png"))
        out = str(tmp_path / "glow.png")
        r = run_tool("edge-glow", "edge-glow.py", [img, out, "--radius", "2"])
        assert r.returncode == 0
        px = _pixels(out).sum(axis=2)
        assert px[:, 30:34].mean() > 100
        assert px[:, :8].max() <= 3
        assert px[:, -8:].max() <= 3

    def test_missing_input(self, run_tool):
        r = run_tool("edge-glow", "edge-glow.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("edge-glow", "edge-glow.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_edge_glow.py`. Expected: FAIL, because `edge-glow/edge-glow.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `edge-glow/requirements.txt` with exactly:

```text
Pillow
numpy
scipy
```

- [ ] **Step 4: Write the patch.** Create `edge-glow/edge-glow.py`:

```python
#!/usr/bin/env python3
"""Turn edges into neon lines in each pixel's own hue, with a bloom halo, over a darkening base."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, sobel


def main() -> None:
    parser = argparse.ArgumentParser(description="Glowing neon edges.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=1.0, help="Blend from the photo (0) to glowing edges on black (1) (default: 1.0)")
    parser.add_argument("--radius", type=float, default=6.0, help="Halo blur sigma in pixels (default: 6.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")
    if args.radius < 0:
        parser.error("--radius must be 0 or more")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    lum = gaussian_filter(arr @ np.array([0.299, 0.587, 0.114]), 1.0)
    magnitude = np.hypot(sobel(lum, axis=1), sobel(lum, axis=0))
    peak = np.percentile(magnitude, 99)
    edges = np.clip(magnitude / peak, 0.0, 1.0) if peak > 0 else np.zeros_like(magnitude)

    # Each edge glows in its own pixel's hue at full brightness; black pixels glow white.
    brightest = arr.max(axis=2, keepdims=True)
    hue = np.where(brightest > 0, arr / np.maximum(brightest, 1e-9), 1.0)
    glow = hue * 255.0 * edges[:, :, None]
    halo = gaussian_filter(glow, (args.radius, args.radius, 0))

    result = arr * (1.0 - args.amount) + (glow + halo) * args.amount
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-edgeglow{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved edge-glow image to {out_path} (amount={args.amount}, radius={args.radius})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_edge_glow.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"edge-glow",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### edge-glow

Turn edges into neon lines in each pixel's own hue, with a soft halo, over a darkened base.

```bash
python3 ./edge-glow/edge-glow.py <input> [output] [--amount N] [--radius N]
```

Default: `--amount 1 --radius 6`

![edge-glow example](_output/mclaren-edgeglow.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op edge-glow _output/mclaren.jpg _output/mclaren-edgeglow.jpg`. Then run `ls -la _output/mclaren-edgeglow.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add edge-glow/edge-glow.py edge-glow/requirements.txt tests/test_edge_glow.py tests/test_op_cli.py README.md _output/mclaren-edgeglow.jpg`, then commit with the message `feat(edge-glow): add edge-glow patch` and the trailer the build note gives.


### Task 8: contour

Brainstorm rank 12. On `_output/mclaren.jpg`: Glossy panels become tight concentric rings; the grass becomes small closed loops.

**Files:**
- Create: `contour/contour.py`, `contour/requirements.txt`, `tests/test_contour.py`, `_output/mclaren-contour.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `contour <input> [output] [--levels N] [--blur N] [--width PX] [--color HEX] [--amount N]`, default output `<base>-contour<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_contour.py`:

```python
"""Tests for contour tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image

PINK = (236, 72, 153)


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _ramp(path: str) -> str:
    """Grey ramp from black on the left to white on the right."""
    row = np.linspace(0, 255, 64).astype(np.uint8)
    arr = np.repeat(np.repeat(row[None, :, None], 64, axis=0), 3, axis=2)
    Image.fromarray(arr).save(path)
    return path


class TestContour:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("contour", "contour.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-contour.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("contour", "contour.py", [img, out, "--levels", "8", "--width", "2", "--color", "#0f0"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "color=#00ff00" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("contour", "contour.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_lines_mark_band_boundaries(self, run_tool, tmp_path):
        """A left-to-right ramp in 4 bands has 3 pink vertical lines on black."""
        img = _ramp(str(tmp_path / "ramp.png"))
        out = str(tmp_path / "lines.png")
        r = run_tool("contour", "contour.py", [img, out, "--levels", "4", "--blur", "0"])
        assert r.returncode == 0
        row = _pixels(out)[32]
        pink = [x for x in range(64) if tuple(row[x]) == PINK]
        assert len(pink) == 3
        others = [x for x in range(64) if x not in pink]
        assert row[others].max() == 0

    def test_bad_color(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("contour", "contour.py", [img, "--color", "pink"])
        assert r.returncode != 0

    def test_missing_input(self, run_tool):
        r = run_tool("contour", "contour.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("contour", "contour.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_contour.py`. Expected: FAIL, because `contour/contour.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `contour/requirements.txt` with exactly:

```text
Pillow
numpy
scipy
```

- [ ] **Step 4: Write the patch.** Create `contour/contour.py`:

```python
#!/usr/bin/env python3
"""Draw iso-luminance lines at N levels, like a topographic map of the photo."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, gaussian_filter


def parse_color(value: str) -> tuple[int, int, int]:
    hexstr = value.lstrip("#")
    if len(hexstr) == 3:
        hexstr = "".join(ch * 2 for ch in hexstr)
    if len(hexstr) != 6:
        raise argparse.ArgumentTypeError(f"invalid color: {value}")
    try:
        return tuple(int(hexstr[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid color: {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Topographic contour lines of brightness.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--levels", type=int, default=16, help="Number of brightness bands, 2 to 64 (default: 16)")
    parser.add_argument("--blur", type=float, default=2.0, help="Blur sigma before banding (default: 2.0)")
    parser.add_argument("--width", type=int, default=1, help="Line width in pixels (default: 1)")
    parser.add_argument("--color", type=parse_color, default="#ec4899", help="Line color as hex (default: #ec4899)")
    parser.add_argument("--amount", type=float, default=1.0, help="Blend from the photo (0) to lines on black (1) (default: 1.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 2 <= args.levels <= 64:
        parser.error("--levels must be between 2 and 64")
    if args.width < 1:
        parser.error("--width must be at least 1")
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")

    img = Image.open(args.input).convert("RGB")
    arr = np.array(img, dtype=np.float64)
    lum = gaussian_filter(np.array(img.convert("L"), dtype=np.float64), args.blur)
    band = np.floor(lum * args.levels / 256.0).astype(int)

    edge = np.zeros(band.shape, dtype=bool)
    edge[1:, :] |= band[1:, :] != band[:-1, :]
    edge[:, 1:] |= band[:, 1:] != band[:, :-1]
    if args.width > 1:
        edge = binary_dilation(edge, iterations=args.width - 1)

    result = arr * (1.0 - args.amount)
    result[edge] += np.array(args.color, dtype=np.float64) * args.amount
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-contour{ext or '.png'}"

    color = "#%02x%02x%02x" % args.color
    result_img.save(out_path)
    print(f"Saved contour image to {out_path} (levels={args.levels}, blur={args.blur}, width={args.width}, color={color}, amount={args.amount})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_contour.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"contour",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### contour

Draw lines where brightness crosses N levels, like a topographic map of the photo. Pink lines on black by default.

```bash
python3 ./contour/contour.py <input> [output] [--levels N] [--blur N] [--width PX] [--color HEX] [--amount N]
```

Default: `--levels 16 --blur 2 --width 1 --color #ec4899 --amount 1`

![contour example](_output/mclaren-contour.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op contour _output/mclaren.jpg _output/mclaren-contour.jpg`. Then run `ls -la _output/mclaren-contour.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add contour/contour.py contour/requirements.txt tests/test_contour.py tests/test_op_cli.py README.md _output/mclaren-contour.jpg`, then commit with the message `feat(contour): add contour patch` and the trailer the build note gives.


### Task 9: hue-isolate

Brainstorm rank 11. On `_output/mclaren.jpg`: Both McLarens stay vivid orange; the lawn and trees go grey.

**Files:**
- Create: `hue-isolate/hue-isolate.py`, `hue-isolate/requirements.txt`, `tests/test_hue_isolate.py`, `_output/mclaren-hueiso.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `hue-isolate <input> [output] [--hue DEG] [--width DEG] [--amount N]`, default output `<base>-hueiso<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_hue_isolate.py`:

```python
"""Tests for hue-isolate tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _orange_and_green(path: str) -> str:
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[:, :32] = (240, 120, 20)
    arr[:, 32:] = (40, 180, 60)
    Image.fromarray(arr).save(path)
    return path


class TestHueIsolate:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("hue-isolate", "hue-isolate.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-hueiso.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("hue-isolate", "hue-isolate.py", [img, out, "--hue", "200", "--width", "30", "--amount", "0.7"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "hue=200.0" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("hue-isolate", "hue-isolate.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_keeps_orange_greys_green(self, run_tool, tmp_path):
        img = _orange_and_green(str(tmp_path / "two.png"))
        out = str(tmp_path / "pop.png")
        r = run_tool("hue-isolate", "hue-isolate.py", [img, out])
        assert r.returncode == 0
        px = _pixels(out)
        assert tuple(px[10, 10]) == (240, 120, 20)
        green = px[10, 50]
        assert green.max() - green.min() <= 1

    def test_missing_input(self, run_tool):
        r = run_tool("hue-isolate", "hue-isolate.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("hue-isolate", "hue-isolate.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_hue_isolate.py`. Expected: FAIL, because `hue-isolate/hue-isolate.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `hue-isolate/requirements.txt` with exactly:

```text
Pillow
numpy
```

- [ ] **Step 4: Write the patch.** Create `hue-isolate/hue-isolate.py`:

```python
#!/usr/bin/env python3
"""Keep one hue band in full colour and desaturate everything else."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser(description="Colour pop: keep one hue, grey out the rest.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--hue", type=float, default=25.0, help="Hue to keep in degrees, 0 to 360 (default: 25.0)")
    parser.add_argument("--width", type=float, default=20.0, help="Half-width of the kept band in degrees (default: 20.0)")
    parser.add_argument("--amount", type=float, default=1.0, help="Desaturation strength outside the band, 0 to 1 (default: 1.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.hue <= 360.0:
        parser.error("--hue must be between 0 and 360")
    if args.width < 0:
        parser.error("--width must be 0 or more")
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")

    img = Image.open(args.input).convert("RGB")
    arr = np.array(img, dtype=np.float64)
    hue = np.array(img.convert("HSV"), dtype=np.float64)[:, :, 0] * 360.0 / 255.0

    distance = np.abs(hue - args.hue) % 360.0
    distance = np.minimum(distance, 360.0 - distance)
    keep = np.clip(1.0 - (distance - args.width) / 15.0, 0.0, 1.0)

    gray = (arr @ np.array([0.299, 0.587, 0.114]))[:, :, None]
    saturation = keep + (1.0 - keep) * (1.0 - args.amount)
    result = gray + (arr - gray) * saturation[:, :, None]
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-hueiso{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved hue-isolated image to {out_path} (hue={args.hue}, width={args.width}, amount={args.amount})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_hue_isolate.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"hue-isolate",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### hue-isolate

Keep one hue band in full colour and turn everything else grey.

```bash
python3 ./hue-isolate/hue-isolate.py <input> [output] [--hue DEG] [--width DEG] [--amount N]
```

Default: `--hue 25 --width 20 --amount 1` (orange)

![hue-isolate example](_output/mclaren-hueiso.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op hue-isolate _output/mclaren.jpg _output/mclaren-hueiso.jpg`. Then run `ls -la _output/mclaren-hueiso.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add hue-isolate/hue-isolate.py hue-isolate/requirements.txt tests/test_hue_isolate.py tests/test_op_cli.py README.md _output/mclaren-hueiso.jpg`, then commit with the message `feat(hue-isolate): add hue-isolate patch` and the trailer the build note gives.


### Task 10: bloom

Brainstorm rank 15. On `_output/mclaren.jpg`: Windscreen reflections, the headlight and the rims flare into a warm haze. Subtle alone; best as a layer.

**Files:**
- Create: `bloom/bloom.py`, `bloom/requirements.txt`, `tests/test_bloom.py`, `_output/mclaren-bloom.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `bloom <input> [output] [--amount N] [--threshold N] [--radius N]`, default output `<base>-bloom<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_bloom.py`:

```python
"""Tests for bloom tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _bright_spot(path: str) -> str:
    """Dark grey 64x64 with a white 4x4 square in the middle."""
    arr = np.full((64, 64, 3), 40, dtype=np.uint8)
    arr[30:34, 30:34] = 255
    Image.fromarray(arr).save(path)
    return path


class TestBloom:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("bloom", "bloom.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-bloom.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("bloom", "bloom.py", [img, out, "--amount", "1.5", "--threshold", "120", "--radius", "4"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "threshold=120" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("bloom", "bloom.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_never_darkens(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "bloom.png")
        r = run_tool("bloom", "bloom.py", [img, out, "--amount", "2", "--threshold", "100"])
        assert r.returncode == 0
        assert (_pixels(out) >= _pixels(img) - 1).all()

    def test_highlight_spreads(self, run_tool, tmp_path):
        img = _bright_spot(str(tmp_path / "spot.png"))
        out = str(tmp_path / "glow.png")
        r = run_tool("bloom", "bloom.py", [img, out, "--radius", "3"])
        assert r.returncode == 0
        px = _pixels(out)
        assert px[32, 38].mean() > 40
        assert px[32, 38].mean() > px[0, 0].mean()

    def test_missing_input(self, run_tool):
        r = run_tool("bloom", "bloom.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("bloom", "bloom.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_bloom.py`. Expected: FAIL, because `bloom/bloom.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `bloom/requirements.txt` with exactly:

```text
Pillow
numpy
scipy
```

- [ ] **Step 4: Write the patch.** Create `bloom/bloom.py`:

```python
#!/usr/bin/env python3
"""Blur the highlights at several radii and screen them back for a soft glow."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter


def main() -> None:
    parser = argparse.ArgumentParser(description="Highlight bloom and halation.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=1.0, help="Glow strength, 0 to 2 (default: 1.0)")
    parser.add_argument("--threshold", type=int, default=170, help="Brightness above which pixels glow, 0 to 255 (default: 170)")
    parser.add_argument("--radius", type=float, default=8.0, help="Base glow radius in pixels (default: 8.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 2.0:
        parser.error("--amount must be between 0 and 2")
    if not 0 <= args.threshold <= 255:
        parser.error("--threshold must be between 0 and 255")
    if args.radius <= 0:
        parser.error("--radius must be more than 0")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    lum = arr @ np.array([0.299, 0.587, 0.114])
    bright = arr * np.clip((lum - args.threshold) / max(255 - args.threshold, 1), 0.0, 1.0)[:, :, None]

    halo = np.zeros_like(arr)
    for scale, weight in ((1, 0.5), (3, 0.3), (9, 0.2)):
        sigma = args.radius * scale
        halo += weight * gaussian_filter(bright, (sigma, sigma, 0))
    glow = np.clip(halo * args.amount, 0, 255)

    # Screen blend: never darkens.
    result = 255.0 - (255.0 - arr) * (255.0 - glow) / 255.0
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-bloom{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved bloom image to {out_path} (amount={args.amount}, threshold={args.threshold}, radius={args.radius})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_bloom.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"bloom",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### bloom

Pull out the highlights, blur them at three radii and screen them back for a soft glow.

```bash
python3 ./bloom/bloom.py <input> [output] [--amount N] [--threshold N] [--radius N]
```

Default: `--amount 1 --threshold 170 --radius 8`

![bloom example](_output/mclaren-bloom.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op bloom _output/mclaren.jpg _output/mclaren-bloom.jpg`. Then run `ls -la _output/mclaren-bloom.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add bloom/bloom.py bloom/requirements.txt tests/test_bloom.py tests/test_op_cli.py README.md _output/mclaren-bloom.jpg`, then commit with the message `feat(bloom): add bloom patch` and the trailer the build note gives.


### Task 11: shared input checks for drip, edge-glow, contour, hue-isolate, bloom

**Files:**
- Modify: `tests/test_new_patch_inputs.py` (`NEW_PATCHES`)

**Interfaces:**
- Consumes: every patch in this milestone; `run_tool`, `run_op`, `tmp_workdir`, `assert_valid_image` from `tests/conftest.py`.
- Produces: `NEW_PATCHES`, a list of `(patch directory, output suffix)` pairs that later milestones extend.

- [ ] **Step 1: Extend the list.** In `tests/test_new_patch_inputs.py`, add these lines at the end of `NEW_PATCHES`, directly before its closing `]`:

```python
    ("drip", "drip"),
    ("edge-glow", "edgeglow"),
    ("contour", "contour"),
    ("hue-isolate", "hueiso"),
    ("bloom", "bloom"),
```

Nothing else in the file changes. The whole file after this step is:

```python
"""Input edge cases shared by the patches added in the new-patches plan."""

import os

import numpy as np
import pytest
from PIL import Image

from conftest import assert_valid_image

# (patch directory, output suffix). Each milestone appends its patches here.
NEW_PATCHES = [
    ("fft-phase", "fftphase"),
    ("zoom-blur", "zoomblur"),
    ("swirl", "swirl"),
    ("displace", "displace"),
    ("drip", "drip"),
    ("edge-glow", "edgeglow"),
    ("contour", "contour"),
    ("hue-isolate", "hueiso"),
    ("bloom", "bloom"),
]
NAMES = [name for name, _ in NEW_PATCHES]


def _gradient_array(size: int = 64) -> np.ndarray:
    yy, xx = np.mgrid[0:size, 0:size]
    return np.stack([xx * 4, yy * 4, (xx + yy) * 2], axis=2).clip(0, 255).astype(np.uint8)


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("mode", ["RGBA", "L", "P"])
def test_accepts_other_modes(run_tool, tmp_path, name, mode):
    """Transparent, greyscale and palette inputs all produce an RGB image the same size."""
    src = str(tmp_path / f"in-{mode}.png")
    img = Image.fromarray(_gradient_array())
    if mode == "RGBA":
        img = img.convert("RGBA")
        img.putalpha(128)
    else:
        img = img.convert(mode)
    img.save(src)
    out = str(tmp_path / "out.png")
    r = run_tool(name, f"{name}.py", [src, out])
    assert r.returncode == 0, r.stderr
    result = Image.open(out)
    assert result.mode == "RGB"
    assert result.size == (64, 64)


@pytest.mark.parametrize("name", [n for n in NAMES if n != "ascii"])
@pytest.mark.parametrize("size", [1, 2, 5])
def test_tiny_images(run_tool, tmp_path, name, size):
    src = str(tmp_path / "tiny.png")
    Image.fromarray(_gradient_array(64)[:size, :size]).save(src)
    out = str(tmp_path / "out.png")
    r = run_tool(name, f"{name}.py", [src, out])
    assert r.returncode == 0, r.stderr
    assert Image.open(out).size == (size, size)


@pytest.mark.parametrize("name,suffix", NEW_PATCHES)
def test_input_without_extension_defaults_to_png(run_tool, tmp_path, name, suffix):
    src = str(tmp_path / "photo")
    Image.fromarray(_gradient_array()).save(src, format="PNG")
    r = run_tool(name, f"{name}.py", [src])
    assert r.returncode == 0, r.stderr
    assert_valid_image(str(tmp_path / f"photo-{suffix}.png"))


@pytest.mark.parametrize("name", NAMES)
def test_explicit_jpeg_output(run_tool, tmp_workdir, name):
    tmp_path, img = tmp_workdir
    out = str(tmp_path / "out.jpg")
    r = run_tool(name, f"{name}.py", [img, out])
    assert r.returncode == 0, r.stderr
    assert Image.open(out).format == "JPEG"


@pytest.mark.parametrize("name,suffix", NEW_PATCHES)
def test_runs_through_op(run_op, tmp_workdir, name, suffix):
    tmp_path, img = tmp_workdir
    r = run_op([name, img])
    assert r.returncode == 0, r.stderr
    assert os.path.isfile(str(tmp_path / f"input-{suffix}.png"))
```

- [ ] **Step 2: Run it.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_new_patch_inputs.py`. Expected: every test passes. If a patch fails on a tiny or non-RGB image, fix that patch (the scripts above pass as written) and rerun.

- [ ] **Step 3: Commit.** Run `git add tests/test_new_patch_inputs.py`, then commit with the message `test(new-patches): input edge cases for drip, edge-glow, contour, hue-isolate, bloom` and the trailer the build note gives.


**End of milestone:** run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`. Expected: no failure outside the baseline recorded at the start of M2. Record the pass count in the closing report.

---


## M3: Cells, paint and depth

Patches that rebuild the image from regions or strokes, or blur it by depth.

**Start of milestone:** run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests` and record the failing tests as this milestone's baseline.


### Task 12: voronoi-mosaic

Brainstorm rank 6. On `_output/mclaren.jpg`: The car becomes faceted orange shards and the lawn crazy paving; with `--edges 2` the frame reads as a church window.

**Files:**
- Create: `voronoi-mosaic/voronoi-mosaic.py`, `voronoi-mosaic/requirements.txt`, `tests/test_voronoi_mosaic.py`, `_output/mclaren-voronoi.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `voronoi-mosaic <input> [output] [--size PX] [--jitter N] [--edges PX] [--seed N]`, default output `<base>-voronoi<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_voronoi_mosaic.py`:

```python
"""Tests for voronoi-mosaic tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestVoronoiMosaic:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("voronoi-mosaic", "voronoi-mosaic.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-voronoi.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("voronoi-mosaic", "voronoi-mosaic.py", [img, out, "--size", "12", "--edges", "2", "--seed", "4"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "size=12" in r.stderr
        assert "edges=2" in r.stderr

    def test_single_pixel_cells_are_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("voronoi-mosaic", "voronoi-mosaic.py", [img, out, "--size", "1", "--jitter", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_one_colour_per_cell(self, run_tool, tmp_workdir):
        """16-pixel cells on a 64x64 image give 16 seeds, so at most 16 colours."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "cells.png")
        r = run_tool("voronoi-mosaic", "voronoi-mosaic.py", [img, out, "--size", "16", "--seed", "1"])
        assert r.returncode == 0
        colours = {tuple(p) for p in _pixels(out).reshape(-1, 3)}
        assert 2 <= len(colours) <= 16

    def test_size_out_of_range(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("voronoi-mosaic", "voronoi-mosaic.py", [img, "--size", "0"])
        assert r.returncode != 0

    def test_missing_input(self, run_tool):
        r = run_tool("voronoi-mosaic", "voronoi-mosaic.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("voronoi-mosaic", "voronoi-mosaic.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_voronoi_mosaic.py`. Expected: FAIL, because `voronoi-mosaic/voronoi-mosaic.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `voronoi-mosaic/requirements.txt` with exactly:

```text
Pillow
numpy
scipy
```

- [ ] **Step 4: Write the patch.** Create `voronoi-mosaic/voronoi-mosaic.py`:

```python
#!/usr/bin/env python3
"""Split the image into irregular Voronoi cells filled with their mean colour, with optional dark leading."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
from scipy.spatial import cKDTree

LEADING = (20, 20, 20)


def main() -> None:
    parser = argparse.ArgumentParser(description="Voronoi stained-glass mosaic.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--size", type=int, default=24, help="Cell spacing in pixels, 1 to 200 (default: 24)")
    parser.add_argument("--jitter", type=float, default=1.0, help="Seed randomness, 0 (grid) to 1 (default: 1.0)")
    parser.add_argument("--edges", type=int, default=0, help="Leading width in pixels; 0 for none (default: 0)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (default: None)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 1 <= args.size <= 200:
        parser.error("--size must be between 1 and 200")
    if not 0.0 <= args.jitter <= 1.0:
        parser.error("--jitter must be between 0 and 1")
    if args.edges < 0:
        parser.error("--edges must be 0 or more")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    h, w, _ = arr.shape

    # Seeds sit on a grid of cell centres; at size 1 with no jitter every pixel is its own cell.
    rng = np.random.default_rng(args.seed)
    centres_y = np.arange((args.size - 1) / 2.0, h, args.size)
    centres_x = np.arange((args.size - 1) / 2.0, w, args.size)
    # An image smaller than one cell still gets a single seed.
    if centres_y.size == 0:
        centres_y = np.array([(h - 1) / 2.0])
    if centres_x.size == 0:
        centres_x = np.array([(w - 1) / 2.0])
    gy, gx = np.meshgrid(centres_y, centres_x, indexing="ij")
    seeds = np.column_stack([gy.ravel(), gx.ravel()])
    seeds += rng.uniform(-0.5, 0.5, seeds.shape) * args.jitter * args.size

    yy, xx = np.mgrid[0:h, 0:w]
    _, labels = cKDTree(seeds).query(np.column_stack([yy.ravel(), xx.ravel()]))
    counts = np.maximum(np.bincount(labels, minlength=len(seeds)), 1)
    means = np.stack([np.bincount(labels, weights=arr[:, :, c].ravel(), minlength=len(seeds)) / counts for c in range(3)], axis=1)
    result = means[labels].reshape(h, w, 3)

    if args.edges > 0:
        grid = labels.reshape(h, w)
        boundary = np.zeros((h, w), dtype=bool)
        boundary[1:, :] |= grid[1:, :] != grid[:-1, :]
        boundary[:, 1:] |= grid[:, 1:] != grid[:, :-1]
        if args.edges > 1:
            boundary = binary_dilation(boundary, iterations=args.edges - 1)
        result[boundary] = LEADING

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-voronoi{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved Voronoi mosaic to {out_path} (size={args.size}, jitter={args.jitter}, edges={args.edges}, seed={args.seed})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_voronoi_mosaic.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"voronoi-mosaic",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### voronoi-mosaic

Split the image into irregular Voronoi cells filled with their average colour, with optional dark leading like stained glass.

```bash
python3 ./voronoi-mosaic/voronoi-mosaic.py <input> [output] [--size PX] [--jitter N] [--edges PX] [--seed N]
```

Default: `--size 24 --jitter 1 --edges 0`

![voronoi-mosaic example](_output/mclaren-voronoi.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op voronoi-mosaic _output/mclaren.jpg _output/mclaren-voronoi.jpg --seed 1`. Then run `ls -la _output/mclaren-voronoi.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add voronoi-mosaic/voronoi-mosaic.py voronoi-mosaic/requirements.txt tests/test_voronoi_mosaic.py tests/test_op_cli.py README.md _output/mclaren-voronoi.jpg`, then commit with the message `feat(voronoi-mosaic): add voronoi-mosaic patch` and the trailer the build note gives.


### Task 13: oil-paint

Brainstorm rank 7. On `_output/mclaren.jpg`: Bonnet reflections become flat slabs of orange and cream; the silhouette and headlight stay sharp.

**Files:**
- Create: `oil-paint/oil-paint.py`, `oil-paint/requirements.txt`, `tests/test_oil_paint.py`, `_output/mclaren-oilpaint.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `oil-paint <input> [output] [--radius N]`, default output `<base>-oilpaint<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_oil_paint.py`:

```python
"""Tests for oil-paint tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _split(path: str) -> str:
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[:, :32] = (200, 0, 0)
    arr[:, 32:] = (0, 0, 200)
    Image.fromarray(arr).save(path)
    return path


def _noise(path: str) -> str:
    rng = np.random.default_rng(0)
    Image.fromarray(rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)).save(path)
    return path


class TestOilPaint:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("oil-paint", "oil-paint.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-oilpaint.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("oil-paint", "oil-paint.py", [img, out, "--radius", "3"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "radius=3" in r.stderr

    def test_zero_radius_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("oil-paint", "oil-paint.py", [img, out, "--radius", "0"])
        assert r.returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_keeps_hard_edges(self, run_tool, tmp_path):
        """A sharp two-colour boundary survives unchanged."""
        img = _split(str(tmp_path / "split.png"))
        out = str(tmp_path / "paint.png")
        r = run_tool("oil-paint", "oil-paint.py", [img, out, "--radius", "5"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_flattens_texture(self, run_tool, tmp_path):
        img = _noise(str(tmp_path / "noise.png"))
        out = str(tmp_path / "paint.png")
        r = run_tool("oil-paint", "oil-paint.py", [img, out, "--radius", "4"])
        assert r.returncode == 0
        assert _pixels(out).std() < _pixels(img).std() * 0.6

    def test_missing_input(self, run_tool):
        r = run_tool("oil-paint", "oil-paint.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("oil-paint", "oil-paint.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_oil_paint.py`. Expected: FAIL, because `oil-paint/oil-paint.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `oil-paint/requirements.txt` with exactly:

```text
Pillow
numpy
```

- [ ] **Step 4: Write the patch.** Create `oil-paint/oil-paint.py`:

```python
#!/usr/bin/env python3
"""Kuwahara filter: edge-preserving smoothing into flat painterly patches with crisp edges."""

import argparse
import os
import sys

import numpy as np
from PIL import Image


def integral(padded: np.ndarray) -> np.ndarray:
    """Summed-area table with a leading row and column of zeros."""
    table = np.zeros((padded.shape[0] + 1, padded.shape[1] + 1) + padded.shape[2:])
    table[1:, 1:] = padded.cumsum(axis=0).cumsum(axis=1)
    return table


def window_mean(table: np.ndarray, h: int, w: int, r: int, oy: int, ox: int) -> np.ndarray:
    """Mean over the (r+1)x(r+1) window whose top-left corner sits at (y+oy, x+ox) for every pixel."""
    k = r + 1
    y0, x0 = r + oy, r + ox
    total = (table[y0 + k:y0 + k + h, x0 + k:x0 + k + w] - table[y0:y0 + h, x0 + k:x0 + k + w]
             - table[y0 + k:y0 + k + h, x0:x0 + w] + table[y0:y0 + h, x0:x0 + w])
    return total / (k * k)


def main() -> None:
    parser = argparse.ArgumentParser(description="Oil-paint look with a Kuwahara filter.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--radius", type=int, default=6, help="Quadrant size in pixels, 0 to 16 (default: 6)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0 <= args.radius <= 16:
        parser.error("--radius must be between 0 and 16")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    h, w, _ = arr.shape
    r = args.radius

    if r == 0:
        result = arr
    else:
        lum = arr @ np.array([0.299, 0.587, 0.114])
        colour_table = integral(np.pad(arr, ((r, r), (r, r), (0, 0)), mode="edge"))
        lum_table = integral(np.pad(lum, r, mode="edge"))
        sq_table = integral(np.pad(lum ** 2, r, mode="edge"))

        # The four quadrants that share the pixel as a corner: pick the one with the least variance.
        quadrants = [(-r, -r), (-r, 0), (0, -r), (0, 0)]
        means = np.stack([window_mean(colour_table, h, w, r, oy, ox) for oy, ox in quadrants])
        variances = np.stack([
            window_mean(sq_table, h, w, r, oy, ox) - window_mean(lum_table, h, w, r, oy, ox) ** 2
            for oy, ox in quadrants
        ])
        best = np.argmin(variances, axis=0)
        result = np.take_along_axis(means, best[None, :, :, None], axis=0)[0]

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-oilpaint{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved oil-paint image to {out_path} (radius={args.radius})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_oil_paint.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"oil-paint",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### oil-paint

Kuwahara filter: smooth into flat painterly patches while keeping edges crisp.

```bash
python3 ./oil-paint/oil-paint.py <input> [output] [--radius N]
```

Default: `--radius 6`

![oil-paint example](_output/mclaren-oilpaint.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op oil-paint _output/mclaren.jpg _output/mclaren-oilpaint.jpg`. Then run `ls -la _output/mclaren-oilpaint.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add oil-paint/oil-paint.py oil-paint/requirements.txt tests/test_oil_paint.py tests/test_op_cli.py README.md _output/mclaren-oilpaint.jpg`, then commit with the message `feat(oil-paint): add oil-paint patch` and the trailer the build note gives.


### Task 14: tilt-shift

Brainstorm rank 9. On `_output/mclaren.jpg`: The car and the lawn at its wheels stay sharp; trees and near grass go soft, like a model railway.

**Files:**
- Create: `tilt-shift/tilt-shift.py`, `tilt-shift/requirements.txt`, `tests/test_tilt_shift.py`, `_output/mclaren-tiltshift.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `tilt-shift <input> [output] [--blur N] [--focus N] [--band N]`, default output `<base>-tiltshift<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_tilt_shift.py`:

```python
"""Tests for tilt-shift tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _checker(path: str) -> str:
    """Grey checkerboard of 2-pixel squares; grey is unaffected by the saturation lift."""
    yy, xx = np.mgrid[0:64, 0:64]
    grey = np.where(((yy // 2) + (xx // 2)) % 2 == 0, 200, 50).astype(np.uint8)
    Image.fromarray(np.repeat(grey[:, :, None], 3, axis=2)).save(path)
    return path


def _sharpness(arr: np.ndarray) -> float:
    return float(np.abs(np.diff(arr[:, :, 0], axis=1)).mean())


class TestTiltShift:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("tilt-shift", "tilt-shift.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-tiltshift.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("tilt-shift", "tilt-shift.py", [img, out, "--blur", "6", "--focus", "0.5", "--band", "0.2"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "focus=0.5" in r.stderr

    def test_zero_blur_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("tilt-shift", "tilt-shift.py", [img, out, "--blur", "0"])
        assert r.returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_band_stays_sharp(self, run_tool, tmp_path):
        """Rows in the focus band keep their detail; rows at the top lose it."""
        img = _checker(str(tmp_path / "checker.png"))
        out = str(tmp_path / "tilt.png")
        r = run_tool("tilt-shift", "tilt-shift.py", [img, out, "--blur", "8", "--focus", "0.5", "--band", "0.25"])
        assert r.returncode == 0
        px = _pixels(out)
        assert _sharpness(px[28:36]) > 3 * _sharpness(px[0:6])

    def test_blur_out_of_range(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("tilt-shift", "tilt-shift.py", [img, "--blur", "100"])
        assert r.returncode != 0

    def test_missing_input(self, run_tool):
        r = run_tool("tilt-shift", "tilt-shift.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("tilt-shift", "tilt-shift.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_tilt_shift.py`. Expected: FAIL, because `tilt-shift/tilt-shift.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `tilt-shift/requirements.txt` with exactly:

```text
Pillow
numpy
```

- [ ] **Step 4: Write the patch.** Create `tilt-shift/tilt-shift.py`:

```python
#!/usr/bin/env python3
"""Blur away from a horizontal focus band and lift saturation, so the scene reads as a miniature."""

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

LEVELS = 8


def main() -> None:
    parser = argparse.ArgumentParser(description="Fake miniature with a tilt-shift blur.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--blur", type=float, default=10.0, help="Largest blur radius, 0 to 40 (default: 10.0)")
    parser.add_argument("--focus", type=float, default=0.62, help="Centre of the sharp band as a fraction of height (default: 0.62)")
    parser.add_argument("--band", type=float, default=0.25, help="Height of the sharp band as a fraction of height (default: 0.25)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.blur <= 40.0:
        parser.error("--blur must be between 0 and 40")
    if not 0.0 <= args.focus <= 1.0:
        parser.error("--focus must be between 0 and 1")
    if not 0.0 <= args.band <= 1.0:
        parser.error("--band must be between 0 and 1")

    img = Image.open(args.input).convert("RGB")
    h = img.height

    if args.blur == 0:
        result_img = img
    else:
        # A stack of increasingly blurred copies; each row blends the two levels either side of its depth.
        stack = np.stack([
            np.array(img.filter(ImageFilter.GaussianBlur(args.blur * k / (LEVELS - 1))), dtype=np.float64)
            for k in range(LEVELS)
        ])
        rows = (np.arange(h) + 0.5) / h
        depth = np.clip((np.abs(rows - args.focus) - args.band / 2.0) / 0.3, 0.0, 1.0) * (LEVELS - 1)
        k0 = np.floor(depth).astype(int)
        k1 = np.minimum(k0 + 1, LEVELS - 1)
        frac = (depth - k0)[:, None, None]
        idx = np.arange(h)
        blended = stack[k0, idx] * (1.0 - frac) + stack[k1, idx] * frac
        result_img = Image.fromarray(np.clip(np.rint(blended), 0, 255).astype(np.uint8))
        strength = min(args.blur / 10.0, 1.0)
        result_img = ImageEnhance.Color(result_img).enhance(1.0 + 0.4 * strength)
        result_img = ImageEnhance.Contrast(result_img).enhance(1.0 + 0.1 * strength)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-tiltshift{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved tilt-shift image to {out_path} (blur={args.blur}, focus={args.focus}, band={args.band})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_tilt_shift.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"tilt-shift",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### tilt-shift

Blur away from a horizontal focus band and lift the colour, so the scene looks like a miniature.

```bash
python3 ./tilt-shift/tilt-shift.py <input> [output] [--blur N] [--focus N] [--band N]
```

Default: `--blur 10 --focus 0.62 --band 0.25`

![tilt-shift example](_output/mclaren-tiltshift.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op tilt-shift _output/mclaren.jpg _output/mclaren-tiltshift.jpg`. Then run `ls -la _output/mclaren-tiltshift.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add tilt-shift/tilt-shift.py tilt-shift/requirements.txt tests/test_tilt_shift.py tests/test_op_cli.py README.md _output/mclaren-tiltshift.jpg`, then commit with the message `feat(tilt-shift): add tilt-shift patch` and the trailer the build note gives.


### Task 15: flow-streak

Brainstorm rank 16. On `_output/mclaren.jpg`: The paint gets brushed strokes that wrap its curves; the grass becomes long combed strands.

**Files:**
- Create: `flow-streak/flow-streak.py`, `flow-streak/requirements.txt`, `tests/test_flow_streak.py`, `_output/mclaren-flow.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `flow-streak <input> [output] [--length N] [--sigma N]`, default output `<base>-flow<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_flow_streak.py`:

```python
"""Tests for flow-streak tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _horizontal_stripes(path: str) -> str:
    """4-pixel stripes that are constant along x, so the flow runs horizontally everywhere."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    for y in range(64):
        arr[y, :] = (230, 200, 40) if (y // 4) % 2 == 0 else (20, 40, 90)
    Image.fromarray(arr).save(path)
    return path


class TestFlowStreak:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("flow-streak", "flow-streak.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-flow.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("flow-streak", "flow-streak.py", [img, out, "--length", "6", "--sigma", "2"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "length=6" in r.stderr

    def test_zero_length_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("flow-streak", "flow-streak.py", [img, out, "--length", "0"])
        assert r.returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_streaks_follow_contours(self, run_tool, tmp_path):
        """Streaking along horizontal contours leaves horizontal stripes intact."""
        img = _horizontal_stripes(str(tmp_path / "stripes.png"))
        out = str(tmp_path / "flow.png")
        r = run_tool("flow-streak", "flow-streak.py", [img, out, "--length", "12"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_changes_a_photo(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "flow.png")
        r = run_tool("flow-streak", "flow-streak.py", [img, out, "--length", "12"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).mean() > 1

    def test_missing_input(self, run_tool):
        r = run_tool("flow-streak", "flow-streak.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("flow-streak", "flow-streak.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_flow_streak.py`. Expected: FAIL, because `flow-streak/flow-streak.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `flow-streak/requirements.txt` with exactly:

```text
Pillow
numpy
scipy
```

- [ ] **Step 4: Write the patch.** Create `flow-streak/flow-streak.py`:

```python
#!/usr/bin/env python3
"""Line-integral convolution along the image's edge tangents: brushed strokes that follow its contours."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates, sobel


def main() -> None:
    parser = argparse.ArgumentParser(description="Brush strokes that follow the image's contours.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--length", type=int, default=12, help="Steps traced each way along the flow, 0 to 40 (default: 12)")
    parser.add_argument("--sigma", type=float, default=3.0, help="Smoothing of the flow field (default: 3.0)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0 <= args.length <= 40:
        parser.error("--length must be between 0 and 40")
    if args.sigma < 0:
        parser.error("--sigma must be 0 or more")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    h, w, _ = arr.shape

    # Structure tensor: its dominant eigenvector is across edges; the tangent is 90 degrees from it.
    lum = arr @ np.array([0.299, 0.587, 0.114])
    gx, gy = sobel(lum, axis=1), sobel(lum, axis=0)
    jxx = gaussian_filter(gx * gx, args.sigma)
    jxy = gaussian_filter(gx * gy, args.sigma)
    jyy = gaussian_filter(gy * gy, args.sigma)
    angle = 0.5 * np.arctan2(2.0 * jxy, jxx - jyy) + np.pi / 2.0
    tx, ty = np.cos(angle), np.sin(angle)

    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    acc = arr.copy()
    count = 1
    for sign in (1.0, -1.0):
        px, py = xx.copy(), yy.copy()
        prev_x = prev_y = None
        for _ in range(args.length):
            vx = map_coordinates(tx, [py, px], order=0, mode="nearest")
            vy = map_coordinates(ty, [py, px], order=0, mode="nearest")
            if prev_x is None:
                vx, vy = sign * vx, sign * vy
            else:
                # The tangent has no preferred sign; keep stepping the way we were going.
                flip = vx * prev_x + vy * prev_y < 0
                vx, vy = np.where(flip, -vx, vx), np.where(flip, -vy, vy)
            px = np.clip(px + vx, 0, w - 1)
            py = np.clip(py + vy, 0, h - 1)
            prev_x, prev_y = vx, vy
            for c in range(3):
                acc[:, :, c] += map_coordinates(arr[:, :, c], [py, px], order=1, mode="nearest")
            count += 1

    result_img = Image.fromarray(np.clip(np.rint(acc / count), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-flow{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved flow-streak image to {out_path} (length={args.length}, sigma={args.sigma})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_flow_streak.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"flow-streak",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### flow-streak

Smear the image along its own contours for brushed, combed strokes.

```bash
python3 ./flow-streak/flow-streak.py <input> [output] [--length N] [--sigma N]
```

Default: `--length 12 --sigma 3`

![flow-streak example](_output/mclaren-flow.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op flow-streak _output/mclaren.jpg _output/mclaren-flow.jpg`. Then run `ls -la _output/mclaren-flow.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add flow-streak/flow-streak.py flow-streak/requirements.txt tests/test_flow_streak.py tests/test_op_cli.py README.md _output/mclaren-flow.jpg`, then commit with the message `feat(flow-streak): add flow-streak patch` and the trailer the build note gives.


### Task 16: shared input checks for voronoi-mosaic, oil-paint, tilt-shift, flow-streak

**Files:**
- Modify: `tests/test_new_patch_inputs.py` (`NEW_PATCHES`)

**Interfaces:**
- Consumes: every patch in this milestone; `run_tool`, `run_op`, `tmp_workdir`, `assert_valid_image` from `tests/conftest.py`.
- Produces: `NEW_PATCHES`, a list of `(patch directory, output suffix)` pairs that later milestones extend.

- [ ] **Step 1: Extend the list.** In `tests/test_new_patch_inputs.py`, add these lines at the end of `NEW_PATCHES`, directly before its closing `]`:

```python
    ("voronoi-mosaic", "voronoi"),
    ("oil-paint", "oilpaint"),
    ("tilt-shift", "tiltshift"),
    ("flow-streak", "flow"),
```

Nothing else in the file changes. The whole file after this step is:

```python
"""Input edge cases shared by the patches added in the new-patches plan."""

import os

import numpy as np
import pytest
from PIL import Image

from conftest import assert_valid_image

# (patch directory, output suffix). Each milestone appends its patches here.
NEW_PATCHES = [
    ("fft-phase", "fftphase"),
    ("zoom-blur", "zoomblur"),
    ("swirl", "swirl"),
    ("displace", "displace"),
    ("drip", "drip"),
    ("edge-glow", "edgeglow"),
    ("contour", "contour"),
    ("hue-isolate", "hueiso"),
    ("bloom", "bloom"),
    ("voronoi-mosaic", "voronoi"),
    ("oil-paint", "oilpaint"),
    ("tilt-shift", "tiltshift"),
    ("flow-streak", "flow"),
]
NAMES = [name for name, _ in NEW_PATCHES]


def _gradient_array(size: int = 64) -> np.ndarray:
    yy, xx = np.mgrid[0:size, 0:size]
    return np.stack([xx * 4, yy * 4, (xx + yy) * 2], axis=2).clip(0, 255).astype(np.uint8)


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("mode", ["RGBA", "L", "P"])
def test_accepts_other_modes(run_tool, tmp_path, name, mode):
    """Transparent, greyscale and palette inputs all produce an RGB image the same size."""
    src = str(tmp_path / f"in-{mode}.png")
    img = Image.fromarray(_gradient_array())
    if mode == "RGBA":
        img = img.convert("RGBA")
        img.putalpha(128)
    else:
        img = img.convert(mode)
    img.save(src)
    out = str(tmp_path / "out.png")
    r = run_tool(name, f"{name}.py", [src, out])
    assert r.returncode == 0, r.stderr
    result = Image.open(out)
    assert result.mode == "RGB"
    assert result.size == (64, 64)


@pytest.mark.parametrize("name", [n for n in NAMES if n != "ascii"])
@pytest.mark.parametrize("size", [1, 2, 5])
def test_tiny_images(run_tool, tmp_path, name, size):
    src = str(tmp_path / "tiny.png")
    Image.fromarray(_gradient_array(64)[:size, :size]).save(src)
    out = str(tmp_path / "out.png")
    r = run_tool(name, f"{name}.py", [src, out])
    assert r.returncode == 0, r.stderr
    assert Image.open(out).size == (size, size)


@pytest.mark.parametrize("name,suffix", NEW_PATCHES)
def test_input_without_extension_defaults_to_png(run_tool, tmp_path, name, suffix):
    src = str(tmp_path / "photo")
    Image.fromarray(_gradient_array()).save(src, format="PNG")
    r = run_tool(name, f"{name}.py", [src])
    assert r.returncode == 0, r.stderr
    assert_valid_image(str(tmp_path / f"photo-{suffix}.png"))


@pytest.mark.parametrize("name", NAMES)
def test_explicit_jpeg_output(run_tool, tmp_workdir, name):
    tmp_path, img = tmp_workdir
    out = str(tmp_path / "out.jpg")
    r = run_tool(name, f"{name}.py", [img, out])
    assert r.returncode == 0, r.stderr
    assert Image.open(out).format == "JPEG"


@pytest.mark.parametrize("name,suffix", NEW_PATCHES)
def test_runs_through_op(run_op, tmp_workdir, name, suffix):
    tmp_path, img = tmp_workdir
    r = run_op([name, img])
    assert r.returncode == 0, r.stderr
    assert os.path.isfile(str(tmp_path / f"input-{suffix}.png"))
```

- [ ] **Step 2: Run it.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_new_patch_inputs.py`. Expected: every test passes. If a patch fails on a tiny or non-RGB image, fix that patch (the scripts above pass as written) and rerun.

- [ ] **Step 3: Commit.** Run `git add tests/test_new_patch_inputs.py`, then commit with the message `test(new-patches): input edge cases for voronoi-mosaic, oil-paint, tilt-shift, flow-streak` and the trailer the build note gives.


**End of milestone:** run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`. Expected: no failure outside the baseline recorded at the start of M3. Record the pass count in the closing report.

---


## M4: Display, codec and glyph

Patches that simulate a medium. dither and jpeg-rot ramp only in steps; ascii does not ramp.

**Start of milestone:** run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests` and record the failing tests as this milestone's baseline.


### Task 17: crt

Brainstorm rank 10. On `_output/mclaren.jpg`: A 1990s TV grab: RGB stripes on the orange, bowed dark corners, scanlines through the grass.

**Files:**
- Create: `crt/crt.py`, `crt/requirements.txt`, `tests/test_crt.py`, `_output/mclaren-crt.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `crt <input> [output] [--amount N] [--pitch PX] [--curve N]`, default output `<base>-crt<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_crt.py`:

```python
"""Tests for crt tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _white(path: str) -> str:
    Image.new("RGB", (64, 64), (255, 255, 255)).save(path)
    return path


class TestCrt:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("crt", "crt.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-crt.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("crt", "crt.py", [img, out, "--amount", "0.5", "--pitch", "2", "--curve", "0.2"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "pitch=2" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("crt", "crt.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_mask_and_curvature(self, run_tool, tmp_path):
        """On white, red leads in the first mask stripe, and the curved corners go black."""
        img = _white(str(tmp_path / "white.png"))
        out = str(tmp_path / "crt.png")
        r = run_tool("crt", "crt.py", [img, out, "--pitch", "3"])
        assert r.returncode == 0
        px = _pixels(out)
        # With --pitch 3, columns 27-29 are a red stripe and 30-32 a green one.
        assert px[32, 28, 0] > px[32, 28, 1]
        assert px[32, 31, 1] > px[32, 31, 0]
        assert px[0, 0].max() <= 10

    def test_missing_input(self, run_tool):
        r = run_tool("crt", "crt.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("crt", "crt.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_crt.py`. Expected: FAIL, because `crt/crt.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `crt/requirements.txt` with exactly:

```text
Pillow
numpy
scipy
```

- [ ] **Step 4: Write the patch.** Create `crt/crt.py`:

```python
#!/usr/bin/env python3
"""Simulate a CRT: barrel curvature, an RGB aperture-grille mask, scanlines and a slight bloom."""

import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates


def main() -> None:
    parser = argparse.ArgumentParser(description="Show the image on a simulated CRT.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--amount", type=float, default=1.0, help="Effect strength, 0 to 1 (default: 1.0)")
    parser.add_argument("--pitch", type=int, default=3, help="Width of one mask stripe in pixels (default: 3)")
    parser.add_argument("--curve", type=float, default=0.12, help="Barrel curvature at full strength (default: 0.12)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")
    if args.pitch < 1:
        parser.error("--pitch must be at least 1")
    if args.curve < 0:
        parser.error("--curve must be 0 or more")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    h, w, _ = arr.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)

    # Barrel distortion in normalised coordinates; anything pushed past the frame is black.
    nx = xx / max(w - 1, 1) * 2.0 - 1.0
    ny = yy / max(h - 1, 1) * 2.0 - 1.0
    k = args.curve * args.amount
    scale = 1.0 + k * (nx ** 2 + ny ** 2)
    sx, sy = nx * scale, ny * scale
    inside = (np.abs(sx) <= 1.0) & (np.abs(sy) <= 1.0)
    src_x = (sx + 1.0) / 2.0 * (w - 1)
    src_y = (sy + 1.0) / 2.0 * (h - 1)
    warped = np.zeros_like(arr)
    for c in range(3):
        warped[:, :, c] = map_coordinates(arr[:, :, c], [src_y, src_x], order=1, mode="constant", cval=0.0)
    warped[~inside] = 0.0

    stripe = (xx // args.pitch).astype(int) % 3
    onehot = np.eye(3)[stripe]
    mask = 1.0 - args.amount * 0.6 * (1.0 - onehot)
    scan = 1.0 - args.amount * 0.4 * (0.5 - 0.5 * np.cos(2.0 * np.pi * yy / (2.0 * args.pitch)))
    result = warped * mask * scan[:, :, None]
    result += gaussian_filter(result, (2, 2, 0)) * 0.3 * args.amount

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-crt{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved CRT image to {out_path} (amount={args.amount}, pitch={args.pitch}, curve={args.curve})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_crt.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"crt",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### crt

Show the image on a simulated CRT: curved glass, an RGB stripe mask, scanlines and a slight glow.

```bash
python3 ./crt/crt.py <input> [output] [--amount N] [--pitch PX] [--curve N]
```

Default: `--amount 1 --pitch 3 --curve 0.12`

![crt example](_output/mclaren-crt.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op crt _output/mclaren.jpg _output/mclaren-crt.jpg`. Then run `ls -la _output/mclaren-crt.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add crt/crt.py crt/requirements.txt tests/test_crt.py tests/test_op_cli.py README.md _output/mclaren-crt.jpg`, then commit with the message `feat(crt): add crt patch` and the trailer the build note gives.


### Task 18: dither

Brainstorm rank 13. On `_output/mclaren.jpg`: At 2 levels the car becomes an orange and yellow crosshatch texture: the early-web GIF look.

**Files:**
- Create: `dither/dither.py`, `dither/requirements.txt`, `tests/test_dither.py`, `_output/mclaren-dither.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `dither <input> [output] [--method bayer|floyd|atkinson] [--levels N] [--matrix 2|4|8]`, default output `<base>-dither<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_dither.py`:

```python
"""Tests for dither tool."""

import numpy as np
import pytest
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestDither:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("dither", "dither.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-dither.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("dither", "dither.py", [img, out, "--method", "atkinson", "--levels", "3"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "method=atkinson" in r.stderr

    def test_full_levels_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("dither", "dither.py", [img, out, "--levels", "256"])
        assert r.returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    @pytest.mark.parametrize("method", ["bayer", "floyd", "atkinson"])
    def test_only_allowed_levels(self, run_tool, tmp_workdir, method):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / f"{method}.png")
        r = run_tool("dither", "dither.py", [img, out, "--method", method, "--levels", "2"])
        assert r.returncode == 0
        assert set(np.unique(_pixels(out))) <= {0, 255}

    def test_dither_keeps_average_tone(self, run_tool, tmp_workdir):
        """Dithering to two levels keeps each channel's mean close to the source."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "floyd.png")
        r = run_tool("dither", "dither.py", [img, out, "--method", "floyd"])
        assert r.returncode == 0
        assert np.abs(_pixels(out).mean(axis=(0, 1)) - _pixels(img).mean(axis=(0, 1))).max() < 12

    def test_levels_out_of_range(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("dither", "dither.py", [img, "--levels", "1"])
        assert r.returncode != 0

    def test_missing_input(self, run_tool):
        r = run_tool("dither", "dither.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("dither", "dither.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_dither.py`. Expected: FAIL, because `dither/dither.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `dither/requirements.txt` with exactly:

```text
Pillow
numpy
```

- [ ] **Step 4: Write the patch.** Create `dither/dither.py`:

```python
#!/usr/bin/env python3
"""Ordered (Bayer) or error-diffusion (Floyd-Steinberg, Atkinson) dithering to N levels per channel."""

import argparse
import os
import sys

import numpy as np
from PIL import Image

# (dy, dx, weight) for each error-diffusion kernel.
KERNELS = {
    "floyd": [(0, 1, 7 / 16), (1, -1, 3 / 16), (1, 0, 5 / 16), (1, 1, 1 / 16)],
    "atkinson": [(0, 1, 1 / 8), (0, 2, 1 / 8), (1, -1, 1 / 8), (1, 0, 1 / 8), (1, 1, 1 / 8), (2, 0, 1 / 8)],
}


def bayer(n: int) -> np.ndarray:
    m = np.array([[0, 2], [3, 1]])
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return m


def ordered(arr: np.ndarray, levels: int, size: int) -> np.ndarray:
    h, w, _ = arr.shape
    m = bayer(size)
    thresh = (m + 0.5) / (size * size) - 0.5
    tiled = np.tile(thresh, (h // size + 1, w // size + 1))[:h, :w]
    q = np.floor(arr / 255.0 * (levels - 1) + 0.5 + tiled[:, :, None])
    return np.clip(q, 0, levels - 1) * 255.0 / (levels - 1)


def diffuse(arr: np.ndarray, levels: int, kernel: list[tuple[int, int, float]]) -> np.ndarray:
    h, w, _ = arr.shape
    buf = arr.copy()
    step = 255.0 / (levels - 1)
    for y in range(h):
        for x in range(w):
            old = buf[y, x].copy()
            new = np.clip(np.round(old / step), 0, levels - 1) * step
            buf[y, x] = new
            err = old - new
            for dy, dx, weight in kernel:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w:
                    buf[ny, nx] += err * weight
    return buf


def main() -> None:
    parser = argparse.ArgumentParser(description="Dither to a few levels per channel.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--method", choices=["bayer", "floyd", "atkinson"], default="bayer", help="Dithering method (default: bayer)")
    parser.add_argument("--levels", type=int, default=2, help="Levels per channel, 2 to 256 (default: 2)")
    parser.add_argument("--matrix", type=int, choices=[2, 4, 8], default=8, help="Bayer matrix size (default: 8)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 2 <= args.levels <= 256:
        parser.error("--levels must be between 2 and 256")

    arr = np.array(Image.open(args.input).convert("RGB"), dtype=np.float64)
    if args.method == "bayer":
        result = ordered(arr, args.levels, args.matrix)
    else:
        result = diffuse(arr, args.levels, KERNELS[args.method])

    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-dither{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved dithered image to {out_path} (method={args.method}, levels={args.levels}, matrix={args.matrix})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_dither.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"dither",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### dither

Dither to N levels per channel with a Bayer matrix, or with Floyd–Steinberg or Atkinson error diffusion. Error diffusion takes a few seconds on the README image.

```bash
python3 ./dither/dither.py <input> [output] [--method bayer|floyd|atkinson] [--levels N] [--matrix 2|4|8]
```

Default: `--method bayer --levels 2 --matrix 8`

![dither example](_output/mclaren-dither.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op dither _output/mclaren.jpg _output/mclaren-dither.jpg`. Then run `ls -la _output/mclaren-dither.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add dither/dither.py dither/requirements.txt tests/test_dither.py tests/test_op_cli.py README.md _output/mclaren-dither.jpg`, then commit with the message `feat(dither): add dither patch` and the trailer the build note gives.


### Task 19: jpeg-rot

Brainstorm rank 14. On `_output/mclaren.jpg`: 8×8 blocks tile the lawn, orange bleeds into the grass, and the number plate grows halos.

**Files:**
- Create: `jpeg-rot/jpeg-rot.py`, `jpeg-rot/requirements.txt`, `tests/test_jpeg_rot.py`, `_output/mclaren-jpegrot.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `jpeg-rot <input> [output] [--quality N] [--generations N]`, default output `<base>-jpegrot<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_jpeg_rot.py`:

```python
"""Tests for jpeg-rot tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _split(path: str) -> str:
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[:, 32:] = 255
    Image.fromarray(arr).save(path)
    return path


class TestJpegRot:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("jpeg-rot", "jpeg-rot.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-jpegrot.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("jpeg-rot", "jpeg-rot.py", [img, out, "--quality", "5", "--generations", "10"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "generations=10" in r.stderr

    def test_zero_generations_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("jpeg-rot", "jpeg-rot.py", [img, out, "--generations", "0"])
        assert r.returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_damage_without_drift(self, run_tool, tmp_path):
        """The image degrades, but the shifts are undone so the content stays where it was."""
        img = _split(str(tmp_path / "split.png"))
        out = str(tmp_path / "rot.png")
        r = run_tool("jpeg-rot", "jpeg-rot.py", [img, out, "--quality", "5", "--generations", "20"])
        assert r.returncode == 0
        px = _pixels(out)
        assert np.abs(px - _pixels(img)).mean() > 1
        assert px[:, 8].mean() < 60
        assert px[:, 56].mean() > 190

    def test_missing_input(self, run_tool):
        r = run_tool("jpeg-rot", "jpeg-rot.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("jpeg-rot", "jpeg-rot.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_jpeg_rot.py`. Expected: FAIL, because `jpeg-rot/jpeg-rot.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `jpeg-rot/requirements.txt` with exactly:

```text
Pillow
```

- [ ] **Step 4: Write the patch.** Create `jpeg-rot/jpeg-rot.py`:

```python
#!/usr/bin/env python3
"""Re-encode as a low-quality JPEG many times, shifting a pixel each time so the artefacts pile up."""

import argparse
import io
import os
import sys

from PIL import Image, ImageChops


def main() -> None:
    parser = argparse.ArgumentParser(description="Generational JPEG loss.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--quality", type=int, default=10, help="JPEG quality per generation, 1 to 95 (default: 10)")
    parser.add_argument("--generations", type=int, default=30, help="Number of re-encodes, 0 to 200 (default: 30)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 1 <= args.quality <= 95:
        parser.error("--quality must be between 1 and 95")
    if not 0 <= args.generations <= 200:
        parser.error("--generations must be between 0 and 200")

    img = Image.open(args.input).convert("RGB")
    for _ in range(args.generations):
        # Shifting moves the 8x8 block grid, so each pass damages new places instead of settling.
        img = ImageChops.offset(img, 1, 0)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=args.quality, subsampling=2)
        buf.seek(0)
        img = Image.open(buf).convert("RGB")
    img = ImageChops.offset(img, -args.generations, 0)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-jpegrot{ext or '.png'}"

    img.save(out_path)
    print(f"Saved JPEG-rotted image to {out_path} (quality={args.quality}, generations={args.generations})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_jpeg_rot.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"jpeg-rot",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### jpeg-rot

Re-save as a low-quality JPEG many times, shifting a pixel each time so the damage piles up instead of settling.

```bash
python3 ./jpeg-rot/jpeg-rot.py <input> [output] [--quality N] [--generations N]
```

Default: `--quality 10 --generations 30`

![jpeg-rot example](_output/mclaren-jpegrot.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op jpeg-rot _output/mclaren.jpg _output/mclaren-jpegrot.jpg`. Then run `ls -la _output/mclaren-jpegrot.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add jpeg-rot/jpeg-rot.py jpeg-rot/requirements.txt tests/test_jpeg_rot.py tests/test_op_cli.py README.md _output/mclaren-jpegrot.jpg`, then commit with the message `feat(jpeg-rot): add jpeg-rot patch` and the trailer the build note gives.


### Task 20: ascii

Brainstorm rank 17. On `_output/mclaren.jpg`: The car becomes a field of orange `#%@`, reflections lighter `:-=`, the wheels dark gaps.

**Files:**
- Create: `ascii/ascii.py`, `ascii/requirements.txt`, `tests/test_ascii.py`, `_output/mclaren-ascii.jpg`
- Modify: `tests/test_op_cli.py` (`ALL_PATCHES`), `README.md` (append one section)

**Interfaces:**
- Consumes: the `run_tool` and `tmp_workdir` fixtures and `assert_valid_image` from `tests/conftest.py`.
- Produces: the command `ascii <input> [output] [--cell PX] [--charset CHARS]`, default output `<base>-ascii<ext or .png>`, and a one-line stderr summary starting `Saved`.

- [ ] **Step 1: Write the failing test.** Create `tests/test_ascii.py`:

```python
"""Tests for ascii tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _solid(path: str, colour: tuple[int, int, int]) -> str:
    Image.new("RGB", (64, 64), colour).save(path)
    return path


class TestAscii:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("ascii", "ascii.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-ascii.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("ascii", "ascii.py", [img, out, "--cell", "8", "--charset", " .oO@"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "cell=8" in r.stderr

    def test_keeps_size(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "size.png")
        r = run_tool("ascii", "ascii.py", [img, out, "--cell", "12"])
        assert r.returncode == 0
        assert Image.open(out).size == Image.open(img).size

    def test_brightness_picks_glyph(self, run_tool, tmp_path):
        """Black maps to the blank first character; white maps to a visible glyph in white."""
        black = _solid(str(tmp_path / "black.png"), (0, 0, 0))
        white = _solid(str(tmp_path / "white.png"), (255, 255, 255))
        dark_out, light_out = str(tmp_path / "dark.png"), str(tmp_path / "light.png")
        assert run_tool("ascii", "ascii.py", [black, dark_out]).returncode == 0
        assert run_tool("ascii", "ascii.py", [white, light_out]).returncode == 0
        assert _pixels(dark_out).max() == 0
        assert (_pixels(light_out) > 128).any()

    def test_image_smaller_than_cell(self, run_tool, tmp_path):
        tiny = str(tmp_path / "tiny.png")
        Image.new("RGB", (4, 4), (255, 255, 255)).save(tiny)
        r = run_tool("ascii", "ascii.py", [tiny, "--cell", "10"])
        assert r.returncode != 0
        assert "smaller than one" in r.stderr

    def test_missing_input(self, run_tool):
        r = run_tool("ascii", "ascii.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("ascii", "ascii.py", [])
        assert r.returncode != 0
```

- [ ] **Step 2: Run it and watch it fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_ascii.py`. Expected: FAIL, because `ascii/ascii.py` does not exist yet. The `test_no_args` test and any range-check test pass already, since a missing script also exits non-zero.

- [ ] **Step 3: Write the requirements file.** Create `ascii/requirements.txt` with exactly:

```text
Pillow>=10.1
numpy
```

- [ ] **Step 4: Write the patch.** Create `ascii/ascii.py`:

```python
#!/usr/bin/env python3
"""Replace grid cells with characters chosen by brightness, each in its cell's hue, on black."""

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def glyph_masks(charset: str, cell: int) -> np.ndarray:
    """One cell-by-cell coverage mask (0 to 1) per character, centred in its cell."""
    font = ImageFont.load_default(size=cell)
    masks = []
    for ch in charset:
        tile = Image.new("L", (cell, cell), 0)
        ImageDraw.Draw(tile).text((cell / 2, cell / 2), ch, fill=255, font=font, anchor="mm")
        masks.append(np.array(tile, dtype=np.float64) / 255.0)
    return np.stack(masks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the image as coloured ASCII characters.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--cell", type=int, default=10, help="Character cell size in pixels, 6 to 32 (default: 10)")
    parser.add_argument("--charset", default=" .:-=+*#%@", help="Characters from darkest to brightest (default: ' .:-=+*#%%@')")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 6 <= args.cell <= 32:
        parser.error("--cell must be between 6 and 32")
    if not args.charset:
        parser.error("--charset must not be empty")

    img = Image.open(args.input).convert("RGB")
    w, h = img.size
    cols, rows = w // args.cell, h // args.cell
    if cols == 0 or rows == 0:
        print(f"Error: image is smaller than one {args.cell}px cell", file=sys.stderr)
        sys.exit(1)

    small = np.array(img.resize((cols, rows), Image.BOX), dtype=np.float64)
    lum = small @ np.array([0.299, 0.587, 0.114])
    idx = np.clip((lum / 256.0 * len(args.charset)).astype(int), 0, len(args.charset) - 1)

    masks = glyph_masks(args.charset, args.cell)
    coverage = masks[idx].transpose(0, 2, 1, 3).reshape(rows * args.cell, cols * args.cell)
    # The glyph already carries the brightness, so draw it in the cell's hue at full brightness.
    hue = small * 255.0 / np.maximum(small.max(axis=2, keepdims=True), 1.0)
    colour = np.repeat(np.repeat(hue, args.cell, axis=0), args.cell, axis=1)

    result = np.zeros((h, w, 3))
    result[:rows * args.cell, :cols * args.cell] = colour * coverage[:, :, None]
    result_img = Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-ascii{ext or '.png'}"

    result_img.save(out_path)
    print(f"Saved ASCII image to {out_path} (cell={args.cell}, charset={len(args.charset)} characters)", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run the test and watch it pass.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_ascii.py`. Expected: every test passes.

- [ ] **Step 6: Register the patch.** In `tests/test_op_cli.py`, add `"ascii",` as a new line at the end of `ALL_PATCHES`, directly before its closing `]`. Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass.

- [ ] **Step 7: Document it.** Append this section to the end of `README.md`, after the last `### ` section, with one blank line before it:

````markdown
### ascii

Replace each cell with a character chosen by brightness, drawn in the cell's hue on black.

```bash
python3 ./ascii/ascii.py <input> [output] [--cell PX] [--charset CHARS]
```

Default: `--cell 10 --charset " .:-=+*#%@"`

![ascii example](_output/mclaren-ascii.jpg)
````

- [ ] **Step 8: Generate the README example.** From the repository root, run `PATH="/tmp/opimg-venv/bin:$PATH" ./op ascii _output/mclaren.jpg _output/mclaren-ascii.jpg`. Then run `ls -la _output/mclaren-ascii.jpg`. Expected: the file exists and is larger than 10 KB. Open it and check it matches the description at the top of this task.

- [ ] **Step 9: Commit.** Run `git add ascii/ascii.py ascii/requirements.txt tests/test_ascii.py tests/test_op_cli.py README.md _output/mclaren-ascii.jpg`, then commit with the message `feat(ascii): add ascii patch` and the trailer the build note gives.


### Task 21: shared input checks for crt, dither, jpeg-rot, ascii

**Files:**
- Modify: `tests/test_new_patch_inputs.py` (`NEW_PATCHES`)

**Interfaces:**
- Consumes: every patch in this milestone; `run_tool`, `run_op`, `tmp_workdir`, `assert_valid_image` from `tests/conftest.py`.
- Produces: `NEW_PATCHES`, a list of `(patch directory, output suffix)` pairs that later milestones extend.

- [ ] **Step 1: Extend the list.** In `tests/test_new_patch_inputs.py`, add these lines at the end of `NEW_PATCHES`, directly before its closing `]`:

```python
    ("crt", "crt"),
    ("dither", "dither"),
    ("jpeg-rot", "jpegrot"),
    ("ascii", "ascii"),
```

Nothing else in the file changes. The whole file after this step is:

```python
"""Input edge cases shared by the patches added in the new-patches plan."""

import os

import numpy as np
import pytest
from PIL import Image

from conftest import assert_valid_image

# (patch directory, output suffix). Each milestone appends its patches here.
NEW_PATCHES = [
    ("fft-phase", "fftphase"),
    ("zoom-blur", "zoomblur"),
    ("swirl", "swirl"),
    ("displace", "displace"),
    ("drip", "drip"),
    ("edge-glow", "edgeglow"),
    ("contour", "contour"),
    ("hue-isolate", "hueiso"),
    ("bloom", "bloom"),
    ("voronoi-mosaic", "voronoi"),
    ("oil-paint", "oilpaint"),
    ("tilt-shift", "tiltshift"),
    ("flow-streak", "flow"),
    ("crt", "crt"),
    ("dither", "dither"),
    ("jpeg-rot", "jpegrot"),
    ("ascii", "ascii"),
]
NAMES = [name for name, _ in NEW_PATCHES]


def _gradient_array(size: int = 64) -> np.ndarray:
    yy, xx = np.mgrid[0:size, 0:size]
    return np.stack([xx * 4, yy * 4, (xx + yy) * 2], axis=2).clip(0, 255).astype(np.uint8)


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("mode", ["RGBA", "L", "P"])
def test_accepts_other_modes(run_tool, tmp_path, name, mode):
    """Transparent, greyscale and palette inputs all produce an RGB image the same size."""
    src = str(tmp_path / f"in-{mode}.png")
    img = Image.fromarray(_gradient_array())
    if mode == "RGBA":
        img = img.convert("RGBA")
        img.putalpha(128)
    else:
        img = img.convert(mode)
    img.save(src)
    out = str(tmp_path / "out.png")
    r = run_tool(name, f"{name}.py", [src, out])
    assert r.returncode == 0, r.stderr
    result = Image.open(out)
    assert result.mode == "RGB"
    assert result.size == (64, 64)


@pytest.mark.parametrize("name", [n for n in NAMES if n != "ascii"])
@pytest.mark.parametrize("size", [1, 2, 5])
def test_tiny_images(run_tool, tmp_path, name, size):
    src = str(tmp_path / "tiny.png")
    Image.fromarray(_gradient_array(64)[:size, :size]).save(src)
    out = str(tmp_path / "out.png")
    r = run_tool(name, f"{name}.py", [src, out])
    assert r.returncode == 0, r.stderr
    assert Image.open(out).size == (size, size)


@pytest.mark.parametrize("name,suffix", NEW_PATCHES)
def test_input_without_extension_defaults_to_png(run_tool, tmp_path, name, suffix):
    src = str(tmp_path / "photo")
    Image.fromarray(_gradient_array()).save(src, format="PNG")
    r = run_tool(name, f"{name}.py", [src])
    assert r.returncode == 0, r.stderr
    assert_valid_image(str(tmp_path / f"photo-{suffix}.png"))


@pytest.mark.parametrize("name", NAMES)
def test_explicit_jpeg_output(run_tool, tmp_workdir, name):
    tmp_path, img = tmp_workdir
    out = str(tmp_path / "out.jpg")
    r = run_tool(name, f"{name}.py", [img, out])
    assert r.returncode == 0, r.stderr
    assert Image.open(out).format == "JPEG"


@pytest.mark.parametrize("name,suffix", NEW_PATCHES)
def test_runs_through_op(run_op, tmp_workdir, name, suffix):
    tmp_path, img = tmp_workdir
    r = run_op([name, img])
    assert r.returncode == 0, r.stderr
    assert os.path.isfile(str(tmp_path / f"input-{suffix}.png"))
```

- [ ] **Step 2: Run it.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_new_patch_inputs.py`. Expected: every test passes. If a patch fails on a tiny or non-RGB image, fix that patch (the scripts above pass as written) and rerun.

- [ ] **Step 3: Commit.** Run `git add tests/test_new_patch_inputs.py`, then commit with the message `test(new-patches): input edge cases for crt, dither, jpeg-rot, ascii` and the trailer the build note gives.


**End of milestone:** run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`. Expected: no failure outside the baseline recorded at the start of M4. Record the pass count in the closing report.

---
