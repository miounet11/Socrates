# Changelog

## 0.1.1 - 2026-03-16

- Added a static SEO-focused product site in `site/`.
- Added an Nginx server block template for `ixinxiang.xyz` on port `8088`.
- Added `scripts/deploy_site.sh` for static site sync and Nginx reload on a target host.

## 0.1.0 - 2026-03-16

- Initial public release.
- Added typed Python SDK for rubric-guided content generation.
- Added `direct`, `guided`, and `full` generation modes.
- Added OpenAI-compatible chat-completions provider.
- Added Typer CLI with `init`, `frame`, `generate`, `review`, and `doctor`.
- Added examples, tests, docs, CI, and release workflows.
