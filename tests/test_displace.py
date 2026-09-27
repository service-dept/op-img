"""Tests for displace tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _horizontal_stripes(path: str) -> str:
    """Rows alternate between dark and light; every row is constant along x."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    for y in range(64):
        arr[y, :] = (230, 200, 40) if (y // 8) % 2 == 0 else (20, 40, 90)
    Image.fromarray(arr).save(path)
    return path


class TestDisplace:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("displace", "displace.py", [img, out, "--amount", "20", "--angle", "45", "--blur", "1"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "amount=20.0" in r.stderr
        assert "angle=45.0" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("displace", "displace.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_displacement_follows_angle(self, run_tool, tmp_path):
        """Horizontal displacement cannot change rows that are constant along x; vertical can."""
        img = _horizontal_stripes(str(tmp_path / "stripes.png"))
        across = str(tmp_path / "across.png")
        down = str(tmp_path / "down.png")
        assert run_tool("displace", "displace.py", [img, across, "--amount", "40", "--angle", "0"]).returncode == 0
        assert run_tool("displace", "displace.py", [img, down, "--amount", "40", "--angle", "90"]).returncode == 0
        assert np.abs(_pixels(across) - _pixels(img)).max() <= 1
        assert np.abs(_pixels(down) - _pixels(img)).mean() > 5

    def test_amount_out_of_range(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("displace", "displace.py", [img, "--amount", "500"])
        assert r.returncode != 0
