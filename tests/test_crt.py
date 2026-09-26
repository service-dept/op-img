"""Tests for crt tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _white(path: str) -> str:
    Image.new("RGB", (64, 64), (255, 255, 255)).save(path)
    return path


class TestCrt:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("crt", "crt.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-crt.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("crt", "crt.py", [img, out, "--amount", "0.5", "--pitch", "2", "--curve", "0.2"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "pitch=2" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("crt", "crt.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_mask_and_curvature(self, run_tool, tmp_path):
        """On white, red leads in the first mask stripe, and the curved corners go black."""
        img = _white(str(tmp_path / "white.png"))
        out = str(tmp_path / "crt.png")
        r = run_tool("crt", "crt.py", [img, out, "--pitch", "3"])
        assert r.returncode == 0
        px = _pixels(out)
        # With --pitch 3, columns 27-29 are a red stripe and 30-32 a green one.
        assert px[32, 28, 0] > px[32, 28, 1]
        assert px[32, 31, 1] > px[32, 31, 0]
        assert px[0, 0].max() <= 10

    def test_missing_input(self, run_tool):
        r = run_tool("crt", "crt.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("crt", "crt.py", [])
        assert r.returncode != 0
