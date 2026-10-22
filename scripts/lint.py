"""Lint script for the Data Legion Python SDK."""

import subprocess
import sys


def _run(cmd: list[str], *, fatal: bool = True) -> bool:
    print(f"\n{'=' * 60}")
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)
    result = subprocess.run(cmd)
    if result.returncode != 0:
        if fatal:
            print(f"FAILED: {' '.join(cmd)}")
            sys.exit(1)
        else:
            print(f"WARNING: {' '.join(cmd)} (non-fatal)")
            return False
    return True


def main() -> None:
    """Run all linting checks."""
    # Format
    _run(["ruff", "format", "src/", "tests/", "scripts/"])

    # Lint with auto-fix
    _run(["ruff", "check", "--fix", "src/", "tests/", "scripts/"])

    # Format markdown
    _run(
        ["mdformat", "--wrap", "no", "README.md"],
        fatal=False,
    )

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()


# Run with: uv run python scripts/lint.py
