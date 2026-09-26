"""Tests for res-crush tool (ImageMagick)."""

import pytest

from conftest import assert_valid_image, skip_without_imagemagick

pytestmark = pytest.mark.imagemagick


@skip_without_imagemagick()
class TestResCrush:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("res-crush", "res-crush.sh", [img])
        assert r.returncode == 0
        out = str(tmp_path / "input-pixelate-64.png")
        assert_valid_image(out)

    def test_explicit_options(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "pix.png")
        r = run_tool("res-crush", "res-crush.sh", [img, out, "--size", "16"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "16px" in r.stderr

    def test_missing_input(self, run_tool):
        r = run_tool("res-crush", "res-crush.sh", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()

    def test_no_args(self, run_tool):
        r = run_tool("res-crush", "res-crush.sh", [])
        assert r.returncode != 0
        assert "Usage:" in r.stderr
