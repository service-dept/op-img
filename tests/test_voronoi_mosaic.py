"""Tests for voronoi-mosaic tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestVoronoiMosaic:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("voronoi-mosaic", "voronoi-mosaic.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-voronoi.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("voronoi-mosaic", "voronoi-mosaic.py", [img, out, "--size", "12", "--edges", "2", "--seed", "4"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "size=12" in r.stderr
        assert "edges=2" in r.stderr

    def test_single_pixel_cells_are_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("voronoi-mosaic", "voronoi-mosaic.py", [img, out, "--size", "1", "--jitter", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_one_colour_per_cell(self, run_tool, tmp_workdir):
        """16-pixel cells on a 64x64 image give 16 seeds, so at most 16 colours."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "cells.png")
        r = run_tool("voronoi-mosaic", "voronoi-mosaic.py", [img, out, "--size", "16", "--seed", "1"])
        assert r.returncode == 0
        colours = {tuple(p) for p in _pixels(out).reshape(-1, 3)}
        assert 2 <= len(colours) <= 16

    def test_size_out_of_range(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("voronoi-mosaic", "voronoi-mosaic.py", [img, "--size", "0"])
        assert r.returncode != 0

    def test_missing_input(self, run_tool):
        r = run_tool("voronoi-mosaic", "voronoi-mosaic.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("voronoi-mosaic", "voronoi-mosaic.py", [])
        assert r.returncode != 0
