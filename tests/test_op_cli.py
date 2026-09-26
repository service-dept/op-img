"""Tests for the `op` CLI dispatcher."""

import pytest

from conftest import assert_valid_image, skip_without_imagemagick

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
    "crt",
    "dither",
    "jpeg-rot",
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
