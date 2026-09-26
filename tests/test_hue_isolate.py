"""Tests for hue-isolate tool."""

import numpy as np
from PIL import Image

from conftest import assert_valid_image


def _pixels(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"), dtype=np.int64)


def _orange_and_green(path: str) -> str:
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    arr[:, :32] = (240, 120, 20)
    arr[:, 32:] = (40, 180, 60)
    Image.fromarray(arr).save(path)
    return path


class TestHueIsolate:
    def test_default_args(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        r = run_tool("hue-isolate", "hue-isolate.py", [img])
        assert r.returncode == 0
        assert_valid_image(str(tmp_path / "input-hueiso.png"))

    def test_explicit_output(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "custom.png")
        r = run_tool("hue-isolate", "hue-isolate.py", [img, out, "--hue", "200", "--width", "30", "--amount", "0.7"])
        assert r.returncode == 0
        assert_valid_image(out)
        assert "hue=200.0" in r.stderr

    def test_zero_amount_is_identity(self, run_tool, tmp_workdir):
        tmp_path, img = tmp_workdir
        out = str(tmp_path / "same.png")
        r = run_tool("hue-isolate", "hue-isolate.py", [img, out, "--amount", "0"])
        assert r.returncode == 0
        assert np.abs(_pixels(out) - _pixels(img)).max() <= 1

    def test_keeps_orange_greys_green(self, run_tool, tmp_path):
        img = _orange_and_green(str(tmp_path / "two.png"))
        out = str(tmp_path / "pop.png")
        r = run_tool("hue-isolate", "hue-isolate.py", [img, out])
        assert r.returncode == 0
        px = _pixels(out)
        assert tuple(px[10, 10]) == (240, 120, 20)
        green = px[10, 50]
        assert green.max() - green.min() <= 1

    def test_missing_input(self, run_tool):
        r = run_tool("hue-isolate", "hue-isolate.py", ["/nonexistent/image.png"])
        assert r.returncode != 0
        assert "Error: file not found" in r.stderr

    def test_no_args(self, run_tool):
        r = run_tool("hue-isolate", "hue-isolate.py", [])
        assert r.returncode != 0
