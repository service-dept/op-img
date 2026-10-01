"""The op-img command: runs a patch by name, or a stack of patches joined with `+`."""

import os
import random
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BANNER = """\
░░      ░░░       ░░░        ░░  ░░░░  ░░░      ░░
▒  ▒▒▒▒  ▒▒  ▒▒▒▒  ▒▒▒▒▒  ▒▒▒▒▒   ▒▒   ▒▒  ▒▒▒▒▒▒▒
▓  ▓▓▓▓  ▓▓       ▓▓▓▓▓▓  ▓▓▓▓▓        ▓▓  ▓▓▓   ▓
█  ████  ██  ███████████  █████  █  █  ██  ████  █
██      ███  ████████        ██  ████  ███      ██"""


def patch_dir() -> Path:
    """The patches: inside the installed package, or next to it in a clone."""
    here = Path(__file__).resolve().parent
    return here / "patches" if (here / "patches").is_dir() else here.parent / "patches"


def patch_script(name: str) -> Path | None:
    """The script that runs a patch, or None if there is no such patch."""
    for ext in (".sh", ".py"):
        script = patch_dir() / name / f"{name}{ext}"
        if script.is_file():
            return script
    return None


def all_patches() -> list[str]:
    return sorted(d.name for d in patch_dir().iterdir() if d.is_dir() and patch_script(d.name))


def command(script: Path, args: list[str]) -> list[str]:
    # Python patches run on this interpreter, which is the one with op-img's dependencies.
    return [str(script)] + args if script.suffix == ".sh" else [sys.executable, str(script)] + args


def unknown_patch(name: str) -> int:
    print(f"Error: unknown patch '{name}'", file=sys.stderr)
    print("", file=sys.stderr)
    print("Available patches:", file=sys.stderr)
    for p in all_patches():
        print(f"  {p}", file=sys.stderr)
    return 1


def show_help() -> int:
    patches = all_patches()
    print("")
    print(BANNER)
    print("")
    print("Usage: op-img <patch> <input> [--args]")
    print("       op-img <patch> <input> [output] [--args] + <patch> [--args] ...")
    print("")
    print(f"Patches (3 of {len(patches)}):")
    for p in sorted(random.sample(patches, min(3, len(patches)))):
        print(f"  {p}")
    print("")
    print("Run 'op-img --list' to see all patches.")
    print("Run 'op-img --info <patch>' to see available args.")
    print("")
    return 0


def run(script: Path, args: list[str]) -> int:
    """Run one patch in the foreground, passing its output and exit code through."""
    return subprocess.run(command(script, args)).returncode


def place(src: Path, dest: Path) -> None:
    """Copy src beside dest, then rename it over dest, so dest is never left half written.
    The result gets the permissions a plain write would."""
    fd, staged = tempfile.mkstemp(prefix=".op-stack.", dir=dest.parent)
    os.close(fd)
    try:
        shutil.copyfile(src, staged)
        umask = os.umask(0)
        os.umask(umask)
        os.chmod(staged, 0o666 & ~umask)
        os.replace(staged, dest)
    except BaseException:
        Path(staged).unlink(missing_ok=True)
        raise


def plus_is_value(args: list[str], i: int) -> bool:
    """A `+` right after --option (no `=`) is that option's value, unless a patch name follows it."""
    before = args[i - 1] if i > 0 else ""
    after = args[i + 1] if i + 1 < len(args) else None
    return before.startswith("--") and "=" not in before and (after is None or patch_script(after) is None)


def split_steps(args: list[str]) -> list[list[str]]:
    steps, current = [], []
    for i, arg in enumerate(args):
        if arg == "+" and not plus_is_value(args, i):
            steps.append(current)
            current = []
        else:
            current.append(arg)
    steps.append(current)
    return steps


def stray_argument(opts: list[str]) -> str | None:
    """The first argument that is neither an option nor the one value after it. Every patch
    option takes exactly one value (test_conventions checks this), so anything else is a
    file name the patch would write outside the stack."""
    wants_value = False
    for arg in opts:
        if wants_value:
            wants_value = False
        elif arg.startswith("-"):
            wants_value = arg.startswith("--") and "=" not in arg
        else:
            return arg
    return None


def stack(args: list[str]) -> int:
    """op-img <patch> <input> [output] [options] + <patch> [options] + ...

    Each step runs in a temporary directory on the previous step's result, with the
    patch's own default name, so the suffixes accumulate as they would in a manual
    chain. The final image is moved into place only after every step has succeeded:
    to [output] when one is given, otherwise beside the input."""
    steps = split_steps(args)

    for k, step in enumerate(steps, 1):
        if not step:
            print(f"Error: empty step {k} in stack; put a patch name after each '+'", file=sys.stderr)
            return 1
        if patch_script(step[0]) is None:
            return unknown_patch(step[0])

    first = steps[0]
    if len(first) < 2:
        print("Usage: op-img <patch> <input> [output] [options] + <patch> [options] ...", file=sys.stderr)
        return 1
    source, output, first_opts = Path(first[1]), None, first[2:]
    if first_opts and not first_opts[0].startswith("-"):
        output, first_opts = Path(first_opts[0]), first_opts[1:]
    for k, opts in enumerate([first_opts] + [step[1:] for step in steps[1:]], 1):
        stray = stray_argument(opts)
        if stray is not None:
            print(f"Error: step {k} ({steps[k - 1][0]}) got '{stray}' where an option belongs. "
                  "Only the first patch takes files: its input, then an optional output.", file=sys.stderr)
            return 1
    if not source.is_file():
        print(f"Error: file not found: {source}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        current_image = work / source.name
        shutil.copyfile(source, current_image)
        for k, step in enumerate(steps, 1):
            name = step[0]
            opts = first_opts if k == 1 else step[1:]
            last_with_output = k == len(steps) and output is not None
            target = work / "final" / output.name if last_with_output else None
            if target:
                # Keep the output's name so its extension still picks the format.
                target.parent.mkdir()
            argv = [str(current_image)] + ([str(target)] if target else []) + opts
            before = {p.name for p in work.iterdir()}
            result = subprocess.run(command(patch_script(name), argv), capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Error: step {k} ({name}) failed", file=sys.stderr)
                sys.stderr.write(result.stderr)
                return result.returncode
            if target:
                current_image = target
                break
            # The step's output is the one new file in the work directory.
            made = [work / n for n in {p.name for p in work.iterdir()} - before]
            if len(made) != 1:
                what = "wrote no output" if not made else "wrote more than one file"
                print(f"Error: step {k} ({name}) {what}", file=sys.stderr)
                return 1
            current_image.unlink()
            current_image = made[0]

        dest = output if output is not None else source.parent / current_image.name
        try:
            place(current_image, dest)
        except OSError as err:
            print(f"Error: could not write {dest}: {err}", file=sys.stderr)
            return 1
    print(f"Stacked {len(steps)} patches → {dest}", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args or args[0] in ("--help", "-h"):
        return show_help()
    if args[0] == "--list":
        print("Available patches:")
        for p in all_patches():
            print(f"  {p}")
        return 0
    if args[0] == "--info":
        if len(args) < 2:
            print("Usage: op-img --info <patch>", file=sys.stderr)
            return 1
        script = patch_script(args[1])
        if script is None:
            print(f"Error: unknown patch '{args[1]}'", file=sys.stderr)
            return 1
        return run(script, ["--help"])
    if len(split_steps(args)) > 1:
        return stack(args)
    script = patch_script(args[0])
    if script is None:
        return unknown_patch(args[0])
    return run(script, args[1:])


if __name__ == "__main__":
    sys.exit(main())
