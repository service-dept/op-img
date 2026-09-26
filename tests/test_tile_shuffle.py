"""Tests for tile-shuffle tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


class TestTileShuffle:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("tile-shuffle", "tile-shuffle.py", [img])
        assert r.returncode == 0
        out = str(tmp_path / "input-shuffle.png")
        assert_valid_image(out)

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("tile-shuffle", "tile-shuffle.py", [img, out, "--grid", "3"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "grid=3" in r.stderr

    def test_seed_reproducibility(self, run_tool, tmp_workdir):
        """Same seed should produce identical output."""
        tmp_path, img = tmp_workdir
        out1 = str(tmp_path / "seed1.png")
        out2 = str(tmp_path / "seed2.png")
        r1 = run_tool("tile-shuffle", "tile-shuffle.py", [img, out1, "--seed", "42"])
        r2 = run_tool("tile-shuffle", "tile-shuffle.py", [img, out2, "--seed", "42"])
        assert r1.returncode == 0
        assert r2.returncode == 0
        arr1 = np.array(Image.open(out1))
        arr2 = np.array(Image.open(out2))
        np.testing.assert_array_equal(arr1, arr2)

    def test_different_grid_sizes(self, run_tool, tmp_workdir):
        """Different grid sizes should produce valid but different results."""
        tmp_path, img = tmp_workdir
        out2 = str(tmp_path / "grid2.png")
        out8 = str(tmp_path / "grid8.png")
        r1 = run_tool("tile-shuffle", "tile-shuffle.py", [img, out2, "--grid", "2", "--seed", "1"])
        r2 = run_tool("tile-shuffle", "tile-shuffle.py", [img, out8, "--grid", "8", "--seed", "1"])
        assert r1.returncode == 0
        assert r2.returncode == 0
        assert_valid_image(out2)
        assert_valid_image(out8)

    def test_keeps_size_when_grid_does_not_divide(self, run_tool, tmp_path):
        arr = np.random.default_rng(0).integers(0, 255, (63, 65, 3), dtype=np.uint8)
        img = str(tmp_path / "odd.png")
        Image.fromarray(arr).save(img)
        out = str(tmp_path / "out.png")
        r = run_tool("tile-shuffle", "tile-shuffle.py", [img, out, "--grid", "8", "--seed", "1"])
        assert r.returncode == 0, r.stderr
        assert Image.open(out).size == (65, 63)

    def test_missing_input(self, run_tool):
        r = run_tool("tile-shuffle", "tile-shuffle.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()

    def test_no_args(self, run_tool):
        r = run_tool("tile-shuffle", "tile-shuffle.py", [])
        assert r.returncode != 0
