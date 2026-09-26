"""Tests for stipple tool."""

from conftest import assert_valid_image


class TestStipple:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("stipple", "stipple.py", [img])
        assert r.returncode == 0
        out = str(tmp_path / "input-stipple.png")
        assert_valid_image(out)

    def test_explicit_options(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "stip.png")
        r = run_tool("stipple", "stipple.py", [
            img, out, "--dots", "1000", "--dot-size", "2", "--seed", "42",
        ])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "dots=1000" in r.stderr

    def test_seed_reproducibility(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out1 = str(tmp_path / "a.png")
        out2 = str(tmp_path / "b.png")
        run_tool("stipple", "stipple.py", [img, out1, "--seed", "7"])
        run_tool("stipple", "stipple.py", [img, out2, "--seed", "7"])
        with open(out1, "rb") as f1, open(out2, "rb") as f2:
            assert f1.read() == f2.read()

    def test_missing_input(self, run_tool):
        r = run_tool("stipple", "stipple.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "not found" in r.stderr.lower()

    def test_no_args(self, run_tool):
        r = run_tool("stipple", "stipple.py", [])
        assert r.returncode != 0
