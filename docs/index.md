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

Useful CLI entrypoints:

- `socrates presets`
- `socrates template PRESET --output request.yaml`
- `socrates frame request.yaml --json`
- `socrates generate request.yaml --mode guided`
- `socrates review draft.md --request request.yaml`

Generation modes:

- `direct`: fast transforms and lightweight content jobs
- `guided`: frame + draft for standard publishable work
- `full`: frame + outline + draft + review for high-value content

Built-in presets:

- `blog_post`
- `linkedin_long_post`
- `value_prop`
- `industry_analysis`
- `content_calendar`
- `brand_narrative`

See [architecture.md](architecture.md) for the implementation shape.
