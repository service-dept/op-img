"""Tests for thermal tool."""

import os

import numpy as np
from PIL import Image

from conftest import assert_valid_image


class TestThermal:
    def test_output_is_colorful(self, run_tool, tmp_workdir):
        """Verify output is RGB and contains colorful pixels (not just grayscale)."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "colorful.png")
        r = run_tool("thermal", "thermal.py", [img, out])
        assert r.returncode == 0
        result = assert_valid_image(out)
        arr = np.array(result)
        # Check that channels differ (not grayscale)
        # In a thermal image, R, G, B should not all be equal for most pixels
        diffs = np.abs(arr[:, :, 0].astype(int) - arr[:, :, 1].astype(int))
        assert diffs.max() > 10, "Thermal output looks grayscale -- channels are too similar"
