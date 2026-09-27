"""Tests for seam-carve tool."""

import os

from conftest import assert_valid_image


class TestSeamCarve:
    def test_output_width_reduced(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "reduced.png")
        r = run_tool("seam-carve", "seam-carve.py", [img, out, "--percent", "20"])
        assert r.returncode == 0
        result = assert_valid_image(out)
        # Input is 64x64, removing 20% = ~12-13 seams, output width should be ~51-52
        out_w, out_h = result.size
        assert out_w < 64, f"Expected reduced width, got {out_w}"
        expected_approx = int(64 * 80 / 100)
        assert abs(out_w - expected_approx) <= 1, f"Expected width ~{expected_approx}, got {out_w}"
        assert out_h == 64, f"Expected height 64, got {out_h}"

    def test_height_preserved(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "height.png")
        r = run_tool("seam-carve", "seam-carve.py", [img, out, "--percent", "10"])
        assert r.returncode == 0
        result = assert_valid_image(out)
        assert result.size[1] == 64
