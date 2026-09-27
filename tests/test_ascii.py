"""Tests for ascii tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _solid(path: str, color: tuple[int, int, int]) -> str:
    Image.new("RGB", (64, 64), color).save(path)
    return path


class TestAscii:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("ascii", "ascii.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-ascii.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("ascii", "ascii.py", [img, out, "--cell", "8", "--charset", " .oO@"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "cell=8" in r.stderr

    def test_keeps_size(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "size.png")
        r = run_tool("ascii", "ascii.py", [img, out, "--cell", "12"])
        assert r.returncode == 0
        assert Image.open(out).size == Image.open(img).size

    def test_brightness_picks_glyph(self, run_tool, tmp_path):
        """Black maps to the blank first character; white maps to a visible glyph in white."""
        black = _solid(str(tmp_path / "black.png"), (0, 0, 0))
        white = _solid(str(tmp_path / "white.png"), (255, 255, 255))
        dark_out, light_out = str(tmp_path / "dark.png"), str(tmp_path / "light.png")
        assert run_tool("ascii", "ascii.py", [black, dark_out]).returncode == 0
        assert run_tool("ascii", "ascii.py", [white, light_out]).returncode == 0
        assert _pixels(dark_out).max() == 0
        assert (_pixels(light_out) > 128).any()

    def test_image_smaller_than_cell(self, run_tool, tmp_path):
        tiny = str(tmp_path / "tiny.png")
        Image.new("RGB", (4, 4), (255, 255, 255)).save(tiny)
        r = run_tool("ascii", "ascii.py", [tiny, "--cell", "10"])
        assert r.returncode != 0
        assert "smaller than one" in r.stderr

    def test_missing_input(self, run_tool):
        r = run_tool("ascii", "ascii.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("ascii", "ascii.py", [])
        assert r.returncode != 0

    def test_output_is_not_near_black(self, run_tool, tmp_workdir):
        """Bold glyphs and a stretched range keep the output readable on black."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.png")
        r = run_tool("ascii", "ascii.py", [img, out, "--cell", "8"])
        assert r.returncode == 0
        mean = np.asarray(Image.open(out).convert("RGB"), dtype=np.float64).mean()
        assert mean > 30, f"Output too dark: mean {mean:.1f}"
