---
title: stack-patches
kind: plan
target: op-img
topic: stack-patches
status: approved
written: 2026-09-26T17:35:50Z
by: claude
---

# Stack Patches Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task, inline. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let one `op` command run several patches in sequence, each on the previous result, joined with `+`, and document it in the README.

**Architecture:** A dispatcher-only change to `op` (bash). When any argument is a literal `+`, `op` splits its arguments into steps, validates every step before running anything, copies the input into a temporary directory, and runs each patch there on the previous step's output using the patch's own default output name, so suffixes accumulate exactly as in a manual chain. The last step writes straight to the explicit output path when one is given (so that path's extension picks the format); otherwise the final file is copied beside the input. No patch changes.

**Tech Stack:** bash (`op`), pytest with the existing `run_op` and `tmp_workdir` fixtures in `tests/conftest.py`, Pillow and numpy in tests.

**Spec:** Josh's request in the interactive session on 2026-09-26: stacking patches in one command without `&&`, as sketched there (`op pixel-sort --by hue + fold + polar photo.jpg`), refined in this plan to put the input first, matching op's existing `<patch> <input> [output] [options]` form; plus a README update describing the feature. There is no separate spec document.

## Global Constraints

- Change only `op`, `tests/test_op_cli.py` and `README.md`. No patch directory changes.
- Single-patch behaviour must not change: `op <patch> ...` without a `+` argument still `exec`s the patch directly, and `op`, `op --help`, `op --list` and `op --info <patch>` behave as before (the existing `TestHelp` and `TestDispatch` classes pin this).
- Stack syntax: `op <patch> <input> [output] [options] + <patch> [options] + ...`. The input is the first argument after the first patch. The output, if any, is the next argument when it does not start with `-`. Later steps take only options.
- Errors go to stderr: `Error: unknown patch '<name>'` (exit 1), `Error: empty step <k> in stack; put a patch name after each '+'` (exit 1), `Error: file not found: <input>` (exit 1), `Usage: ...` when the first step has no input (exit 1), and `Error: step <k> (<patch>) failed` followed by the patch's own stderr, exiting with the patch's exit code. In every error case no output file is written.
- Success prints one line to stderr: `Stacked <n> patches → <path>`. Nothing goes to stdout.
- Tests run with `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`. If `/tmp/opimg-venv` is missing, create it with `python3 -m venv /tmp/opimg-venv`, then `/tmp/opimg-venv/bin/pip install pytest numpy Pillow scipy`.
- Base: the integration branch `stack-patches`, created from `main` after PR #3 (17 new patches, `new-patches`) is merged. At that base the suite is expected to show `388 passed`; re-measure at the start and record it.
- Headless build worker: run one simple command per shell call. Do not chain commands with `&&`, `;` or `|`; a chained command can cancel the whole run.
- Commit once per task, staging files by path. Never `git add -A` or `git add .`.

## Review Focus

1. A path with spaces in the input's folder or file name: the stack runs and the result lands beside it with the accumulated name. Pinned by `test_path_with_spaces` (Task 1).
2. An explicit output with a different extension from the input (`photo.png` → `result.jpg`): the file really is a JPEG, and no default-named file appears. Pinned by `test_explicit_output_uses_its_format` (Task 1).
3. Output path equal to the input path: the stack reads the input before overwriting it and succeeds. Pinned by `test_output_may_overwrite_input` (Task 1).
4. A step that fails partway (bad option in step 2): the error names the step and passes the patch's own message through, nothing is written, and no temporary directory is left behind. Pinned by `test_failing_step_names_it_and_writes_nothing` and `test_leaves_no_temporary_files` (Task 1).
5. Mixing a shell patch (always writes `.png`) with Python patches (keep the input's extension): the name follows each patch's own rule, e.g. `input-psort-fold.png`. Pinned by `test_shell_and_python_patches_mix` (Task 1).

## File Structure

- `op` — the dispatcher. Gains helpers `patch_script`, `run_script`, `unknown_patch`, and `stack`; the single-patch tail is rewritten to use `patch_script` and `unknown_patch`; the help screen gains a second usage line.
- `tests/test_op_cli.py` — gains a `TestStack` class and the imports it needs.
- `README.md` — gains a `## Stacking patches` section and one Quick start line.

---

### Task 1: Stack patches with `+` in the dispatcher

**Files:**
- Modify: `op` (the help usage line near `echo "Usage: op <patch> <input> [--args]"`, and everything from the line `patch="$1"` to the end of the file)
- Test: `tests/test_op_cli.py`

**Interfaces:**
- Consumes: `list_patches` and `SCRIPT_DIR` already defined in `op`; fixtures `run_op`, `tmp_workdir`, `_make_gradient`, `assert_valid_image`, `skip_without_imagemagick` from `tests/conftest.py`.
- Produces: the stack behaviour Task 2 documents: default result name `<input base>-<suffix1>-<suffix2>...<ext>` beside the input, success line `Stacked <n> patches → <path>` on stderr.

- [ ] **Step 1: Record the baseline.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`. Expected: `388 passed` (record whatever it prints as the baseline).

- [ ] **Step 2: Write the failing tests.** In `tests/test_op_cli.py`, replace the import block at the top:

```python
import pytest

from conftest import assert_valid_image, skip_without_imagemagick
```

with:

```python
import os

import numpy as np
import pytest
from PIL import Image

from conftest import _make_gradient, assert_valid_image, skip_without_imagemagick
```

Then append this to the end of the file:

```python


def _pixels(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)


class TestStack:
    def test_help_shows_stack_usage(self, run_op):
        r = run_op([])
        assert r.returncode == 0
        assert "+ <patch>" in r.stdout

    def test_default_name_accumulates_suffixes(self, run_op, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_op(["pixel-sort", img, "+", "channel-swap", "+", "invert-lightness"])
        assert r.returncode == 0, r.stderr
        out = tmp_path / "input-psort-chswap-invl.png"
        assert_valid_image(str(out))
        assert sorted(p.name for p in tmp_path.iterdir()) == ["input-psort-chswap-invl.png", "input.png"]
        assert "Stacked 3 patches" in r.stderr

    def test_matches_manual_chain_with_options(self, run_op, tmp_workdir):
        tmp_path, img = tmp_workdir
        manual = tmp_path / "manual"
        manual.mkdir()
        a, b = str(manual / "a.png"), str(manual / "b.png")
        assert run_op(["pixel-sort", img, a, "--direction", "column"]).returncode == 0
        assert run_op(["channel-swap", a, b]).returncode == 0
        r = run_op(["pixel-sort", img, "--direction", "column", "+", "channel-swap"])
        assert r.returncode == 0, r.stderr
        assert np.array_equal(_pixels(tmp_path / "input-psort-chswap.png"), _pixels(b))

    def test_explicit_output_uses_its_format(self, run_op, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = tmp_path / "result.jpg"
        r = run_op(["pixel-sort", img, str(out), "+", "channel-swap"])
        assert r.returncode == 0, r.stderr
        assert Image.open(out).format == "JPEG"
        assert sorted(p.name for p in tmp_path.iterdir()) == ["input.png", "result.jpg"]

    def test_output_may_overwrite_input(self, run_op, tmp_workdir):
        tmp_path, img = tmp_workdir
        before = _pixels(img)
        r = run_op(["pixel-sort", img, img, "+", "channel-swap"])
        assert r.returncode == 0, r.stderr
        assert not np.array_equal(_pixels(img), before)

    def test_path_with_spaces(self, run_op, tmp_path):
        folder = tmp_path / "my photos"
        folder.mkdir()
        img = _make_gradient(str(folder / "my photo.png"))
        r = run_op(["pixel-sort", img, "+", "channel-swap"])
        assert r.returncode == 0, r.stderr
        assert_valid_image(str(folder / "my photo-psort-chswap.png"))

    @skip_without_imagemagick()
    def test_shell_and_python_patches_mix(self, run_op, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_op(["pixel-sort", img, "+", "fold", "--axis", "y"])
        assert r.returncode == 0, r.stderr
        assert_valid_image(str(tmp_path / "input-psort-fold.png"))

    def test_unknown_later_patch_writes_nothing(self, run_op, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_op(["pixel-sort", img, "+", "nonexistent"])
        assert r.returncode == 1
        assert "unknown patch 'nonexistent'" in r.stderr
        assert [p.name for p in tmp_path.iterdir()] == ["input.png"]

    def test_failing_step_names_it_and_writes_nothing(self, run_op, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_op(["pixel-sort", img, "+", "pixel-sort", "--direction", "sideways"])
        assert r.returncode != 0
        assert "step 2 (pixel-sort) failed" in r.stderr
        assert "invalid choice" in r.stderr
        assert [p.name for p in tmp_path.iterdir()] == ["input.png"]

    @pytest.mark.parametrize("args", [["+"], ["+", "+", "channel-swap"]])
    def test_empty_step_is_an_error(self, run_op, tmp_workdir, args):
        tmp_path, img = tmp_workdir
        r = run_op(["pixel-sort", img] + args)
        assert r.returncode == 1
        assert "empty step" in r.stderr
        assert [p.name for p in tmp_path.iterdir()] == ["input.png"]

    def test_missing_input(self, run_op):
        r = run_op(["pixel-sort", "/nonexistent/image.png", "+", "channel-swap"])
        assert r.returncode == 1
        assert "not found" in r.stderr.lower()

    def test_no_input_shows_usage(self, run_op):
        r = run_op(["pixel-sort", "+", "channel-swap"])
        assert r.returncode == 1
        assert "Usage:" in r.stderr

    def test_leaves_no_temporary_files(self, run_op, tmp_workdir):
        tmp_path, img = tmp_workdir
        scratch = tmp_path / "tmp"
        scratch.mkdir()
        env = {**os.environ, "TMPDIR": str(scratch)}
        assert run_op(["pixel-sort", img, "+", "channel-swap"], env=env).returncode == 0
        assert run_op(["pixel-sort", img, "+", "nonexistent"], env=env).returncode == 1
        assert run_op(["pixel-sort", img, "+", "pixel-sort", "--direction", "sideways"], env=env).returncode != 0
        assert list(scratch.iterdir()) == []
```

- [ ] **Step 3: Run the new tests and confirm they fail.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py -k TestStack`. Expected: `14 failed` (the old dispatcher passes `+` to the patch as a stray argument).

- [ ] **Step 4: Add the help usage line.** In `op`, directly after the line `  echo "Usage: op <patch> <input> [--args]"`, add:

```bash
  echo "       op <patch> <input> [output] [--args] + <patch> [--args] ..."
```

- [ ] **Step 5: Replace the dispatch tail.** In `op`, delete everything from the line `patch="$1"` to the end of the file (the single-patch dispatch: `patch="$1"`, `shift`, the `script_sh`/`script_py` lines and the `if`/`elif`/`else` that `exec`s or reports an unknown patch). Put this in its place, so it is the end of the file:

```bash
# Prints the script that runs a patch, or nothing if the patch does not exist.
patch_script() {
  local name="$1"
  if [[ -f "$SCRIPT_DIR/$name/$name.sh" ]]; then
    echo "$SCRIPT_DIR/$name/$name.sh"
  elif [[ -f "$SCRIPT_DIR/$name/$name.py" ]]; then
    echo "$SCRIPT_DIR/$name/$name.py"
  fi
}

run_script() {
  local script="$1"
  shift
  if [[ "$script" == *.sh ]]; then
    "$script" "$@"
  else
    python3 "$script" "$@"
  fi
}

unknown_patch() {
  echo "Error: unknown patch '$1'" >&2
  echo "" >&2
  list_patches >&2
  exit 1
}

# Stacking: op <patch> <input> [output] [options] + <patch> [options] + ...
# Each step runs in a temporary directory on the previous step's result, with
# the patch's own default name, so the suffixes accumulate as they would in a
# manual chain. The last step writes to [output] when one is given; otherwise
# the result lands beside the input.
stack() {
  local steps=() step="" arg
  for arg in "$@"; do
    if [[ "$arg" == "+" ]]; then
      steps+=("$step")
      step=""
    else
      step+="${step:+$'\x1f'}$arg"
    fi
  done
  steps+=("$step")

  local i n=${#steps[@]} parts name
  for (( i = 0; i < n; i++ )); do
    if [[ -z "${steps[i]}" ]]; then
      echo "Error: empty step $((i + 1)) in stack; put a patch name after each '+'" >&2
      exit 1
    fi
    IFS=$'\x1f' read -r -a parts <<< "${steps[i]}"
    name="${parts[0]}"
    [[ -n "$(patch_script "$name")" ]] || unknown_patch "$name"
  done

  IFS=$'\x1f' read -r -a parts <<< "${steps[0]}"
  if [[ ${#parts[@]} -lt 2 ]]; then
    echo "Usage: op <patch> <input> [output] [options] + <patch> [options] ..." >&2
    exit 1
  fi
  local input="${parts[1]}" output="" first_opts=("${parts[@]:2}")
  if [[ ${#first_opts[@]} -gt 0 && "${first_opts[0]}" != -* ]]; then
    output="${first_opts[0]}"
    first_opts=("${first_opts[@]:1}")
  fi
  if [[ ! -f "$input" ]]; then
    echo "Error: file not found: $input" >&2
    exit 1
  fi

  STACK_WORK="$(mktemp -d)"
  trap 'rm -rf "$STACK_WORK"' EXIT
  local work="$STACK_WORK"
  local current="$work/$(basename "$input")"
  cp "$input" "$current"

  local opts made file log="$work/.step.log" status script
  for (( i = 0; i < n; i++ )); do
    IFS=$'\x1f' read -r -a parts <<< "${steps[i]}"
    name="${parts[0]}"
    if (( i == 0 )); then
      opts=("${first_opts[@]}")
    else
      opts=("${parts[@]:1}")
    fi
    script="$(patch_script "$name")"
    if (( i == n - 1 )) && [[ -n "$output" ]]; then
      status=0
      run_script "$script" "$current" "$output" "${opts[@]}" 2> "$log" || status=$?
      if (( status != 0 )); then
        echo "Error: step $((i + 1)) ($name) failed" >&2
        cat "$log" >&2
        exit "$status"
      fi
      echo "Stacked $n patches → $output" >&2
      return 0
    fi
    status=0
    run_script "$script" "$current" "${opts[@]}" 2> "$log" || status=$?
    if (( status != 0 )); then
      echo "Error: step $((i + 1)) ($name) failed" >&2
      cat "$log" >&2
      exit "$status"
    fi
    # The work directory holds only the current image; the step's output is the one new file.
    made=""
    shopt -s dotglob nullglob
    for file in "$work"/*; do
      [[ "$file" == "$current" || "$file" == "$log" ]] && continue
      if [[ -n "$made" ]]; then
        echo "Error: step $((i + 1)) ($name) wrote more than one file" >&2
        exit 1
      fi
      made="$file"
    done
    if [[ -z "$made" ]]; then
      echo "Error: step $((i + 1)) ($name) wrote no output" >&2
      exit 1
    fi
    rm -f "$current"
    current="$made"
  done

  local dest
  dest="$(dirname "$input")/$(basename "$current")"
  cp "$current" "$dest"
  echo "Stacked $n patches → $dest" >&2
}

for arg in "$@"; do
  if [[ "$arg" == "+" ]]; then
    stack "$@"
    exit 0
  fi
done

patch="$1"
shift

script="$(patch_script "$patch")"
[[ -n "$script" ]] || unknown_patch "$patch"
if [[ "$script" == *.sh ]]; then
  exec "$script" "$@"
else
  exec python3 "$script" "$@"
fi
```

Notes for the implementer: `\x1f` (unit separator) joins a step's arguments so arguments with spaces survive the split. `STACK_WORK` is a global on purpose: the `EXIT` trap runs after `stack` returns, when a `local` would already be gone. The dotglob loop is what finds a step's output even for a hidden input such as `.photo.png`.

- [ ] **Step 6: Check the syntax.** Run `bash -n op`. Expected: no output, exit 0.

- [ ] **Step 7: Run the new tests.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py`. Expected: all pass (`25 passed` at a base of 388; the count is the existing dispatcher tests plus 14).

- [ ] **Step 8: Run the full suite.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`. Expected: the baseline plus 14, no failures (`402 passed` at a base of 388).

- [ ] **Step 9: Commit.** Stage `op` and `tests/test_op_cli.py` by path and commit with the subject `feat(op): stack patches with +` and the trailer the build note gives.

### Task 2: Document stacking in the README

**Files:**
- Modify: `README.md` (the Quick start example block, and a new section before `## Requirements`)

**Interfaces:**
- Consumes: the stack behaviour from Task 1 (syntax, default name, explicit output, failure behaviour).
- Produces: nothing later tasks use.

- [ ] **Step 1: Add a Quick start line.** In `README.md`, in the Quick start example block that begins with the line `op bit-crush photo.jpg                      # default 2-bit crush`, change that line's comment to `# default 3-bit crush` (bit-crush's default is `--bits 3`), and add this line at the end of the same block, before its closing fence:

```bash
op pixel-sort photo.jpg + fold + polar         # stack patches with +
```

- [ ] **Step 2: Add the section.** Directly before the line `## Requirements`, insert:

````markdown
## Stacking patches

Join patches with `+` to run them one after another, each on the previous result:

```bash
op <patch> <input> [output] [--args] + <patch> [--args] + ...
```

```bash
op pixel-sort photo.jpg + fold + polar            # writes photo-psort-fold-polar.png
op pixel-sort photo.jpg --by hue + channel-swap   # options follow the patch they belong to
op seam-carve photo.jpg out.jpg + thermal         # an output after the input names the final file
```

The input, and the output if you give one, come right after the first patch; every later step takes only options. Without an output, the result is saved next to the input with each patch's suffix in order, the same name a chain of single `op` calls would produce. Intermediate images live in a temporary directory that is removed afterwards. If a step fails, `op` names it, shows its error, and writes nothing.

````

- [ ] **Step 3: Check the documented default name.** Copy the README photo to a scratch folder and run the first example there:
  - `mkdir -p /tmp/op-stack-check`
  - `cp _output/mclaren.jpg /tmp/op-stack-check/photo.jpg`
  - `PATH="/tmp/opimg-venv/bin:$PATH" ./op pixel-sort /tmp/op-stack-check/photo.jpg + fold + polar`
  - `ls /tmp/op-stack-check`

  Expected: stderr ends with `Stacked 3 patches → /tmp/op-stack-check/photo-psort-fold-polar.png`, and `ls` shows `photo-psort-fold-polar.png` and `photo.jpg`. Then remove the folder with `rm -r /tmp/op-stack-check`.

- [ ] **Step 4: Check the other two examples run.** In the same way (a fresh `/tmp/op-stack-check` with `photo.jpg`), run `PATH="/tmp/opimg-venv/bin:$PATH" ./op pixel-sort /tmp/op-stack-check/photo.jpg --by hue + channel-swap` (expected result `photo-psort-chswap.jpg`) and `PATH="/tmp/opimg-venv/bin:$PATH" ./op seam-carve /tmp/op-stack-check/photo.jpg /tmp/op-stack-check/out.jpg + thermal` (expected result `out.jpg` only). Remove the folder afterwards.

- [ ] **Step 5: Run the full suite.** Run `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`. Expected: the same count as Task 1 Step 8, no failures.

- [ ] **Step 6: Commit.** Stage `README.md` by path and commit with the subject `docs(readme): stacking patches with +` and the trailer the build note gives.

---

## Self-review

- Spec coverage: stacking in one command (Task 1), README update (Task 2). The spec's sketch put the input last; this plan puts it first to keep op's existing argument order, and says so in the Spec line.
- Placeholders: none; every code step carries its code.
- Names: `patch_script`, `run_script`, `unknown_patch`, `stack`, `STACK_WORK`, `_pixels`, `TestStack` are defined where used; suffixes `psort`, `chswap`, `invl`, `fold`, `polar`, `thermal` are the patches' own.
- Pre-checked: the Task 1 code and tests were run by the planning session on a scratch copy of `new-patches` at `a8e2aa4`: the 14 new tests failed against the old `op` (`14 failed`) and passed with the new one; the full suite showed `402 passed`. Manual runs covered a folder with a space, a hidden input, an explicit `.jpg` output, an unknown later patch (exit 1), a bad option in step 2 (exit 2), and no temporary directories left behind.
