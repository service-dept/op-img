"""Conventions every patch keeps, checked once for the whole rack.

Each patch's own test file covers what is particular to it (its effect, its
options, its edge cases). Every directory in patches/ is checked; adding a patch
means adding its default output name to DEFAULT_NAMES here, and its required
options, if any, to REQUIRED_ARGS.
"""

import ast
import os

import pytest

from conftest import ROOT, assert_valid_image
from test_op_cli import ALL_PATCHES

# The name each patch gives its output when none is passed, for an input called input.png.
DEFAULT_NAMES = {
    "ascii": "input-ascii.png",
    "bit-crush": "input-crush-1bit.png",
    "bloom": "input-bloom.png",
    "channel-offset": "input-offset.png",
    "channel-swap": "input-chswap.png",
    "closest-palette": "input-palette.png",
    "contour": "input-contour.png",
    "cross-hatch": "input-hatch.png",
    "displace": "input-displace.png",
    "dither": "input-dither.png",
    "dot-halftone": "input-halftone.png",
    "drip": "input-drip.png",
    "echo": "input-echo.png",
    "edge-glow": "input-edgeglow.png",
    "fft-phase": "input-fftphase.png",
    "flow-streak": "input-flow.png",
    "fold": "input-fold.png",
    "hue-isolate": "input-hueiso.png",
    "invert-lightness": "input-invl.png",
    "isolate-threshold": "input-threshold.png",
    "jpeg-rot": "input-jpegrot.png",
    "kaleidoscope": "input-kaleido.png",
    "line-halftone": "input-lines.png",
    "oil-paint": "input-oilpaint.png",
    "pixel-sort": "input-psort.png",
    "polar": "input-polar.png",
    "posterize-hsv": "input-posterize.png",
    "raw-bend": "input-rawbend.png",
    "recolor": "input-recolor.png",
    "res-crush": "input-pixelate-64.png",
    "scan-glitch": "input-glitch.png",
    "seam-carve": "input-seamcarve.png",
    "slit-scan": "input-slitscan.png",
    "stipple": "input-stipple.png",
    "swirl": "input-swirl.png",
    "thermal": "input-thermal.png",
    "tile-shuffle": "input-shuffle.png",
    "tilt-shift": "input-tiltshift.png",
    "voronoi-mosaic": "input-voronoi.png",
    "wrong-stride": "input-stride.png",
    "zoom-blur": "input-zoomblur.png",
}

# Options a patch cannot run without.
REQUIRED_ARGS = {
    "closest-palette": ["--palette", "#000,#fff,#f00"],
}


def _script(name):
    return f"{name}.py"


def _patches():
    return [pytest.param(name, id=name) for name in ALL_PATCHES]


def test_every_patch_has_a_default_name():
    assert sorted(DEFAULT_NAMES) == sorted(ALL_PATCHES)


@pytest.mark.parametrize("name", _patches())
def test_default_output_name(run_tool, tmp_workdir, name):
    tmp_path, img = tmp_workdir
    r = run_tool(name, _script(name), [img] + REQUIRED_ARGS.get(name, []))
    assert r.returncode == 0, r.stderr
    assert_valid_image(str(tmp_path / DEFAULT_NAMES[name]))


@pytest.mark.parametrize("name", _patches())
def test_explicit_output(run_tool, tmp_workdir, name):
    tmp_path, img = tmp_workdir
    out = str(tmp_path / "explicit.png")
    r = run_tool(name, _script(name), [img, out] + REQUIRED_ARGS.get(name, []))
    assert r.returncode == 0, r.stderr
    assert_valid_image(out)


@pytest.mark.parametrize("name", _patches())
def test_runs_through_op_img(run_op, tmp_workdir, name):
    tmp_path, img = tmp_workdir
    out = str(tmp_path / "through-op-img.png")
    r = run_op([name, img, out] + REQUIRED_ARGS.get(name, []))
    assert r.returncode == 0, r.stderr
    assert_valid_image(out)


@pytest.mark.parametrize("name", _patches())
def test_missing_input(run_tool, name):
    r = run_tool(name, _script(name), ["/nonexistent/image.png"] + REQUIRED_ARGS.get(name, []))
    assert r.returncode == 1
    assert "Error: file not found" in r.stderr


@pytest.mark.parametrize("name", _patches())
def test_no_args_prints_usage(run_tool, name):
    r = run_tool(name, _script(name), [])
    assert r.returncode != 0
    assert "usage" in r.stderr.lower()


# A stack tells a later step's options from a stray file name by pairing each
# --option with the one value after it, so every option must take exactly one.
NO_SINGLE_VALUE = {"store_true", "store_false", "store_const", "append_const", "count", "help", "version"}


@pytest.mark.parametrize("name", _patches())
def test_every_option_takes_one_value(name):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tree = ast.parse(open(os.path.join(root, "patches", name, _script(name))).read())
    for call in ast.walk(tree):
        if not (isinstance(call, ast.Call) and getattr(call.func, "attr", None) == "add_argument"):
            continue
        flags = [a.value for a in call.args if isinstance(a, ast.Constant)]
        if not any(str(f).startswith("-") for f in flags):
            continue
        keywords = {k.arg: k.value for k in call.keywords}
        action = keywords.get("action")
        assert not (isinstance(action, ast.Constant) and action.value in NO_SINGLE_VALUE), f"{flags} takes no value"
        assert "nargs" not in keywords, f"{flags} sets nargs"


@pytest.mark.parametrize("name", _patches())
def test_patch_directory_holds_its_script_and_images(name):
    folder = os.path.join(ROOT, "patches", name)
    extra = [f for f in os.listdir(folder) if f != _script(name) and not f.endswith(".jpg")]
    assert extra == [], f"patches/{name} holds {extra}; dependencies go in pyproject.toml"


@pytest.mark.parametrize("name", _patches())
def test_patch_script_is_executable(name):
    # Every patch script starts with a #! line, so it can be run directly.
    assert os.access(os.path.join(ROOT, "patches", name, _script(name)), os.X_OK)
