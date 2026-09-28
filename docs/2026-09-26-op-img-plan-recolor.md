---
title: recolor
kind: plan
target: op-img
topic: recolor
status: approved
written: 2026-09-26T19:52:44Z
by: claude
---

# recolor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task, inline. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `recolor` patch that repaints an image's most prevalent colours with colours the user gives, keeping their light and shade.

**Architecture:** One Python patch directory, `recolor/`, following every other Python patch. It converts to LAB, finds colour families with k-means on a*b* (chroma only), merges families of one hue, drops greys, ranks by pixel count, and moves each pixel's hue, chroma and lightness toward the target by a soft membership (hue closeness times colourfulness). `--amount` blends in RGB, so 0 is the exact original.

**Tech Stack:** Python 3.10+, Pillow, numpy; pytest with the `run_tool` and `tmp_workdir` fixtures in `tests/conftest.py`.

**Spec:** `/home/jmo/linda/docs/2026-09-26-op-img-spec-recolor.md`

## Global Constraints

- Python 3.10+, Pillow and numpy only.
- Change only: create `recolor/recolor.py`, `recolor/requirements.txt`, `tests/test_recolor.py`, `_output/mclaren-recolor.jpg`; modify `tests/test_op_cli.py` (one list entry), `tests/test_new_patch_inputs.py` (one list entry), `README.md` (one section). Do not change `op` or any other patch.
- Pillow's LAB mode stores a* and b* as signed bytes; the code handles this. Never use `Image.merge("LAB", ...)`: it corrupts images on Pillow 12.
- Tests run with `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`. If `/tmp/opimg-venv` is missing, create it with `python3 -m venv /tmp/opimg-venv`, then `/tmp/opimg-venv/bin/pip install pytest numpy Pillow scipy`.
- Base: the integration branch `recolor`, created from `stack-patches` at `c977922`. The suite there shows `402 passed`; re-measure at the start and record it.
- Headless build worker: run one simple command per shell call. Do not chain commands with `&&`, `;` or `|`.
- Commit once per task, staging files by path. Never `git add -A` or `git add .`.

## Review Focus

1. An image whose top colour spans several saturations (lit and shaded paint): all of it is one colour and moves together. Pinned by `test_two_colours_replace_the_top_two` (the orange ramp must not take both slots).
2. A grey or black-and-white image: nothing is repainted. Pinned by `test_grey_image_is_unchanged`.
3. `--amount 0`: the exact original, so the patch can ramp in the hero loop. Pinned by `test_amount_zero_is_identity`.
4. A typo in a colour (`#12345z`): a clear error, exit 2. Pinned by `test_bad_colour_is_an_error`.
5. Transparent, greyscale and palette inputs, tiny images, no extension, JPEG output, running through `op`: pinned by adding `("recolor", "recolor")` to `tests/test_new_patch_inputs.py`.

## File Structure

- `recolor/recolor.py`: the patch.
- `recolor/requirements.txt`: `Pillow` and `numpy`, one per line.
- `tests/test_recolor.py`: the patch's tests.
- `tests/test_op_cli.py`, `tests/test_new_patch_inputs.py`: one list entry each.
- `README.md`: a `### recolor` section in the colour group.
- `_output/mclaren-recolor.jpg`: the README example.

---

### Task 1: The recolor patch

**Files:**
- Create: `recolor/recolor.py`, `recolor/requirements.txt`
- Test: `tests/test_recolor.py`
- Modify: `tests/test_op_cli.py`, `tests/test_new_patch_inputs.py`

**Interfaces:**
- Produces: `recolor(image, colours, amount, clusters) -> Image.Image`, CLI `recolor.py <input> [output] [--colors C1,C2] [--amount N] [--clusters N]`, default output suffix `-recolor`.

