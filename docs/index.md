# Socrates Docs

Socrates is a structured generation layer for content systems.

Core idea:

1. Build a rubric before drafting.
2. Add structure before prose when the task deserves it.
3. Review for publishability before shipping.

The public entrypoints are:

- `Socrates.generate`
- `Socrates.frame`
- `Socrates.outline`
- `Socrates.draft`
- `Socrates.review`

Generation modes:

- `direct`: fast transforms and lightweight content jobs
- `guided`: frame + draft for standard publishable work
- `full`: frame + outline + draft + review for high-value content

See [architecture.md](architecture.md) for the implementation shape.

