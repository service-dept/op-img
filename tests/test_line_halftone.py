"""Tests for line-halftone tool."""

from conftest import assert_valid_image


class TestLineHalftone:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("line-halftone", "line-halftone.py", [img])
        assert r.returncode == 0
        out = str(tmp_path / "input-lines.png")
        assert_valid_image(out)

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

    def test_missing_input(self, run_tool):
        r = run_tool("line-halftone", "line-halftone.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()

    def test_no_args(self, run_tool):
        r = run_tool("line-halftone", "line-halftone.py", [])
        assert r.returncode != 0
