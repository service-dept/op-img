"""Tests for kaleidoscope tool."""

import os

from conftest import assert_valid_image


class TestKaleidoscope:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("kaleidoscope", "kaleidoscope.py", [img])
        assert r.returncode == 0
        out = str(tmp_path / "input-kaleido.png")
        assert_valid_image(out)

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("kaleidoscope", "kaleidoscope.py", [img, out, "--segments", "8"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "segments=8" in r.stderr

    def test_different_angles(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "angled.png")
        r = run_tool("kaleidoscope", "kaleidoscope.py", [img, out, "--angle", "45"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "angle=45.0" in r.stderr

    def test_missing_input(self, run_tool):
        r = run_tool("kaleidoscope", "kaleidoscope.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()

    def test_no_args(self, run_tool):
        r = run_tool("kaleidoscope", "kaleidoscope.py", [])
        assert r.returncode != 0
