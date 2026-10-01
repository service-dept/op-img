"""Tests for line-halftone tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


class TestLineHalftone:
    def test_explicit_options(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "lines.png")
        r = run_tool("line-halftone", "line-halftone.py", [
            img, out, "--spacing", "10", "--min-width", "1", "--max-width", "8", "--angle", "90",
        ])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "spacing=10" in r.stderr

    def test_output_is_rgba(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "rgba.png")
        r = run_tool("line-halftone", "line-halftone.py", [img, out])
        assert r.returncode == 0
        result = assert_valid_image(out)
        assert result.mode == "RGBA"

    def test_jpeg_output_gets_a_white_background(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "out.jpg")
        r = run_tool("line-halftone", "line-halftone.py", [img, out])
        assert r.returncode == 0, r.stderr
        result = Image.open(out)
        assert result.format == "JPEG" and result.mode == "RGB"
        assert (np.asarray(result) >= 250).all(axis=2).any(), "no white background showing"
