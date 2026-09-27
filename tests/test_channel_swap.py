"""Tests for channel-swap tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


class TestChannelSwap:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("channel-swap", "channel-swap.py", [img, out, "--map", "G,R,B"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "map=G,R,B" in r.stderr

    def test_pixel_values_swapped(self, run_tool, tmp_workdir):
        """Verify that B,G,R map actually swaps R and B channels."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "swapped.png")
        r = run_tool("channel-swap", "channel-swap.py", [img, out, "--map", "B,G,R"])
        assert r.returncode == 0
        original = np.array(Image.open(img))
        swapped = np.array(Image.open(out))
        # With B,G,R: output R = input B, output G = input G, output B = input R
        np.testing.assert_array_equal(swapped[:, :, 0], original[:, :, 2])
        np.testing.assert_array_equal(swapped[:, :, 1], original[:, :, 1])
        np.testing.assert_array_equal(swapped[:, :, 2], original[:, :, 0])
