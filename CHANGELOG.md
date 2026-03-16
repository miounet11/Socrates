# Changelog

## 0.1.3 - 2026-03-16

- Added built-in content presets and starter request generation through `socrates presets` and `socrates template`.
- Updated auto-routing to honor preset metadata before fallback content-type rules.
- Expanded the public site into a multi-page product website with product, use-case, docs, and FAQ pages.
- Improved site SEO with stronger metadata, richer internal linking, and an expanded sitemap.
- Corrected public installation guidance to use the GitHub install path and renamed the Python distribution to avoid a PyPI name collision.

## 0.1.2 - 2026-03-16

- Aligned packaged versioning with the published website deployment release.
- Rebuilt release assets so GitHub release artifacts match the tagged version.

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
