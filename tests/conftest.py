"""Shared fixtures for op-img test suite."""

import os
import subprocess

import numpy as np
import pytest
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OP = os.path.join(ROOT, "op-img")



def _make_gradient(path: str, size: int = 64) -> str:
    """Create a 64x64 RGB gradient PNG with enough variation for all tools."""
    arr = np.zeros((size, size, 3), dtype=np.uint8)
    for y in range(size):
        for x in range(size):
            arr[y, x] = [
                int(255 * x / size),       # R: left-to-right
                int(255 * y / size),       # G: top-to-bottom
                int(128 + 127 * np.sin(x * y * 0.01)),  # B: pattern
            ]
    Image.fromarray(arr).save(path)
    return path


@pytest.fixture
def tmp_workdir(tmp_path):
    """Provide a temp directory with a 64x64 gradient test image at 'input.png'."""
    img_path = str(tmp_path / "input.png")
    _make_gradient(img_path)
    return tmp_path, img_path


@pytest.fixture
def run_tool():
    """Run a tool script directly via subprocess. Returns CompletedProcess."""
    def _run(tool_dir: str, script_name: str, args: list[str], **kwargs) -> subprocess.CompletedProcess:
        script_path = os.path.join(ROOT, "patches", tool_dir, script_name)
        if script_name.endswith(".py"):
            cmd = ["python3", script_path] + args
        else:
            cmd = [script_path] + args
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            **kwargs,
        )
    return _run


@pytest.fixture
def run_op():
    """Run a command through the `op` dispatcher. Returns CompletedProcess."""
    def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess:
        return subprocess.run(
            [OP] + args,
            capture_output=True,
            text=True,
            timeout=60,
            **kwargs,
        )
    return _run


def assert_valid_image(path: str, min_size: int = 100) -> Image.Image:
    """Assert the file exists, has non-trivial size, and is a valid image."""
    assert os.path.isfile(path), f"Output file not found: {path}"
    assert os.path.getsize(path) > min_size, f"Output file too small: {os.path.getsize(path)} bytes"
    img = Image.open(path)
    img.load()  # force decode
    return img
