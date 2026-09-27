"""Tests for bloom tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _bright_spot(path: str) -> str:
    """Dark gray 64x64 with a white 4x4 square in the middle."""
    arr = np.full((64, 64, 3), 40, dtype=np.uint8)
    arr[30:34, 30:34] = 255
    Image.fromarray(arr).save(path)
    return path


class TestBloom:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("bloom", "bloom.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-bloom.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("bloom", "bloom.py", [img, out, "--amount", "1.5", "--threshold", "120", "--radius", "4"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "threshold=120" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("bloom", "bloom.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_never_darkens(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "bloom.png")
        r = run_tool("bloom", "bloom.py", [img, out, "--amount", "2", "--threshold", "100"])
        assert r.returncode == 0
        assert (_pixels(out) >= _pixels(img) - 1).all()

    def test_highlight_spreads(self, run_tool, tmp_path):
        img = _bright_spot(str(tmp_path / "spot.png"))
        out = str(tmp_path / "glow.png")
        r = run_tool("bloom", "bloom.py", [img, out, "--radius", "3"])
        assert r.returncode == 0
        px = _pixels(out)
        assert px[32, 38].mean() > 40
        assert px[32, 38].mean() > px[0, 0].mean()

    def test_missing_input(self, run_tool):
        r = run_tool("bloom", "bloom.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("bloom", "bloom.py", [])
        assert r.returncode != 0
