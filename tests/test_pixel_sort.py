"""Tests for pixel-sort tool."""

from conftest import assert_valid_image


class TestPixelSort:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("pixel-sort", "pixel-sort.py", [img])
        assert r.returncode == 0
        out = str(tmp_path / "input-psort.png")
        assert_valid_image(out)

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

    def test_missing_input(self, run_tool):
        r = run_tool("pixel-sort", "pixel-sort.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()

    def test_no_args(self, run_tool):
        r = run_tool("pixel-sort", "pixel-sort.py", [])
        assert r.returncode != 0
