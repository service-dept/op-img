"""Tests for res-crush tool (ImageMagick)."""

import pytest

from conftest import assert_valid_image, skip_without_imagemagick

pytestmark = pytest.mark.imagemagick


@skip_without_imagemagick()
class TestResCrush:
    def test_explicit_options(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "pix.png")
        r = run_tool("res-crush", "res-crush.sh", [img, out, "--size", "16"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "16px" in r.stderr
