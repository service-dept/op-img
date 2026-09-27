"""Tests for zoom-blur tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestZoomBlur:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("zoom-blur", "zoom-blur.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-zoomblur.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("zoom-blur", "zoom-blur.py", [img, out, "--amount", "0.6", "--center", "0.25,0.75", "--samples", "8"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "amount=0.6" in r.stderr
        assert "center=0.25,0.75" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("zoom-blur", "zoom-blur.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_edges_blur_more_than_center(self, run_tool, tmp_workdir):
        """Streaks grow with distance from the center."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "zoom.png")
        r = run_tool("zoom-blur", "zoom-blur.py", [img, out, "--amount", "1"])
        assert r.returncode == 0
        diff = np.abs(_pixels(out) - _pixels(img)).mean(axis=2)
        assert diff[28:36, 28:36].mean() < diff[:8, :8].mean()

    def test_bad_center(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("zoom-blur", "zoom-blur.py", [img, "--center", "2,0.5"])
        assert r.returncode != 0

    def test_missing_input(self, run_tool):
        r = run_tool("zoom-blur", "zoom-blur.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("zoom-blur", "zoom-blur.py", [])
        assert r.returncode != 0
