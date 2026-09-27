"""Tests for slit-scan tool."""

import os

from conftest import assert_valid_image


class TestSlitScan:
    def test_output_dimensions_match_input(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "dims.png")
        r = run_tool("slit-scan", "slit-scan.py", [img, out, "--slits", "16"])
        assert r.returncode == 0
        result = assert_valid_image(out)
        assert result.size == (64, 64)
