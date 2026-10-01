"""Tests for stipple tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


class TestStipple:
    def test_explicit_options(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "stip.png")
        r = run_tool("stipple", "stipple.py", [
            img, out, "--dots", "1000", "--dot-size", "2", "--seed", "42",
        ])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "dots=1000" in r.stderr

    def test_seed_reproducibility(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out1 = str(tmp_path / "a.png")
        out2 = str(tmp_path / "b.png")
        run_tool("stipple", "stipple.py", [img, out1, "--seed", "7"])
        run_tool("stipple", "stipple.py", [img, out2, "--seed", "7"])
        with open(out1, "rb") as f1, open(out2, "rb") as f2:
            assert f1.read() == f2.read()

    def test_jpeg_output_gets_a_white_background(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.jpg")
        r = run_tool("stipple", "stipple.py", [img, out, "--dots", "1000"])
        assert r.returncode == 0, r.stderr
        result = Image.open(out)
        assert result.format == "JPEG" and result.mode == "RGB"
        assert (np.asarray(result) >= 250).all(axis=2).any(), "no white background showing"
