"""Input edge cases shared by the patches added in the new-patches plan."""

import os

import numpy as np
import pytest
from PIL import Image

from conftest import assert_valid_image

# (patch directory, output suffix). Each milestone appends its patches here.
NEW_PATCHES = [
    ("fft-phase", "fftphase"),
    ("zoom-blur", "zoomblur"),
    ("swirl", "swirl"),
    ("displace", "displace"),
    ("drip", "drip"),
    ("edge-glow", "edgeglow"),
    ("contour", "contour"),
    ("hue-isolate", "hueiso"),
    ("bloom", "bloom"),
]
NAMES = [name for name, _ in NEW_PATCHES]


def _gradient_array(size: int = 64) -> np.ndarray:
    yy, xx = np.mgrid[0:size, 0:size]
    return np.stack([xx * 4, yy * 4, (xx + yy) * 2], axis=2).clip(0, 255).astype(np.uint8)


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("mode", ["RGBA", "L", "P"])
def test_accepts_other_modes(run_tool, tmp_path, name, mode):
    """Transparent, greyscale and palette inputs all produce an RGB image the same size."""
    src = str(tmp_path / f"in-{mode}.png")
    img = Image.fromarray(_gradient_array())
    if mode == "RGBA":
        img = img.convert("RGBA")
        img.putalpha(128)
    else:
        img = img.convert(mode)
    img.save(src)
    out = str(tmp_path / "out.png")
    r = run_tool(name, f"{name}.py", [src, out])
    assert r.returncode == 0, r.stderr
    result = Image.open(out)
    assert result.mode == "RGB"
    assert result.size == (64, 64)


@pytest.mark.parametrize("name", [n for n in NAMES if n != "ascii"])
@pytest.mark.parametrize("size", [1, 2, 5])
def test_tiny_images(run_tool, tmp_path, name, size):
    src = str(tmp_path / "tiny.png")
    Image.fromarray(_gradient_array(64)[:size, :size]).save(src)
    out = str(tmp_path / "out.png")
    r = run_tool(name, f"{name}.py", [src, out])
    assert r.returncode == 0, r.stderr
    assert Image.open(out).size == (size, size)


@pytest.mark.parametrize("name,suffix", NEW_PATCHES)
def test_input_without_extension_defaults_to_png(run_tool, tmp_path, name, suffix):
    src = str(tmp_path / "photo")
    Image.fromarray(_gradient_array()).save(src, format="PNG")
    r = run_tool(name, f"{name}.py", [src])
    assert r.returncode == 0, r.stderr
    assert_valid_image(str(tmp_path / f"photo-{suffix}.png"))


@pytest.mark.parametrize("name", NAMES)
def test_explicit_jpeg_output(run_tool, tmp_workdir, name):
    tmp_path, img = tmp_workdir
    out = str(tmp_path / "out.jpg")
    r = run_tool(name, f"{name}.py", [img, out])
    assert r.returncode == 0, r.stderr
    assert Image.open(out).format == "JPEG"


@pytest.mark.parametrize("name,suffix", NEW_PATCHES)
def test_runs_through_op(run_op, tmp_workdir, name, suffix):
    tmp_path, img = tmp_workdir
    r = run_op([name, img])
    assert r.returncode == 0, r.stderr
    assert os.path.isfile(str(tmp_path / f"input-{suffix}.png"))
