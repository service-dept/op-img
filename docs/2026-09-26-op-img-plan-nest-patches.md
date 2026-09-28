---
title: nest-patches
kind: plan
target: op-img
topic: nest-patches
status: approved
written: 2026-09-26T20:01:25Z
by: claude
---

# nest-patches Implementation Plan

**Goal:** Move every patch directory under `patches/` and update `op`, the test harness and the README to match.

**Architecture:** One move plus three small path changes. `op` gains `PATCH_DIR="$SCRIPT_DIR/patches"` and uses it wherever it looked up `$SCRIPT_DIR/<patch>`. `tests/conftest.py`'s `run_tool` builds `ROOT/patches/<dir>/<script>`. README usage lines gain the `patches/` prefix.

**Tech Stack:** bash, pytest.

**Spec:** `/home/jmo/linda/docs/2026-09-26-op-img-spec-nest-patches.md`

**Executor:** the interactive session (Josh asked for spec, plan and implementation in one go).

## Global Constraints

- Keep history: move with `git mv`, one directory at a time.
- The move must include every patch on the branch at the time, including `recolor` once its build is merged in.
- No behaviour change for users: `op <patch> ...` and `op ... + ...` are unchanged.
- Tests run with `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests`.
- Branch `nest-patches`, from `stack-patches` with `recolor` merged in; the PR is based on `main` and merges after the stacking and recolor PRs.

## Review Focus

1. `op` run through a symlink from another directory still finds patches. Pinned by the existing dispatcher tests, which run `op` by absolute path, and a manual symlink check.
2. A stray patch left at the root: pinned by `test_patches_live_under_patches`, which also fails if any patch directory is missing from `patches/`.
3. README usage lines that still point at the root: pinned by a grep in Task 1 Step 6 that must find none.

## Task 1: Move the patches and update the plumbing

- [ ] **Step 1: Write the failing test.** Append to `tests/test_op_cli.py`:

```python


class TestLayout:
    def test_patches_live_under_patches(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for name in ALL_PATCHES:
            assert os.path.isdir(os.path.join(root, "patches", name)), f"{name} is not under patches/"
            assert not os.path.exists(os.path.join(root, name)), f"{name} is still at the root"
```

- [ ] **Step 2: Run it and confirm it fails.** `PATH="/tmp/opimg-venv/bin:$PATH" python3 -m pytest -q tests/test_op_cli.py -k Layout`. Expected: 1 failed.

- [ ] **Step 3: Move every patch.** For each name in `ALL_PATCHES`: `git mv <name> patches/<name>` (after `mkdir patches`).

- [ ] **Step 4: Update `op`.** After the line `SCRIPT_DIR="$(cd "$(dirname "$SOURCE")" && pwd)"`, add `PATCH_DIR="$SCRIPT_DIR/patches"`. Replace every patch lookup that uses `$SCRIPT_DIR` (`"$SCRIPT_DIR"/*/` in `list_patches` and `list_random_patches`, `$SCRIPT_DIR/$patch/...` in `--info`, `$SCRIPT_DIR/$name/...` in `patch_script`) with `$PATCH_DIR`. `SCRIPT_DIR` stays for resolving the symlink.

- [ ] **Step 5: Update the test harness.** In `tests/conftest.py`, change `script_path = os.path.join(ROOT, tool_dir, script_name)` to `script_path = os.path.join(ROOT, "patches", tool_dir, script_name)`.

- [ ] **Step 6: Update the README.** Prefix every per-patch usage line: `./<patch>/` becomes `./patches/<patch>/` (both `python3 ./<patch>/...` and `./<patch>/...` forms). Then `grep -nE '^(python3 )?\./[a-z-]+/' README.md` must print nothing. Add, directly before `## Requirements`, an "Adding a patch" section: a new patch is a directory under `patches/` named after it, holding `<name>.py` (with `requirements.txt`) or `<name>.sh`; `op` finds it by name; add its tests in `tests/test_<name>.py` and its name to `ALL_PATCHES` in `tests/test_op_cli.py`.

- [ ] **Step 7: Run the full suite.** Expected: the base count plus 1, no failures. Also symlink `op` into a scratch directory and run `op --list` and one stack through the link from another directory.

- [ ] **Step 8: Commit** by path (the moved directories, `op`, `tests/conftest.py`, `tests/test_op_cli.py`, `README.md`) with the subject `refactor: move patches into patches/`.