- [ ] **Step 1: Record the baseline.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`. Expected: `402 passed`.

- [ ] **Step 2: Write the failing tests.** Create `tests/test_recolor.py` with exactly:

```python
"""Tests for recolor tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _two_colour_image(path):
    """Left 40 columns orange, right 24 columns green, each with a lightness ramp, 64x64."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    ramp = np.linspace(0.6, 1.0, 64)[:, None]
    arr[:, :40] = (np.array([230, 120, 30])[None, None, :] * ramp[:, :, None]).astype(np.uint8)
    arr[:, 40:] = (np.array([60, 150, 50])[None, None, :] * ramp[:, :, None]).astype(np.uint8)
    Image.fromarray(arr).save(path)
    return path


def _mean(path, cols):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float64)[:, cols].reshape(-1, 3).mean(0)


class TestRecolor:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("recolor", "recolor.py", [img])
        assert r.returncode == 0, r.stderr
        assert_valid_image(str(tmp_path / "input-recolor.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        r = run_tool("recolor", "recolor.py", [img, out, "--colors", "#1e3a8a"])
        assert r.returncode == 0, r.stderr
        assert_valid_image(out)

    def test_amount_zero_is_identity(self, run_tool, tmp_path):
        img = _two_colour_image(str(tmp_path / "two.png"))
        out = str(tmp_path / "out.png")
        r = run_tool("recolor", "recolor.py", [img, out, "--colors", "#1e3a8a", "--amount", "0"])
        assert r.returncode == 0, r.stderr
        assert np.array_equal(np.asarray(Image.open(out)), np.asarray(Image.open(img)))

    def test_one_colour_replaces_the_most_prevalent(self, run_tool, tmp_path):
        img = _two_colour_image(str(tmp_path / "two.png"))
        out = str(tmp_path / "out.png")
        r = run_tool("recolor", "recolor.py", [img, out, "--colors", "#1e3a8a"])
        assert r.returncode == 0, r.stderr
        before_left, after_left = _mean(img, slice(0, 40)), _mean(out, slice(0, 40))
        assert after_left[2] > after_left[0], f"orange area should turn blue: {after_left}"
        assert before_left[0] > before_left[2]
        assert np.abs(_mean(out, slice(44, 64)) - _mean(img, slice(44, 64))).max() < 6, "the green area should barely change"

    def test_two_colours_replace_the_top_two(self, run_tool, tmp_path):
        img = _two_colour_image(str(tmp_path / "two.png"))
        out = str(tmp_path / "out.png")
        r = run_tool("recolor", "recolor.py", [img, out, "--colors", "#1e3a8a,#facc15"])
        assert r.returncode == 0, r.stderr
        left, right = _mean(out, slice(0, 36)), _mean(out, slice(44, 64))
        assert left[2] > left[0], f"orange area should turn blue: {left}"
        assert right[0] > right[2] and right[1] > right[2], f"green area should turn yellow: {right}"

    def test_keeps_light_and_shade(self, run_tool, tmp_path):
        img = _two_colour_image(str(tmp_path / "two.png"))
        out = str(tmp_path / "out.png")
        assert run_tool("recolor", "recolor.py", [img, out, "--colors", "#1e3a8a"]).returncode == 0
        arr = np.asarray(Image.open(out).convert("L"), dtype=np.float64)[:, :36]
        assert arr[-8:].mean() > arr[:8].mean() + 10, "the lightness ramp should survive"

    def test_grey_image_is_unchanged(self, run_tool, tmp_path):
        grey = np.tile(np.linspace(0, 255, 64, dtype=np.uint8)[None, :, None], (64, 1, 3))
        img = str(tmp_path / "grey.png")
        Image.fromarray(grey).save(img)
        out = str(tmp_path / "out.png")
        r = run_tool("recolor", "recolor.py", [img, out, "--colors", "#ec4899"])
        assert r.returncode == 0, r.stderr
        assert np.abs(np.asarray(Image.open(out), dtype=int) - grey.astype(int)).max() <= 1

    def test_bad_colour_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("recolor", "recolor.py", [img, "--colors", "#12345z"])
        assert r.returncode == 2
        assert "not a colour" in r.stderr

    def test_too_many_colours_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("recolor", "recolor.py", [img, "--colors", "red,blue", "--clusters", "2"])
        assert r.returncode == 2
        assert "fewer colours" in r.stderr

    def test_missing_input(self, run_tool):
        r = run_tool("recolor", "recolor.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()

    def test_no_args(self, run_tool):
        r = run_tool("recolor", "recolor.py", [])
        assert r.returncode != 0
```

- [ ] **Step 3: Register the patch in the two lists.** In `tests/test_op_cli.py`, in `ALL_PATCHES`, add the line `    "recolor",` directly after the line `    "ascii",`. In `tests/test_new_patch_inputs.py`, in `NEW_PATCHES`, add the line `    ("recolor", "recolor"),` directly after the line `    ("ascii", "ascii"),`.

- [ ] **Step 4: Run the tests and confirm they fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_recolor.py`. Expected: all 11 fail (the script does not exist yet).

- [ ] **Step 5: Write the patch.** Create `recolor/requirements.txt` with the two lines `Pillow` and `numpy`. Create `recolor/recolor.py` with exactly this, then make it executable with `chmod +x recolor/recolor.py`:

```python
#!/usr/bin/env python3
"""Repaint an image's most prevalent colours with the colours you give, keeping their light and shade."""

import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageColor

NEUTRAL_CHROMA = 12.0  # a*b* distance below which a colour family counts as grey, black or white
HUE_WIDTH = np.radians(22)  # how far in hue a family reaches (standard deviation)
MERGE_HUE = np.radians(30)  # k-means centres closer than this in hue are one colour


def to_lab(image: Image.Image) -> np.ndarray:
    """RGB image to float L, a, b arrays. Pillow stores a and b as signed bytes."""
    lab = np.array(image.convert("LAB"), dtype=np.int16)
    lab[:, :, 1:] = np.where(lab[:, :, 1:] > 127, lab[:, :, 1:] - 256, lab[:, :, 1:])
    return lab.astype(np.float64)


def from_lab(lab: np.ndarray) -> Image.Image:
    out = np.rint(lab)
    out[:, :, 0] = np.clip(out[:, :, 0], 0, 255)
    out[:, :, 1:] = np.clip(out[:, :, 1:], -128, 127) % 256
    # Image.merge("LAB", ...) corrupts the image on Pillow 12; build the LAB image directly.
    return Image.fromarray(out.astype(np.uint8), "LAB").convert("RGB")


def colour_families(ab: np.ndarray, k: int, seed: int = 0) -> np.ndarray:
    """k-means on a*b* (chroma only, so light and shadow of one colour stay together). Returns k centres."""
    rng = np.random.default_rng(seed)
    sample = ab[rng.choice(len(ab), size=min(len(ab), 20000), replace=False)]
    centres = [sample[rng.integers(len(sample))]]
    for _ in range(1, k):
        d = np.min(((sample[:, None, :] - np.array(centres)[None]) ** 2).sum(-1), axis=1)
        if d.sum() == 0:
            break
        centres.append(sample[rng.choice(len(sample), p=d / d.sum())])
    centres = np.array(centres)
    for _ in range(20):
        labels = ((sample[:, None, :] - centres[None]) ** 2).sum(-1).argmin(1)
        centres = np.array([sample[labels == i].mean(0) if np.any(labels == i) else centres[i] for i in range(len(centres))])
    return centres


def rank_families(ab: np.ndarray, centres: np.ndarray) -> list[dict]:
    """Merge k-means centres of one hue (light and saturated orange are one colour), drop greys,
    and rank what is left by how many pixels it covers."""
    labels = ((ab[:, None, :] - centres[None]) ** 2).sum(-1).argmin(1)
    counts = np.bincount(labels, minlength=len(centres))
    groups = []
    for i in np.argsort(-counts):
        chroma = float(np.hypot(*centres[i]))
        if counts[i] == 0 or chroma < NEUTRAL_CHROMA:
            continue
        hue = float(np.arctan2(centres[i][1], centres[i][0]))
        for g in groups:
            if abs(np.angle(np.exp(1j * (hue - g["hue"])))) < MERGE_HUE:
                g["members"].append(i)
                g["count"] += int(counts[i])
                break
        else:
            groups.append({"hue": hue, "members": [i], "count": int(counts[i])})
    for g in groups:
        sel = np.isin(labels, g["members"])
        g["pixels"] = sel
        mean_ab = ab[sel].mean(0)
        g["hue"] = float(np.arctan2(mean_ab[1], mean_ab[0]))
        g["chroma"] = float(np.hypot(ab[sel, 0], ab[sel, 1]).mean())
    return sorted(groups, key=lambda g: -g["count"])


def recolor(image: Image.Image, colours: list[tuple[int, int, int]], amount: float, clusters: int) -> Image.Image:
    if amount <= 0:
        return image.copy()
    src = np.array(image, dtype=np.float64)
    lab = to_lab(image)
    h, w, _ = lab.shape
    L = lab[:, :, 0].reshape(-1)
    ab = lab[:, :, 1:].reshape(-1, 2)
    chroma = np.hypot(ab[:, 0], ab[:, 1])
    hue = np.arctan2(ab[:, 1], ab[:, 0])
    families = rank_families(ab, colour_families(ab, clusters))
    targets = families[:len(colours)]
    if not targets:
        return image.copy()
    # A pixel belongs to a family by how close its hue is, scaled by how colourful it is, so every
    # shade of one colour moves together and near-greys barely move.
    colourful = np.clip((chroma - 4.0) / 16.0, 0.0, 1.0)
    fam_hues = [f["hue"] for f in targets]
    member = []
    for fh in fam_hues:
        dh = np.angle(np.exp(1j * (hue - fh)))
        member.append(np.exp(-0.5 * (dh / HUE_WIDTH) ** 2) * colourful)
    member = np.array(member)
    total = member.sum(0)
    member = np.where(total > 1, member / np.maximum(total, 1e-9), member)
    new_l, new_c, new_h = L.copy(), chroma.copy(), hue.copy()
    for m, fam, fh, colour in zip(member, targets, fam_hues, colours):
        t = to_lab(Image.new("RGB", (1, 1), colour))[0, 0]
        th, tc = np.arctan2(t[2], t[1]), np.hypot(t[1], t[2])
        fl, fc = L[fam["pixels"]].mean(), fam["chroma"]
        # Keep each pixel's light and shade relative to its family; move hue and chroma to the target.
        new_l += m * (t[0] - fl)
        new_c *= 1 + m * (tc / max(fc, 1e-6) - 1)
        new_h += m * np.angle(np.exp(1j * (th - fh)))
    new_lab = np.stack([new_l, new_c * np.cos(new_h), new_c * np.sin(new_h)], 1).reshape(h, w, 3)
    out = np.array(from_lab(new_lab), dtype=np.float64)
    blend = (amount * np.clip(member.sum(0), 0, 1)).reshape(h, w, 1)
    result = src + blend * (out - src)
    return Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8))


def parse_colours(value: str) -> list[tuple[int, int, int]]:
    colours = []
    for part in value.split(","):
        part = part.strip()
        try:
            colours.append(ImageColor.getrgb(part)[:3])
        except ValueError:
            raise argparse.ArgumentTypeError(f"not a colour: '{part}' (use hex like #ec4899 or a name like pink)")
    if not colours:
        raise argparse.ArgumentTypeError("give at least one colour")
    return colours


def main() -> None:
    parser = argparse.ArgumentParser(description="Repaint the most prevalent colours with the colours you give.")
    parser.add_argument("input", help="Input image path")
    parser.add_argument("output", nargs="?", default=None, help="Output image path")
    parser.add_argument("--colors", type=parse_colours, default=parse_colours("#ec4899"),
                        help="Comma-separated colours, most prevalent first, e.g. '#ec4899,#1e3a8a' (default: #ec4899)")
    parser.add_argument("--amount", type=float, default=1.0, help="Strength, 0 (original) to 1 (full swap) (default: 1.0)")
    parser.add_argument("--clusters", type=int, default=6, help="Colour families to find, 2 to 16 (default: 6)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    if not 0.0 <= args.amount <= 1.0:
        parser.error("--amount must be between 0 and 1")
    if not 2 <= args.clusters <= 16:
        parser.error("--clusters must be between 2 and 16")
    if len(args.colors) >= args.clusters:
        parser.error("give fewer colours than --clusters")

    img = Image.open(args.input).convert("RGB")
    result = recolor(img, args.colors, args.amount, args.clusters)

    if args.output:
        out_path = args.output
    else:
        base, ext = os.path.splitext(args.input)
        out_path = f"{base}-recolor{ext or '.png'}"

    result.save(out_path)
    print(f"Saved recolored image to {out_path} (colors={len(args.colors)}, amount={args.amount}, clusters={args.clusters})", file=sys.stderr)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run the patch tests.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_recolor.py`. Expected: `11 passed`.

- [ ] **Step 7: Run the full suite.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`. Expected: `422 passed` at a base of 402 (11 recolor tests plus 9 new input checks), no failures.

- [ ] **Step 8: Commit.** Stage `recolor/recolor.py`, `recolor/requirements.txt`, `tests/test_recolor.py`, `tests/test_op_cli.py` and `tests/test_new_patch_inputs.py` by path, and commit with the subject `feat(recolor): repaint the most prevalent colours` and the trailer the build note gives.

### Task 2: README section and example

**Files:**
- Modify: `README.md`
- Create: `_output/mclaren-recolor.jpg`

- [ ] **Step 1: Add the section.** In `README.md`, directly before the line `### dot-halftone`, insert this section followed by one blank line:

````markdown
### recolor

Repaint the image's most prevalent colours with the colours you give, most prevalent first, keeping their light and shade. Greys, black and white are left alone.

```bash
python3 ./recolor/recolor.py <input> [output] [--colors C1,C2] [--amount N] [--clusters N]
```

Default: `--colors "#ec4899" --amount 1 --clusters 6`

Example: `--colors "#1e3a8a,#facc15"`

![recolor example](_output/mclaren-recolor.jpg)
````

- [ ] **Step 2: Generate the example.** From the repository root run `PATH="/tmp/opimg-venv/bin:$PATH" ./op recolor _output/mclaren.jpg _output/mclaren-recolor.jpg --colors "#1e3a8a,#facc15"`, then `ls -la _output/mclaren-recolor.jpg`. Expected: the file exists and is larger than 10 KB. Open it: the orange car is deep blue with its reflections intact, and the grass is yellow.

- [ ] **Step 3: Run the full suite.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`. Expected: the same count as Task 1 Step 7, no failures.

- [ ] **Step 4: Commit.** Stage `README.md` and `_output/mclaren-recolor.jpg` by path, and commit with the subject `docs(readme): recolor` and the trailer the build note gives.

---

## Self-review

- Spec coverage: behaviour, colours, prevalence ranking, merging of one hue, greys untouched, light and shade kept, amount 0 identity, clusters bound, errors, conventions (Task 1); README and example (Task 2).
- Pre-checked by the planning session on a scratch copy of `stack-patches` at `c977922`: the full suite showed `422 passed` with this exact code and these tests; renders on the README photo gave a pink car (one colour), a pink car on blue grass (two colours), and a blue car on yellow grass (the README example).
