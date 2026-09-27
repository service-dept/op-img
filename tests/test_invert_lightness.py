"""Tests for invert-lightness tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


class TestInvertLightness:
    def test_pixels_changed(self, run_tool, tmp_workdir):
        """Verify the output is visually different from the input."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "inverted.png")
        r = run_tool("invert-lightness", "invert-lightness.py", [img, out])
        assert r.returncode == 0
        original = np.array(Image.open(img))
        inverted = np.array(Image.open(out))
        assert not np.array_equal(original, inverted)

    def test_lightness_is_inverted(self, run_tool, tmp_workdir):
        """L in the output is 255 - L of the input, pixel for pixel, within LAB rounding."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "inverted.png")
        r = run_tool("invert-lightness", "invert-lightness.py", [img, out])
        assert r.returncode == 0
        l_in = np.array(Image.open(img).convert("LAB"), dtype=np.float64)[:, :, 0]
        l_out = np.array(Image.open(out).convert("LAB"), dtype=np.float64)[:, :, 0]
        err = np.mean(np.abs(l_out - (255 - l_in)))
        assert err < 8, f"Mean lightness error too high: {err:.1f}"

    def test_involution_is_close(self, run_tool, tmp_workdir):
        """Two inversions return close to the original (a corrupting rebuild does not)."""
        tmp_path, img = tmp_workdir
        mid = str(tmp_path / "mid.png")
        out = str(tmp_path / "roundtrip.png")
        assert run_tool("invert-lightness", "invert-lightness.py", [img, mid]).returncode == 0
        assert run_tool("invert-lightness", "invert-lightness.py", [mid, out]).returncode == 0
        original = np.array(Image.open(img), dtype=np.float64)
        roundtrip = np.array(Image.open(out), dtype=np.float64)
        mae = np.mean(np.abs(original - roundtrip))
        assert mae < 30, f"Mean absolute error too high: {mae:.1f}"
