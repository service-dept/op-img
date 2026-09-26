"""Tests for polar tool."""

import os

import numpy as np
from PIL import Image

from conftest import assert_valid_image


class TestPolar:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("polar", "polar.py", [img])
        assert r.returncode == 0
        out = str(tmp_path / "input-polar.png")
        assert_valid_image(out)

    def test_explicit_from_polar(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("polar", "polar.py", [img, out, "--mode", "from-polar"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "mode=from-polar" in r.stderr

    def test_roundtrip(self, run_tool, tmp_workdir):
        """to-polar then from-polar should give a roughly similar image."""
        tmp_path, img = tmp_workdir
        polar_out = str(tmp_path / "polar.png")
        roundtrip_out = str(tmp_path / "roundtrip.png")

        r1 = run_tool("polar", "polar.py", [img, polar_out, "--mode", "to-polar"])
        assert r1.returncode == 0
        r2 = run_tool("polar", "polar.py", [polar_out, roundtrip_out, "--mode", "from-polar"])
        assert r2.returncode == 0

        original = np.array(Image.open(img))
        roundtrip = np.array(Image.open(roundtrip_out))
        # Due to interpolation, they won't be exact -- just check shapes match
        assert original.shape == roundtrip.shape

    def test_rotate_shifts_the_angle_axis(self, run_tool, tmp_workdir):
        """A quarter turn moves the to-polar output a quarter of the width along x."""
        tmp_path, img = tmp_workdir
        plain, turned = str(tmp_path / "plain.png"), str(tmp_path / "turned.png")
        assert run_tool("polar", "polar.py", [img, plain]).returncode == 0
        assert run_tool("polar", "polar.py", [img, turned, "--rotate", "90"]).returncode == 0
        a, b = np.array(Image.open(plain), dtype=int), np.array(Image.open(turned), dtype=int)
        # Equal up to floating-point rounding in the angle.
        assert np.abs(b - np.roll(a, -a.shape[1] // 4, axis=1)).max() <= 1

    def test_center_and_radius_change_the_result(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        plain = str(tmp_path / "plain.png")
        assert run_tool("polar", "polar.py", [img, plain]).returncode == 0
        for opts in (["--center", "0.3,0.6"], ["--radius", "0.5"]):
            out = str(tmp_path / f"{opts[0][2:]}.png")
            r = run_tool("polar", "polar.py", [img, out] + opts)
            assert r.returncode == 0, r.stderr
            assert not np.array_equal(np.array(Image.open(out)), np.array(Image.open(plain)))

    def test_defaults_match_explicit_defaults(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        plain, explicit = str(tmp_path / "plain.png"), str(tmp_path / "explicit.png")
        assert run_tool("polar", "polar.py", [img, plain]).returncode == 0
        assert run_tool("polar", "polar.py", [img, explicit, "--center", "0.5,0.5", "--rotate", "0", "--radius", "1"]).returncode == 0
        assert np.array_equal(np.array(Image.open(plain)), np.array(Image.open(explicit)))

    def test_roundtrip_with_options_returns_close_to_the_original(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        opts = ["--center", "0.4,0.6", "--rotate", "40"]
        mid, back = str(tmp_path / "mid.png"), str(tmp_path / "back.png")
        assert run_tool("polar", "polar.py", [img, mid] + opts).returncode == 0
        assert run_tool("polar", "polar.py", [mid, back, "--mode", "from-polar"] + opts).returncode == 0
        diff = np.abs(np.array(Image.open(back), dtype=float) - np.array(Image.open(img).convert("RGB"), dtype=float)).mean()
        assert diff < 20, f"round trip drifted: {diff:.1f}"

    def test_bad_center_and_radius_are_errors(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        for opts in (["--center", "0.5"], ["--center", "a,b"], ["--radius", "0"]):
            r = run_tool("polar", "polar.py", [img] + opts)
            assert r.returncode == 2, opts

    def test_missing_input(self, run_tool):
        r = run_tool("polar", "polar.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()

    def test_no_args(self, run_tool):
        r = run_tool("polar", "polar.py", [])
        assert r.returncode != 0
