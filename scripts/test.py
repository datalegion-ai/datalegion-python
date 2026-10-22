"""Test runner for the Data Legion Python SDK."""

import subprocess
import sys


def main() -> None:
    """Run pytest with any extra arguments passed through."""
    cmd = ["pytest", "tests/", "-v", *sys.argv[1:]]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
