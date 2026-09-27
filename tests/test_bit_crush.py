"""Tests for bit-crush tool."""

from conftest import assert_valid_image


class TestBitCrush:
    def test_explicit_options(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "crushed.png")
        r = run_tool("bit-crush", "bit-crush.py", [img, out, "--bits", "4"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "4-bit" in r.stderr
