# Homebrew install

The staged formula is [`Formula/op-img.rb`](../../Formula/op-img.rb). It installs
the published PyPI **0.1.0** sdist with its SHA-256 checksum and MIT license.
It is intended for both macOS and Linux; the Homebrew workflow builds from source
and runs the formula test on each platform.

## Packaging

- Use a tap, not homebrew-core. The intended public destination is
  `service-dept/homebrew-tap`, with the formula at `Formula/op-img.rb`.
- Keep a source copy here so changes can be reviewed and tested before the tap
  is published. The tap is a separate publication step; adding this file alone
  does **not** make `brew install service-dept/tap/op-img` available.
- Use Homebrew's `Language::Python::Virtualenv` with `python@3.14`, `numpy`,
  `scipy`, and `pillow`. The Python version must match the bindings shipped by
  those formulae. The original Python 3.12 proposal does not match their current
  Python 3.13/3.14 builds.
- The virtualenv helper exposes the matching Homebrew dependency paths and
  installs the `op-img` command. Exclude the three shared packages from
  `brew update-python-resources`; no Python runtime resources are needed.
  The sdist's Hatch build requirements use pip's normal isolated build.
- The formula test lists patches, generates a small PNG using the installed
  virtualenv, runs `bit-crush`, and checks the output pixels. It also runs `swirl`
  to exercise SciPy's native dependency, then verifies both output images.

## Test before publishing

From this checkout on a supported Homebrew installation:

```bash
brew tap-new --no-git service-dept/op-img-ci
cp Formula/op-img.rb "$(brew --repository service-dept/op-img-ci)/Formula/op-img.rb"
brew style service-dept/op-img-ci/op-img
brew install --build-from-source service-dept/op-img-ci/op-img
brew audit --strict service-dept/op-img-ci/op-img
brew test service-dept/op-img-ci/op-img
```

Use `brew reinstall --build-from-source service-dept/op-img-ci/op-img` after
changing a formula that is already installed. The local test tap does not need a
GitHub repository. To remove the test install afterward:

```bash
brew uninstall service-dept/op-img-ci/op-img
brew untap service-dept/op-img-ci
```

The [`Homebrew` workflow](../../.github/workflows/homebrew.yml) runs these checks
on `macos-latest` and `ubuntu-latest` when the formula or workflow changes, every
Monday to catch Homebrew dependency updates, and can also be started manually. It installs the **released sdist**, not the current
checkout's Python code. The regular test workflow covers the checkout.

## Publish the tap

After the Homebrew checks pass on both platforms:

1. Create `service-dept/homebrew-tap` and copy `Formula/op-img.rb` into it.
2. Make that tap public, then verify a fresh install with
   `brew install service-dept/tap/op-img` and `brew test op-img`.
3. Add Homebrew as an installation option in the README only after that command
   works. Keep the existing pipx-first quick start until then.

These repository and publication steps are manual and happen only after the
platform checks pass.

## Release flow

1. Publish a GitHub release and wait for `Publish to PyPI` to succeed.
2. Read the new release's sdist URL and SHA-256 from PyPI, update the source
   formula here, and run the Homebrew workflow. Do not point it at a moving branch.
3. Update the tap's formula to the same tested URL and checksum, for example with
   `brew bump-formula-pr --url … service-dept/tap/op-img`.
4. Run `brew install --build-from-source service-dept/tap/op-img` (or `reinstall`)
   and `brew test op-img` on macOS and Linux.

When Homebrew changes Python bindings, update the formula's Python dependency and
increment its `revision` if the op-img release is unchanged. Re-run the platform
checks. Automated tap PRs and bottled op-img releases can be added later.
