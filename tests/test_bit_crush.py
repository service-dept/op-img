"""Tests for bit-crush tool (ImageMagick)."""

import pytest

from conftest import assert_valid_image, skip_without_imagemagick

pytestmark = pytest.mark.imagemagick


@skip_without_imagemagick()
class TestBitCrush:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("bit-crush", "bit-crush.sh", [img])
        assert r.returncode == 0
        out = str(tmp_path / "input-crush-1bit.png")
        assert_valid_image(out)

    def test_explicit_options(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "crushed.png")
        r = run_tool("bit-crush", "bit-crush.sh", [img, out, "--bits", "4"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "4-bit" in r.stderr

    def test_missing_input(self, run_tool):
        r = run_tool("bit-crush", "bit-crush.sh", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()

    def test_no_args(self, run_tool):
        r = run_tool("bit-crush", "bit-crush.sh", [])
        assert r.returncode != 0
        assert "Usage:" in r.stderr
