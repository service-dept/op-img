# Homebrew install

The staged formula is [`Formula/op-img.rb`](../../Formula/op-img.rb). It installs
the published PyPI **0.1.0** sdist with its SHA-256 checksum and MIT license.
It is intended for both macOS and Linux; the Homebrew workflow builds from source
and runs the formula test on each platform.

## Packaging

- Use a tap, not homebrew-core. The public tap is
  [`service-dept/homebrew-tap`](https://github.com/service-dept/homebrew-tap),
  with the formula at `Formula/op-img.rb`.
- Keep a source copy here so changes can be reviewed and tested before they
  reach the tap. Changing this file alone does **not** change what
  `brew install service-dept/tap/op-img` installs.
- Use Homebrew's `Language::Python::Virtualenv` with `python@3.14`, `numpy`,
  `scipy`, and `pillow`. The Python version must match the bindings shipped by
  those formulae. The original Python 3.12 proposal does not match their current
  Python 3.13/3.14 builds.
- The virtualenv uses `python@3.14`'s system site-packages, where the linked
  `numpy`, `scipy`, and `pillow` kegs install their bindings, and it installs
  the `op-img` command. Exclude the three shared packages from
  `brew update-python-resources`; no Python runtime resources are needed.
- The sdist's Hatch build requirements use pip's normal isolated build, so a
  source install downloads and builds `hatchling` and its dependencies from
  PyPI. Those are not pinned, and the install needs network access while it
  builds. Bottles would remove that for users.
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
Monday to catch Homebrew dependency updates, and can also be started manually.
GitHub disables scheduled workflows after 60 days without repository activity;
re-enable it from the Actions tab if the Monday runs stop. It installs the
**released sdist**, not the current checkout's Python code. The regular test
workflow covers the checkout. The local tap has no git history, so `brew audit`
skips its version and checksum history checks there.

## The tap

`service-dept/homebrew-tap` is public and holds a copy of `Formula/op-img.rb`.
Its `Tests` workflow runs the same style, install, audit and test checks against
the tap itself on macOS and Linux, on every PR, on `main`, and every Monday.
There the audit also checks the version and checksum history. The README lists
Homebrew as an install option after pipx.

## Release flow

1. Publish a GitHub release and wait for `Publish to PyPI` to succeed.
2. Read the new release's sdist URL and SHA-256 from PyPI, update the source
   formula here, and run the Homebrew workflow. Do not point it at a moving branch.
3. Update the tap's formula to the same tested URL and checksum, for example with
   `brew bump-formula-pr --url … service-dept/tap/op-img`.
4. Merge the tap PR once its `Tests` workflow passes on macOS and Linux.

When Homebrew changes Python bindings, update the formula's Python dependency and
increment its `revision` if the op-img release is unchanged. Re-run the platform
checks. Automated tap PRs and bottled op-img releases can be added later.
