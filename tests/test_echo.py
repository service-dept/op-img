"""Tests for echo tool."""

import os

from conftest import assert_valid_image


class TestEcho:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("echo", "echo.py", [img, out, "--count", "3"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "count=3" in r.stderr

    def test_different_offsets(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "offset.png")
        r = run_tool("echo", "echo.py", [img, out, "--offset-x", "5", "--offset-y", "5"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "offset=(5,5)" in r.stderr
