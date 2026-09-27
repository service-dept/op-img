"""Tests for dither tool."""

import numpy as np
import pytest
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestDither:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("dither", "dither.py", [img, out, "--method", "atkinson", "--levels", "3"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "method=atkinson" in r.stderr

    def test_full_levels_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("dither", "dither.py", [img, out, "--levels", "256"])
        assert r.returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    @pytest.mark.parametrize("method", ["bayer", "floyd", "atkinson"])
    def test_only_allowed_levels(self, run_tool, tmp_workdir, method):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / f"{method}.png")
        r = run_tool("dither", "dither.py", [img, out, "--method", method, "--levels", "2"])
        assert r.returncode == 0
        assert set(np.unique(_pixels(out))) <= {0, 255}

    def test_dither_keeps_average_tone(self, run_tool, tmp_workdir):
        """Dithering to two levels keeps each channel's mean close to the source."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "floyd.png")
        r = run_tool("dither", "dither.py", [img, out, "--method", "floyd"])
        assert r.returncode == 0
        assert np.abs(_pixels(out).mean(axis=(0, 1)) - _pixels(img).mean(axis=(0, 1))).max() < 12

    def test_levels_out_of_range(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("dither", "dither.py", [img, "--levels", "1"])
        assert r.returncode != 0
