"""Tests for closest-palette tool."""

from conftest import assert_valid_image


class TestClosestPalette:
    def test_with_palette(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("closest-palette", "closest-palette.py", [
            img, "--palette", "#000000,#ffffff,#ff0000",
        ])
        assert r.returncode == 0
        out = str(tmp_path / "input-palette.png")
        assert_valid_image(out)

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("closest-palette", "closest-palette.py", [
            img, out, "--palette", "#000,#fff",
        ])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "2 colors" in r.stderr

    def test_from_image(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "from-img.png")
        r = run_tool("closest-palette", "closest-palette.py", [
            img, out, "--from-image", img, "--colors", "3",
        ])
        assert r.returncode == 0
        assert_valid_image(out)

    def test_no_palette_errors(self, run_tool, tmp_workdir):
        _, img = tmp_workdir
        r = run_tool("closest-palette", "closest-palette.py", [img])
        assert r.returncode != 0
