"""Tests for edge-glow tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _split(path: str) -> str:
    """Left half dark blue, right half light orange: one vertical edge at x=32."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[:, :32] = (10, 20, 60)
    arr[:, 32:] = (240, 150, 60)
    Image.fromarray(arr).save(path)
    return path


class TestEdgeGlow:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("edge-glow", "edge-glow.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-edgeglow.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("edge-glow", "edge-glow.py", [img, out, "--amount", "0.5", "--radius", "3"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "amount=0.5" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("edge-glow", "edge-glow.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_glow_sits_on_the_edge(self, run_tool, tmp_path):
        img = _split(str(tmp_path / "split.png"))
        out = str(tmp_path / "glow.png")
        r = run_tool("edge-glow", "edge-glow.py", [img, out, "--radius", "2"])
        assert r.returncode == 0
        px = _pixels(out).sum(axis=2)
        assert px[:, 30:34].mean() > 100
        assert px[:, :8].max() <= 3
        assert px[:, -8:].max() <= 3

    def test_missing_input(self, run_tool):
        r = run_tool("edge-glow", "edge-glow.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("edge-glow", "edge-glow.py", [])
        assert r.returncode != 0
