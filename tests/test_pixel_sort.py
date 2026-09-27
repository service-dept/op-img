"""Tests for pixel-sort tool."""

from conftest import assert_valid_image


class TestPixelSort:
    def test_explicit_options(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "sorted.png")
        r = run_tool("pixel-sort", "pixel-sort.py", [
            img, out, "--by", "hue", "--threshold", "150", "--direction", "column",
        ])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "by=hue" in r.stderr

    def test_saturation_metric(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "sat.png")
        r = run_tool("pixel-sort", "pixel-sort.py", [img, out, "--by", "saturation"])
        assert r.returncode == 0
        assert_valid_image(out)
