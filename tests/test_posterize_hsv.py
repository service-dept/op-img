"""Tests for posterize-hsv tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


class TestPosterizeHsv:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("posterize-hsv", "posterize-hsv.py", [
            img, out, "--h-levels", "4", "--s-levels", "2", "--v-levels", "3",
        ])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "h=4" in r.stderr
        assert "s=2" in r.stderr
        assert "v=3" in r.stderr

    def test_fewer_unique_colors(self, run_tool, tmp_workdir):
        """Posterized image should have fewer unique colors than the original."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "posterized.png")
        r = run_tool("posterize-hsv", "posterize-hsv.py", [
            img, out, "--h-levels", "3", "--s-levels", "2", "--v-levels", "2",
        ])
        assert r.returncode == 0
        original = np.array(Image.open(img))
        posterized = np.array(Image.open(out))
        orig_colors = len(np.unique(original.reshape(-1, 3), axis=0))
        post_colors = len(np.unique(posterized.reshape(-1, 3), axis=0))
        assert post_colors < orig_colors
