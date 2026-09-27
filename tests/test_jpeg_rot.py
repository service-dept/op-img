"""Tests for jpeg-rot tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _split(path: str) -> str:
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[:, 32:] = 255
    Image.fromarray(arr).save(path)
    return path


class TestJpegRot:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("jpeg-rot", "jpeg-rot.py", [img, out, "--quality", "5", "--generations", "10"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "generations=10" in r.stderr

    def test_zero_generations_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("jpeg-rot", "jpeg-rot.py", [img, out, "--generations", "0"])
        assert r.returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_damage_without_drift(self, run_tool, tmp_path):
        """The image degrades, but the shifts are undone so the content stays where it was."""
        img = _split(str(tmp_path / "split.png"))
        out = str(tmp_path / "rot.png")
        r = run_tool("jpeg-rot", "jpeg-rot.py", [img, out, "--quality", "5", "--generations", "20"])
        assert r.returncode == 0
        px = _pixels(out)
        assert np.abs(px - _pixels(img)).mean() > 1
        assert px[:, 8].mean() < 60
        assert px[:, 56].mean() > 190
