# Contributing

## Development setup

```bash
uv sync --extra dev
```

## Checks

```bash
uv run ruff check .
uv run mypy src
uv run pytest
uv build
```

## Guidelines

- Keep the public API typed and stable.
- Prefer behavior-level docs and tests over prompt dumps.
- Do not add provider-specific logic outside `src/socrates/providers/`.
- Keep prompts concrete and audience-specific; avoid generic “helpful assistant” wording.

## Pull requests

- Include tests for user-visible behavior.
- Update README or docs when public workflows change.
- Keep PRs small enough to review.

