"""CI conventions."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_fails_when_lint_changes_a_file() -> None:
    # Lint fixes in place and exits 0, so CI needs the step after it that fails on any change.
    steps = (ROOT / ".github/workflows/test.yml").read_text().split("\n      - name: ")
    lint = next(i for i, step in enumerate(steps) if "run: uv run python scripts/lint.py" in step)
    assert steps[lint + 1].startswith("Check lint changed nothing")
    assert "git diff --exit-code" in steps[lint + 1]


def test_the_pre_commit_hook_commits_what_lint_fixed() -> None:
    assert "stage_fixed: true" in (ROOT / "lefthook.yml").read_text()
