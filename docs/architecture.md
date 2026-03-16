# Architecture

## Pipeline

Socrates uses four content objects:

- `ContentFrame`
- `ContentOutline`
- `ContentDraft`
- `ReviewReport`

Execution flow:

1. Parse a `ContentRequest`.
2. Resolve mode from the explicit argument or the `content_type`.
3. Generate the necessary upstream artifacts.
4. Return a `ContentResult`.

## Provider boundary

The provider surface is intentionally small:

- `structured_completion(messages, response_model, model, temperature)`

This keeps the pipeline independent from provider-specific SDKs while still supporting typed outputs.

## Review strategy

The review stage is hybrid:

- model-generated review for editorial judgment
- local heuristics for stock AI phrasing, repeated paragraphs, and inflated claims

The two reports are merged into the final `ReviewReport`.

