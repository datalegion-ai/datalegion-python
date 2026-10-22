# Contributing

Thank you for your interest in contributing to the Data Legion Python SDK.

## Getting Started

1. Fork the repository
2. Clone your fork and create a new branch
3. Install dependencies: `uv sync --dev`
4. Make your changes

## Development

```bash
uv sync --dev        # Install dependencies
uv run lefthook install  # Arm the git hooks (pre-commit lint)
uv run python scripts/lint.py          # Run linter
uv build             # Build the project
uv run pytest tests/ # Run tests (requires DATALEGION_API_KEY)
```

## Pull Requests

- Keep changes focused and scoped to a single feature or fix
- Ensure linting and build pass before submitting
- Write a clear PR description explaining the change and motivation

## Code Style

- Follow existing patterns in the codebase
- Minimal dependencies — httpx and pydantic only

## Reporting Issues

Use the [issue templates](https://github.com/datalegion-ai/datalegion-python/issues/new/choose) to report bugs or request features.

## Security

Please see [SECURITY.md](SECURITY.md) for reporting vulnerabilities.
