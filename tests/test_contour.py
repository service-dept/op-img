"""Tests for contour tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image

PINK = (236, 72, 153)


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _ramp(path: str) -> str:
    """Gray ramp from black on the left to white on the right."""
    row = np.linspace(0, 255, 64).astype(np.uint8)
    arr = np.repeat(np.repeat(row[None, :, None], 64, axis=0), 3, axis=2)
    Image.fromarray(arr).save(path)
    return path


class TestContour:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("contour", "contour.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-contour.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("contour", "contour.py", [img, out, "--levels", "8", "--width", "2", "--color", "#0f0"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "color=#00ff00" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("contour", "contour.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_lines_mark_band_boundaries(self, run_tool, tmp_path):
        """A left-to-right ramp in 4 bands has 3 pink vertical lines on black."""
        img = _ramp(str(tmp_path / "ramp.png"))
        out = str(tmp_path / "lines.png")
        r = run_tool("contour", "contour.py", [img, out, "--levels", "4", "--blur", "0"])
        assert r.returncode == 0
        row = _pixels(out)[32]
        pink = [x for x in range(64) if tuple(row[x]) == PINK]
        assert len(pink) == 3
        others = [x for x in range(64) if x not in pink]
        assert row[others].max() == 0

    def test_bad_color(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("contour", "contour.py", [img, "--color", "pink"])
        assert r.returncode != 0

    def test_missing_input(self, run_tool):
        r = run_tool("contour", "contour.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("contour", "contour.py", [])
        assert r.returncode != 0
