"""Tests for flow-streak tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _horizontal_stripes(path: str) -> str:
    """4-pixel stripes that are constant along x, so the flow runs horizontally everywhere."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    for y in range(64):
        arr[y, :] = (230, 200, 40) if (y // 4) % 2 == 0 else (20, 40, 90)
    Image.fromarray(arr).save(path)
    return path


class TestFlowStreak:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("flow-streak", "flow-streak.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-flow.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("flow-streak", "flow-streak.py", [img, out, "--length", "6", "--sigma", "2"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "length=6" in r.stderr

    def test_zero_length_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("flow-streak", "flow-streak.py", [img, out, "--length", "0"])
        assert r.returncode == 0
        assert np.array_equal(_pixels(out), _pixels(img))

    def test_streaks_follow_contours(self, run_tool, tmp_path):
        """Streaking along horizontal contours leaves horizontal stripes intact."""
        img = _horizontal_stripes(str(tmp_path / "stripes.png"))
        out = str(tmp_path / "flow.png")
        r = run_tool("flow-streak", "flow-streak.py", [img, out, "--length", "12"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_changes_a_photo(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "flow.png")
        r = run_tool("flow-streak", "flow-streak.py", [img, out, "--length", "12"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).mean() > 1

    def test_missing_input(self, run_tool):
        r = run_tool("flow-streak", "flow-streak.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("flow-streak", "flow-streak.py", [])
        assert r.returncode != 0
