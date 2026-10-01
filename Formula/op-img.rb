class OpImg < Formula
  include Language::Python::Virtualenv

  desc "Composable image manipulation CLI"
  homepage "https://github.com/service-dept/op-img"
  url "https://files.pythonhosted.org/packages/aa/e6/222ac04e17be70de7e010fa026a156409ecebe99448dc8d692397330f939/op_img-0.2.0.tar.gz"
  sha256 "9f128e008481c17c0501060b6261f5dfe6916447b4b08740ecce5fe6ea1ab13c"
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
