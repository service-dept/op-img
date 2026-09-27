"""Tests for dot-halftone tool."""

from conftest import assert_valid_image


class TestDotHalftone:
    def test_explicit_options(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "dots.png")
        r = run_tool("dot-halftone", "dot-halftone.py", [
            img, out, "--spacing", "12", "--min-dot", "1", "--max-dot", "5", "--angle", "45",
        ])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "spacing=12" in r.stderr

    def test_output_is_rgba(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "rgba.png")
        r = run_tool("dot-halftone", "dot-halftone.py", [img, out])
        assert r.returncode == 0
        result = assert_valid_image(out)
        assert result.mode == "RGBA"
