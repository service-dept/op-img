"""Tests for fold tool."""

from conftest import assert_valid_image


class TestFold:
    def test_y_axis_repeat(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "folded.png")
        r = run_tool("fold", "fold.py", [
            img, out, "--axis", "y", "--mode", "repeat",
        ])
        assert r.returncode == 0
        assert_valid_image(out)

    def test_invalid_axis(self, run_tool, tmp_workdir):
        _, img = tmp_workdir
        r = run_tool("fold", "fold.py", [img, "--axis", "z"])
        assert r.returncode != 0
        assert "invalid choice" in r.stderr.lower()
