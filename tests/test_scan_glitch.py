"""Tests for scan-glitch tool."""

import os

from conftest import assert_valid_image


class TestScanGlitch:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("scan-glitch", "scan-glitch.py", [img, out, "--severity", "3", "--seed", "42"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "severity=3" in r.stderr

    def test_seed_reproducibility(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out1 = str(tmp_path / "a.png")
        out2 = str(tmp_path / "b.png")
        run_tool("scan-glitch", "scan-glitch.py", [img, out1, "--seed", "99"])
        run_tool("scan-glitch", "scan-glitch.py", [img, out2, "--seed", "99"])
        with open(out1, "rb") as f1, open(out2, "rb") as f2:
            assert f1.read() == f2.read()
