"""Tests for fft-phase tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


class TestFftPhase:
    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("fft-phase", "fft-phase.py", [img, out, "--amount", "0.8", "--seed", "3"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "amount=0.8" in r.stderr
        assert "seed=3" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("fft-phase", "fft-phase.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_full_amount_dissolves(self, run_tool, tmp_workdir):
        """Full phase noise moves the image far from the source."""
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "full.png")
        r = run_tool("fft-phase", "fft-phase.py", [img, out, "--amount", "1", "--seed", "1"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).mean() > 10

    def test_seed_is_repeatable(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        a, b = str(tmp_path / "a.png"), str(tmp_path / "b.png")
        assert run_tool("fft-phase", "fft-phase.py", [img, a, "--seed", "7"]).returncode == 0
        assert run_tool("fft-phase", "fft-phase.py", [img, b, "--seed", "7"]).returncode == 0
        assert np.array_equal(_pixels(a), _pixels(b))

    def test_amount_out_of_range(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("fft-phase", "fft-phase.py", [img, "--amount", "2"])
        assert r.returncode != 0
