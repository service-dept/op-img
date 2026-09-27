"""Tests for wrong-stride tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


class TestWrongStride:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("wrong-stride", "wrong-stride.py", [img, out, "--offset", "5"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "offset=5" in r.stderr

    def test_output_dimensions_match(self, run_tool, tmp_workdir):
        """Output dimensions should match input dimensions."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "strided.png")
        r = run_tool("wrong-stride", "wrong-stride.py", [img, out, "--offset", "3"])
        assert r.returncode == 0
        original = Image.open(img)
        result = Image.open(out)
        assert original.size == result.size
