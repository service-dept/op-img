"""Tests for cross-hatch tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


class TestCrossHatch:
    def test_explicit_options(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "hatch.png")
        r = run_tool("cross-hatch", "cross-hatch.py", [
            img, out, "--layers", "2", "--spacing", "8", "--thresholds", "180,80",
        ])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "layers=2" in r.stderr

    def test_threshold_count_mismatch(self, run_tool, tmp_workdir):
        _, img = tmp_workdir
        r = run_tool("cross-hatch", "cross-hatch.py", [
            img, "--layers", "3", "--thresholds", "200,100",
        ])
        assert r.returncode != 0

    def test_jpeg_output_gets_a_white_background(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.jpg")
        r = run_tool("cross-hatch", "cross-hatch.py", [img, out])
        assert r.returncode == 0, r.stderr
        result = Image.open(out)
        assert result.format == "JPEG" and result.mode == "RGB"
        assert (np.asarray(result) >= 250).all(axis=2).any(), "no white background showing"
