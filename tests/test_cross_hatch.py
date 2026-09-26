"""Tests for cross-hatch tool."""

from conftest import assert_valid_image


class TestCrossHatch:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("cross-hatch", "cross-hatch.py", [img])
        assert r.returncode == 0
        out = str(tmp_path / "input-hatch.png")
        assert_valid_image(out)

    def test_explicit_options(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "hatch.png")
        r = run_tool("cross-hatch", "cross-hatch.py", [
            img, out, "--layers", "2", "--spacing", "8", "--thresholds", "180,80",
        ])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "layers=2" in r.stderr

    def test_threshold_count_mismatch(self, run_tool, tmp_workdir):
        _, img = tmp_workdir
        r = run_tool("cross-hatch", "cross-hatch.py", [
            img, "--layers", "3", "--thresholds", "200,100",
        ])
        assert r.returncode != 0

    def test_missing_input(self, run_tool):
        r = run_tool("cross-hatch", "cross-hatch.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()

    def test_no_args(self, run_tool):
        r = run_tool("cross-hatch", "cross-hatch.py", [])
        assert r.returncode != 0
