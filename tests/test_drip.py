"""Tests for drip tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _white_spot(path: str) -> str:
    """Black 64x64 with a 2x2 white spot at rows 10-11, columns 30-31."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[10:12, 30:32] = 255
    Image.fromarray(arr).save(path)
    return path


class TestDrip:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("drip", "drip.py", [img, out, "--length", "30", "--threshold", "100", "--direction", "left"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "direction=left" in r.stderr

    def test_zero_length_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("drip", "drip.py", [img, out, "--length", "0"])
        assert r.returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_only_brightens(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "drip.png")
        r = run_tool("drip", "drip.py", [img, out, "--threshold", "100"])
        assert r.returncode == 0
        assert (_pixels(out) >= _pixels(img)).all()

    def test_drips_in_direction(self, run_tool, tmp_path):
        """A white spot trails below itself when dripping down, and nothing appears above."""
        img = _white_spot(str(tmp_path / "spot.png"))
        down = str(tmp_path / "down.png")
        up = str(tmp_path / "up.png")
        assert run_tool("drip", "drip.py", [img, down, "--length", "20", "--direction", "down"]).returncode == 0
        assert run_tool("drip", "drip.py", [img, up, "--length", "20", "--direction", "up"]).returncode == 0
        d, u = _pixels(down), _pixels(up)
        assert d[20, 30].min() > 0 and d[5, 30].max() == 0
        assert u[5, 30].min() > 0 and u[20, 30].max() == 0
