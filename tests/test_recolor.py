"""Tests for recolor tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _two_color_image(path):
    """Left 40 columns orange, right 24 columns green, each with a lightness ramp, 64x64."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    ramp = np.linspace(0.6, 1.0, 64)[:, None]
    arr[:, :40] = (np.array([230, 120, 30])[None, None, :] * ramp[:, :, None]).astype(np.uint8)
    arr[:, 40:] = (np.array([60, 150, 50])[None, None, :] * ramp[:, :, None]).astype(np.uint8)
    Image.fromarray(arr).save(path)
    return path


def _mean(path, cols):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float64)[:, cols].reshape(-1, 3).mean(0)


class TestRecolor:
    def test_amount_zero_is_identity(self, run_tool, tmp_path):
        img = _two_color_image(str(tmp_path / "two.png"))
        out = str(tmp_path / "out.png")
        r = run_tool("recolor", "recolor.py", [img, out, "--colors", "#1e3a8a", "--amount", "0"])
        assert r.returncode == 0, r.stderr
        assert np.array_equal(np.asarray(Image.open(out)), np.asarray(Image.open(img)))

    def test_one_color_replaces_the_most_prevalent(self, run_tool, tmp_path):
        img = _two_color_image(str(tmp_path / "two.png"))
        out = str(tmp_path / "out.png")
        r = run_tool("recolor", "recolor.py", [img, out, "--colors", "#1e3a8a"])
        assert r.returncode == 0, r.stderr
        before_left, after_left = _mean(img, slice(0, 40)), _mean(out, slice(0, 40))
        assert after_left[2] > after_left[0], f"orange area should turn blue: {after_left}"
        assert before_left[0] > before_left[2]
        assert np.abs(_mean(out, slice(44, 64)) - _mean(img, slice(44, 64))).max() < 6, "the green area should barely change"

    def test_two_colors_replace_the_top_two(self, run_tool, tmp_path):
        img = _two_color_image(str(tmp_path / "two.png"))
        out = str(tmp_path / "out.png")
        r = run_tool("recolor", "recolor.py", [img, out, "--colors", "#1e3a8a,#facc15"])
        assert r.returncode == 0, r.stderr
        left, right = _mean(out, slice(0, 36)), _mean(out, slice(44, 64))
        assert left[2] > left[0], f"orange area should turn blue: {left}"
        assert right[0] > right[2] and right[1] > right[2], f"green area should turn yellow: {right}"

    def test_keeps_light_and_shade(self, run_tool, tmp_path):
        img = _two_color_image(str(tmp_path / "two.png"))
        out = str(tmp_path / "out.png")
        assert run_tool("recolor", "recolor.py", [img, out, "--colors", "#1e3a8a"]).returncode == 0
        arr = np.asarray(Image.open(out).convert("L"), dtype=np.float64)[:, :36]
        assert arr[-8:].mean() > arr[:8].mean() + 10, "the lightness ramp should survive"

    def test_gray_image_is_unchanged(self, run_tool, tmp_path):
        gray = np.tile(np.linspace(0, 255, 64, dtype=np.uint8)[None, :, None], (64, 1, 3))
        img = str(tmp_path / "gray.png")
        Image.fromarray(gray).save(img)
        out = str(tmp_path / "out.png")
        r = run_tool("recolor", "recolor.py", [img, out, "--colors", "#ec4899"])
        assert r.returncode == 0, r.stderr
        assert np.abs(np.asarray(Image.open(out), dtype=int) - gray.astype(int)).max() <= 1

    def test_bad_color_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("recolor", "recolor.py", [img, "--colors", "#12345z"])
        assert r.returncode == 2
        assert "not a color" in r.stderr

    def test_too_many_colors_is_an_error(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("recolor", "recolor.py", [img, "--colors", "red,blue", "--clusters", "2"])
        assert r.returncode == 2
        assert "fewer colors" in r.stderr

    def test_neighboring_color_is_left_alone(self, run_tool, tmp_path):
        """A red 33 degrees of hue from the orange is its own family and keeps its color."""
        arr = np.zeros((64, 64, 3), dtype=np.uint8)
        ramp = np.linspace(0.6, 1.0, 64)[:, None]
        arr[:, :40] = (np.array([230, 120, 30])[None, None, :] * ramp[:, :, None]).astype(np.uint8)
        arr[:, 40:] = (np.array([220, 40, 70])[None, None, :] * ramp[:, :, None]).astype(np.uint8)
        img = str(tmp_path / "near.png")
        Image.fromarray(arr).save(img)
        out = str(tmp_path / "out.png")
        r = run_tool("recolor", "recolor.py", [img, out, "--colors", "#1e3a8a"])
        assert r.returncode == 0, r.stderr
        assert _mean(out, slice(0, 36))[2] > _mean(out, slice(0, 36))[0], "the orange should turn blue"
        change = np.abs(_mean(out, slice(44, 64)) - _mean(img, slice(44, 64))).max()
        assert change < 8, f"the red changed by {change:.1f}"
