"""Tests for oil-paint tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _split(path: str) -> str:
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[:, :32] = (200, 0, 0)
    arr[:, 32:] = (0, 0, 200)
    Image.fromarray(arr).save(path)
    return path


def _noise(path: str) -> str:
    rng = np.random.default_rng(0)
    Image.fromarray(rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)).save(path)
    return path


class TestOilPaint:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("oil-paint", "oil-paint.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-oilpaint.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("oil-paint", "oil-paint.py", [img, out, "--radius", "3"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "radius=3" in r.stderr

    def test_zero_radius_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("oil-paint", "oil-paint.py", [img, out, "--radius", "0"])
        assert r.returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_keeps_hard_edges(self, run_tool, tmp_path):
        """A sharp two-colour boundary survives unchanged."""
        img = _split(str(tmp_path / "split.png"))
        out = str(tmp_path / "paint.png")
        r = run_tool("oil-paint", "oil-paint.py", [img, out, "--radius", "5"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_flattens_texture(self, run_tool, tmp_path):
        img = _noise(str(tmp_path / "noise.png"))
        out = str(tmp_path / "paint.png")
        r = run_tool("oil-paint", "oil-paint.py", [img, out, "--radius", "4"])
        assert r.returncode == 0
        assert _pixels(out).std() < _pixels(img).std() * 0.6

    def test_missing_input(self, run_tool):
        r = run_tool("oil-paint", "oil-paint.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("oil-paint", "oil-paint.py", [])
        assert r.returncode != 0
