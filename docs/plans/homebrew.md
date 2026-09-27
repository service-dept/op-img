# Homebrew install

Follow-up to publishing op-img on PyPI: let macOS and Linux users install it with one Homebrew command, dependencies included.

```bash
brew install service-dept/tap/op-img
```

## Why
`pipx install op-img` needs Python and pipx first. A Homebrew formula brings its own Python and the libraries op-img uses, so `brew install` is the whole setup.

## Shape
- **A tap, not homebrew-core.** Create `service-dept/homebrew-tap` with `Formula/op-img.rb`. homebrew-core would need a license, a stable release history and review; a tap needs none of that and can move to core later.
- **The formula installs from the PyPI sdist.**
  - It uses Homebrew's `Language::Python::Virtualenv`: `url` and `sha256` point at the release's `op_img-<version>.tar.gz` on PyPI.
  - It depends on `python@3.12` and Homebrew's `numpy`, `scipy` and `pillow` formulae, so no library needs a `resource` block.
  - If one is needed later, `brew update-python-resources op-img` fills it in.
- **The command is `op-img`,** the same name as the PyPI and clone installs.
- **The test block** runs `op-img --list` and one patch on a generated image: `op-img bit-crush` on a small PNG made with Pillow inside the test.

## Release flow
1. Publish a GitHub release; the `Publish to PyPI` workflow uploads the sdist and wheel.
2. In the tap, bump `url` and `sha256` to the new sdist (`brew bump-formula-pr --url … op-img` does both).
3. Check with `brew install --build-from-source service-dept/tap/op-img` and `brew test op-img`.

Later, a workflow in this repository could open that tap PR automatically on each release.

## Before starting
- op-img is on PyPI (the first release is published).
- A license is chosen. The tap works without one, but Homebrew shows the license field, and homebrew-core requires an open-source license.

## Open questions
- macOS only, or Linux (Linuxbrew) too? The formula is the same, but testing on both takes a Linux runner.
- Should the README list Homebrew first once the tap exists, with pipx second?
