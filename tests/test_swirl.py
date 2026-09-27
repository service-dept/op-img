"""Tests for swirl tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestSwirl:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("swirl", "swirl.py", [img, out, "--angle", "-180", "--radius", "0.5", "--center", "0.4,0.6"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "angle=-180.0" in r.stderr
        assert "radius=0.5" in r.stderr

    def test_zero_angle_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("swirl", "swirl.py", [img, out, "--angle", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_outside_radius_is_untouched(self, run_tool, tmp_workdir):
        """Pixels beyond the radius do not move; pixels inside do."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "swirl.png")
        r = run_tool("swirl", "swirl.py", [img, out, "--angle", "360", "--radius", "0.5"])
        assert r.returncode == 0
        diff = np.abs(_pixels(out) - _pixels(img)).max(axis=2)
        assert diff[:4, :4].max() <= 1
        assert diff[:4, -4:].max() <= 1
        assert diff[20:44, 20:44].mean() > 5

    def test_angle_out_of_range(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("swirl", "swirl.py", [img, "--angle", "5000"])
        assert r.returncode != 0
