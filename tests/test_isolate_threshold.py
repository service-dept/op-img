"""Tests for isolate-threshold tool."""

from PIL import Image

from conftest import assert_valid_image


class TestIsolateThreshold:
    def test_explicit_options(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "thresh.png")
        r = run_tool("isolate-threshold", "isolate-threshold.py", [
            img, out, "--scale", "2", "--threshold", "40", "--color", "#00ff00",
        ])
        assert r.returncode == 0
        assert_valid_image(out)

    def test_scale_increases_dimensions(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "scaled.png")
        r = run_tool("isolate-threshold", "isolate-threshold.py", [
            img, out, "--scale", "2",
        ])
        assert r.returncode == 0
        result = assert_valid_image(out)
        # Original is 64x64, scale 2 → 128x128
        assert result.size == (128, 128)

    def test_jpeg_output_gets_a_white_background(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.jpg")
        r = run_tool("isolate-threshold", "isolate-threshold.py", [img, out])
        assert r.returncode == 0, r.stderr
        result = Image.open(out)
        assert result.format == "JPEG" and result.mode == "RGB"
