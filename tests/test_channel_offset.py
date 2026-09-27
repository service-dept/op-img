"""Tests for channel-offset tool."""

from conftest import assert_valid_image


class TestChannelOffset:
    def test_explicit_options(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "offset.png")
        r = run_tool("channel-offset", "channel-offset.py", [
            img, out, "--r", "5,0", "--g", "0,0", "--b", "-5,0",
        ])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "r:5,0" in r.stderr
