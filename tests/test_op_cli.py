"""Tests for the `op` CLI dispatcher."""

import os

import numpy as np
import pytest
from PIL import Image

from conftest import _make_gradient, assert_valid_image, skip_without_imagemagick

ALL_PATCHES = [
    "bit-crush", "channel-offset", "channel-swap",
    "closest-palette", "cross-hatch", "dot-halftone", "echo",
    "fold", "invert-lightness", "isolate-threshold",
    "kaleidoscope", "line-halftone", "pixel-sort", "polar",
    "posterize-hsv", "raw-bend", "res-crush", "scan-glitch", "seam-carve",
    "slit-scan", "stipple", "thermal", "tile-shuffle",
    "wrong-stride",
    "fft-phase",
    "zoom-blur",
    "swirl",
    "displace",
    "drip",
    "edge-glow",
    "contour",
    "hue-isolate",
    "bloom",
    "voronoi-mosaic",
    "oil-paint",
    "tilt-shift",
    "flow-streak",
    "dither",
    "jpeg-rot",
    "ascii",
    "recolor",
]


class TestHelp:
    def test_no_args_shows_help(self, run_op):
        r = run_op([])
        assert r.returncode == 0
        assert "Usage:" in r.stdout
        assert "Patches (3 of" in r.stdout

    def test_help_flag(self, run_op):
        r = run_op(["--help"])
        assert r.returncode == 0
        assert "Usage:" in r.stdout

    def test_h_flag(self, run_op):
        r = run_op(["-h"])
        assert r.returncode == 0
        assert "Usage:" in r.stdout

    def test_no_args_shows_three_patches(self, run_op):
        r = run_op([])
        patch_lines = [l for l in r.stdout.splitlines() if l.startswith("  ") and l.strip() in ALL_PATCHES]
        assert len(patch_lines) == 3

    def test_info_flag(self, run_op):
        r = run_op(["--info", "scan-glitch"])
        assert r.returncode == 0
        assert "--severity" in r.stdout

    def test_info_shell_patch(self, run_op):
        r = run_op(["--info", "fold"])
        assert r.returncode == 0
        assert "--axis" in r.stdout

    def test_info_unknown_patch(self, run_op):
        r = run_op(["--info", "nonexistent"])
        assert r.returncode != 0

    def test_list_flag_shows_all(self, run_op):
        r = run_op(["--list"])
        assert r.returncode == 0
        assert "Available patches:" in r.stdout
        for patch in ALL_PATCHES:
            assert patch in r.stdout, f"Patch '{patch}' not in --list output"


class TestDispatch:
    def test_dispatch_python_patch(self, run_op, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        r = run_op(["scan-glitch", img, out, "--severity", "1", "--seed", "1"])
        assert r.returncode == 0
        assert_valid_image(out)

    @skip_without_imagemagick()
    def test_dispatch_shell_patch(self, run_op, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        r = run_op(["bit-crush", img, out, "--bits", "2"])
        assert r.returncode == 0
        assert_valid_image(out)

    def test_unknown_patch(self, run_op):
        r = run_op(["nonexistent-patch"])
        assert r.returncode != 0
        assert "unknown patch" in r.stderr.lower()
        assert "Available patches:" in r.stderr


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



class TestLayout:
    def test_patches_live_under_patches(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for name in ALL_PATCHES:
            assert os.path.isdir(os.path.join(root, "patches", name)), f"{name} is not under patches/"
            assert not os.path.exists(os.path.join(root, name)), f"{name} is still at the root"
