"""Tests for tilt-shift tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _checker(path: str) -> str:
    """Gray checkerboard of 2-pixel squares; gray is unaffected by the saturation lift."""
    yy, xx = np.mgrid[0:64, 0:64]
    gray = np.where(((yy // 2) + (xx // 2)) % 2 == 0, 200, 50).astype(np.uint8)
    Image.fromarray(np.repeat(gray[:, :, None], 3, axis=2)).save(path)
    return path


def _sharpness(arr: np.ndarray) -> float:
    return float(np.abs(np.diff(arr[:, :, 0], axis=1)).mean())


class TestTiltShift:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("tilt-shift", "tilt-shift.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-tiltshift.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("tilt-shift", "tilt-shift.py", [img, out, "--blur", "6", "--focus", "0.5", "--band", "0.2"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "focus=0.5" in r.stderr

    def test_zero_blur_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("tilt-shift", "tilt-shift.py", [img, out, "--blur", "0"])
        assert r.returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_band_stays_sharp(self, run_tool, tmp_path):
        """Rows in the focus band keep their detail; rows at the top lose it."""
        img = _checker(str(tmp_path / "checker.png"))
        out = str(tmp_path / "tilt.png")
        r = run_tool("tilt-shift", "tilt-shift.py", [img, out, "--blur", "8", "--focus", "0.5", "--band", "0.25"])
        assert r.returncode == 0
        px = _pixels(out)
        assert _sharpness(px[28:36]) > 3 * _sharpness(px[0:6])

    def test_blur_out_of_range(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("tilt-shift", "tilt-shift.py", [img, "--blur", "100"])
        assert r.returncode != 0

    def test_missing_input(self, run_tool):
        r = run_tool("tilt-shift", "tilt-shift.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("tilt-shift", "tilt-shift.py", [])
        assert r.returncode != 0
