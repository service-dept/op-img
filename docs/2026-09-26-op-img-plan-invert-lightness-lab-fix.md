---
title: invert-lightness LAB fix Implementation Plan
kind: plan
target: op-img
topic: invert-lightness-lab-fix
status: approved
written: 2026-09-26T04:20:30Z
by: claude
---

# invert-lightness LAB fix Implementation Plan

> **For agentic workers:** Execute this plan inline with superpowers:executing-plans, one task. You are headless: choose the conservative option when the plan is silent, record it in your closing report, and continue. No subagents, no whole-branch review.

**Goal:** `invert-lightness` produces a correct LAB lightness inversion on current Pillow again, and a test fails if it regresses.

**Architecture:** `invert-lightness/invert-lightness.py` converts to LAB, inverts L, and rebuilds the image with `Image.merge("LAB", [...])`. On Pillow 12.3.0, merging three `L`-mode bands into `LAB` corrupts the image: an unmodified RGB→LAB→merge→RGB round trip is 53.6% RMSE off the original, while `Image.fromarray(arr, "LAB")` round-trips at 0.4%. The fix rebuilds with `Image.fromarray(arr, "LAB")`.

**Tech Stack:** Python 3, Pillow 12.3.0, numpy, pytest.

**Spec:** Josh's request, 2026-09-26: fix the op-img invert-lightness bug found while rendering joshosborne.info figures. Evidence (session, 2026-09-26): with Pillow 12.3.0 the patch's output differs from the README's `_output/mclaren-invl.jpg` by 56.9% RMSE; with the fix it differs by 2.4%.

## Global Constraints

- Work only in your worktree. Never push, merge, rebase, or delete branches. Commit through the git-commit skill, staging by path. Trailer: `Co-Authored-By: Grok <noreply@x.ai>`.
- **Python environment outside the repository:** `python3 -m venv "$TMPDIR/opimg-venv"`, then `"$TMPDIR/opimg-venv/bin/pip" install pytest numpy Pillow scipy`. `.venv` is not gitignored here, so never create one in the worktree.
- The tests invoke each tool with `python3` from `PATH`, so run pytest with the venv first on `PATH`: `PATH="$TMPDIR/opimg-venv/bin:$PATH" python3 -m pytest -q tests`.
- **Run exactly one simple command per shell call.** No `&&`, `;`, or `|` chains and no subshells: a chained command cancels headless runs.
- **Known unrelated failures, out of scope:** `tests/test_bit_crush.py::TestBitCrush::test_default_args` and `tests/test_res_crush.py::TestResCrush::test_default_args` fail at the base commit (128 pass, 2 fail). Do not touch them; report them.
- Change nothing but `invert-lightness/invert-lightness.py` and `tests/test_invert_lightness.py`. Do not regenerate `_output/` images.

## Review Focus

1. **The test must catch the bug.** The current tests pass on the broken code: they only check that pixels changed and that a double inversion is within MAE 50. The new tests must fail on the current code before the fix.
2. **Lossy LAB.** Pillow's LAB conversion is lossy. On the suite's 64×64 gradient (measured 2026-09-26, Pillow 12.3.0), mean lightness error is 17.3 (broken) against 2.9 (fixed), with threshold 8. Double-inversion MAE is 47.3 (broken) against 17.8 (fixed), with threshold 30. Keep these thresholds unless your measurements differ; if they do, report both values.

---

### Task 1: Regression tests, then the fix

**Files:** modify `tests/test_invert_lightness.py` and `invert-lightness/invert-lightness.py`.

- [ ] **Step 1: Add failing tests** to `TestInvertLightness` in `tests/test_invert_lightness.py`:

```python
    def test_lightness_is_inverted(self, run_tool, tmp_workdir):
        """L in the output is 255 - L of the input, pixel for pixel, within LAB rounding."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "inverted.png")
        r = run_tool("invert-lightness", "invert-lightness.py", [img, out])
        assert r.returncode == 0
        l_in = np.array(Image.open(img).convert("LAB"), dtype=np.float64)[:, :, 0]
        l_out = np.array(Image.open(out).convert("LAB"), dtype=np.float64)[:, :, 0]
        err = np.mean(np.abs(l_out - (255 - l_in)))
        assert err < 8, f"Mean lightness error too high: {err:.1f}"

    def test_involution_is_close(self, run_tool, tmp_workdir):
        """Two inversions return close to the original (a corrupting rebuild does not)."""
        tmp_path, img = tmp_workdir
        mid = str(tmp_path / "mid.png")
        out = str(tmp_path / "roundtrip.png")
        assert run_tool("invert-lightness", "invert-lightness.py", [img, mid]).returncode == 0
        assert run_tool("invert-lightness", "invert-lightness.py", [mid, out]).returncode == 0
        original = np.array(Image.open(img), dtype=np.float64)
        roundtrip = np.array(Image.open(out), dtype=np.float64)
        mae = np.mean(np.abs(original - roundtrip))
        assert mae < 30, f"Mean absolute error too high: {mae:.1f}"
```

- [ ] **Step 2: Run them and confirm they fail** on the current code: `PATH="$TMPDIR/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_invert_lightness.py`. Record both failure messages. If either passes, the tolerance does not separate bug from fix: measure the values on the current code, choose a threshold between the broken and fixed values, and report both numbers.

- [ ] **Step 3: Fix.** In `invert-lightness/invert-lightness.py`, replace

```python
    lab_out = Image.merge("LAB", [Image.fromarray(arr[:, :, c]) for c in range(3)])
```

with

```python
    # Image.merge("LAB", ...) of L-mode bands corrupts the image on Pillow 12; build the LAB image directly.
    lab_out = Image.fromarray(arr, "LAB")
```

- [ ] **Step 4: Run the file's tests, then the whole suite.** Expected: `tests/test_invert_lightness.py` all pass (8); the whole suite 130 pass and 2 fail (the two known failures above, unchanged).

- [ ] **Step 5: Check the README example.** Run the fixed tool on `_output/mclaren.jpg` to a file in `$TMPDIR` (not in the repo), and report its RMSE against `_output/mclaren-invl.jpg` with numpy. Expected: about 0.024 (2.4%) of 255.

- [ ] **Step 6: Commit** `fix(invert-lightness): rebuild LAB with fromarray on Pillow 12`, with a body stating why. Then write the closing report with handoff-write (same target and topic): the commit, the failing-then-passing test output, the suite counts, the README RMSE, and the two known failures.
