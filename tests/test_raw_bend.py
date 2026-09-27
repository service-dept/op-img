"""Tests for raw-bend tool."""

import os

from conftest import assert_valid_image


class TestRawBend:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("raw-bend", "raw-bend.py", [
            img, out,
            "--echo-strength", "0.8",
            "--echo-delay", "200",
            "--chorus", "0.5",
            "--bitcrush", "4",
        ])
        assert r.returncode == 0
        assert_valid_image(out)

    def test_output_dimensions_match_input(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "dims.png")
        r = run_tool("raw-bend", "raw-bend.py", [img, out])
        assert r.returncode == 0
        result = assert_valid_image(out)
        assert result.size == (64, 64)
