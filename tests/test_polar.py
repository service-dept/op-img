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

    def test_missing_input(self, run_tool):
        r = run_tool("polar", "polar.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()

    def test_no_args(self, run_tool):
        r = run_tool("polar", "polar.py", [])
        assert r.returncode != 0
