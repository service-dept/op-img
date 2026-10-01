class OpImg < Formula
  include Language::Python::Virtualenv

  desc "Composable image manipulation CLI"
  homepage "https://github.com/service-dept/op-img"
  url "https://files.pythonhosted.org/packages/7a/f7/c91d5a75b9813568b9d3d1f90a87e372af297e113c81ca456bc0e61bb251/op_img-0.1.0.tar.gz"
  sha256 "23ab800c8fb4b2707e8ed4cb0057ec4b13a821e2e49cb3ec28e7dc00f6511fe5"
  license "MIT"

  depends_on "numpy" => :no_linkage
  depends_on "pillow" => :no_linkage
  depends_on "python@3.14"
  depends_on "scipy" => :no_linkage

  pypi_packages exclude_packages: %w[numpy pillow scipy]

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "bit-crush", shell_output("#{bin}/op-img --list")

    # Use the installed virtualenv, so this also verifies Homebrew's dependencies.
    system libexec/"bin/python", "-c", <<~PYTHON
      import numpy as np
      from PIL import Image

      pixels = np.arange(16 * 16 * 3, dtype=np.uint8).reshape(16, 16, 3)
      Image.fromarray(pixels).save("input.png")
    PYTHON

    system bin/"op-img", "bit-crush", "input.png", "output.png", "--bits", "1"
    # Swirl exercises SciPy's compiled extension, which bit-crush does not use.
    system bin/"op-img", "swirl", "input.png", "swirl.png", "--angle", "90"

    system libexec/"bin/python", "-c", <<~PYTHON
      import numpy as np
      from PIL import Image

      for path in ("output.png", "swirl.png"):
          with Image.open(path) as image:
              image.load()
              assert image.format == "PNG"
              assert image.size == (16, 16)
              assert image.mode == "RGB"
              if path == "output.png":
                  for channel in range(3):
                      assert set(np.unique(np.asarray(image)[:, :, channel])) == {0, 255}
    PYTHON
  end
end
