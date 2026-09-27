"""Tests for bit-crush tool (ImageMagick)."""

import pytest

from conftest import assert_valid_image, skip_without_imagemagick

pytestmark = pytest.mark.imagemagick


@skip_without_imagemagick()
class TestBitCrush:
    def test_explicit_options(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "crushed.png")
        r = run_tool("bit-crush", "bit-crush.sh", [img, out, "--bits", "4"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "4-bit" in r.stderr
