# Socrates System Build And Deploy Playbook

## Purpose

This document records the full process used to turn Socrates from a code project into:

- a packaged product
- a bilingual public website
- a deployed production site
- a content-bearing library site
- a scheduled content automation system

The goal is to make this setup reproducible for future projects with minimal rework.

This is the operational playbook for cloning the same pattern again.

## Final Outcome

The finished system includes five layers:

1. Product layer
   - Python SDK and CLI for strategy-first content generation
   - preset-driven workflows
   - multi-stage generation model: frame, outline, draft, review

2. Public website layer
   - static marketing/documentation site
   - English and Simplified Chinese versions
   - SEO-ready metadata, sitemap, canonical links, `hreflang`, Open Graph, structured data

3. Library layer
   - long-form evergreen resource pages
   - bilingual article hubs:
     - `/library/`
     - `/zh/library/`
   - article pages with FAQ schema and article schema

4. Deployment layer
   - Nginx + HTTPS
   - static docroot serving
   - production deployment to a live server without breaking existing sites

5. Automation layer
   - scheduled daily site-content generation
   - separate automation workspace on the server
   - output sync into the live docroot
   - failure-safe behavior when the LLM endpoint is unstable

## Current Live State

At the time of writing, the live system is:

- Domain: `https://ixinxiang.xyz`
- English home: `https://ixinxiang.xyz/`
- Chinese home: `https://ixinxiang.xyz/zh/`
- English library: `https://ixinxiang.xyz/library/`
- Chinese library: `https://ixinxiang.xyz/zh/library/`

Current release version:

- Package version: `0.1.4`
- Git revision used during final rollout: `bcea5be`

## Core Architecture

### 1. Product Architecture

The product follows a strategy-first generation pipeline:

- `ContentRequest`
- `ContentFrame`
- `ContentOutline`
- `ContentDraft`
- `ReviewReport`

Key implementation files:

- [`src/socrates/client.py`](/Users/lu/sugeladi/src/socrates/client.py)
- [`src/socrates/pipeline.py`](/Users/lu/sugeladi/src/socrates/pipeline.py)
- [`src/socrates/models.py`](/Users/lu/sugeladi/src/socrates/models.py)
- [`src/socrates/presets.py`](/Users/lu/sugeladi/src/socrates/presets.py)
- [`src/socrates/router.py`](/Users/lu/sugeladi/src/socrates/router.py)
- [`src/socrates/cli.py`](/Users/lu/sugeladi/src/socrates/cli.py)

### 2. Website Architecture

The public site is a static site under [`site/`](/Users/lu/sugeladi/site).

Main pages:

- [`site/index.html`](/Users/lu/sugeladi/site/index.html)
- [`site/product.html`](/Users/lu/sugeladi/site/product.html)
- [`site/use-cases.html`](/Users/lu/sugeladi/site/use-cases.html)
- [`site/docs.html`](/Users/lu/sugeladi/site/docs.html)
- [`site/faq.html`](/Users/lu/sugeladi/site/faq.html)

Chinese pages:

- [`site/zh/index.html`](/Users/lu/sugeladi/site/zh/index.html)
- [`site/zh/product.html`](/Users/lu/sugeladi/site/zh/product.html)
- [`site/zh/use-cases.html`](/Users/lu/sugeladi/site/zh/use-cases.html)
- [`site/zh/docs.html`](/Users/lu/sugeladi/site/zh/docs.html)
- [`site/zh/faq.html`](/Users/lu/sugeladi/site/zh/faq.html)

Shared assets:

- [`site/styles.css`](/Users/lu/sugeladi/site/styles.css)
- [`site/app.js`](/Users/lu/sugeladi/site/app.js)
- [`site/robots.txt`](/Users/lu/sugeladi/site/robots.txt)
- [`site/sitemap.xml`](/Users/lu/sugeladi/site/sitemap.xml)
- [`site/manifest.webmanifest`](/Users/lu/sugeladi/site/manifest.webmanifest)

### 3. Site Automation Architecture

The evergreen content system is implemented in:

- [`src/socrates/site_automation.py`](/Users/lu/sugeladi/src/socrates/site_automation.py)

It provides:

- topic inventory generation
- deterministic topic selection
- structured article generation
- local validation against spammy/thin content
- review gating
- static HTML rendering
- bilingual library index rendering
- sitemap rebuilding
- persistent state management

The CLI entry point is:

- `socrates site-generate`

## What Was Built, In Order

### Phase 1. Productization

The first step was turning the idea into a coherent software product.

Work included:

- defining the typed generation model
- exposing a usable SDK surface
- building a CLI
- adding presets for common workflows
- making routing depend on content complexity

Important additions:

- `socrates presets`
- `socrates template`
- guided and full generation paths

### Phase 2. Public Website

The next step was creating a serious public-facing site instead of a demo page.

Requirements:

- explain the product clearly
- support product positioning
- document the CLI and SDK
- present use cases
- be ready for public search traffic

This produced a multi-page static site with:

- product page
- documentation page
- use-case page
- FAQ
- structured homepage

### Phase 3. Production Deployment

The site was then deployed to a server without interfering with other programs already running on that host.

Key choices:

- do not replace the server’s global setup
- do not disturb unrelated sites
- deploy into the existing static site docroot for this domain only
- preserve HTTPS and redirect behavior

Live production docroot:

- `/www/wwwroot/ixinxiang.xyz`

Active Nginx vhost:

- `/www/server/panel/vhost/nginx/ixinxiang.xyz.conf`

### Phase 4. Multilingual Expansion

After the English site worked, the site was expanded to Chinese.

This included:

- Chinese versions of all core pages
- navigation parity
- metadata parity
- alternate language discovery through `hreflang`
- Chinese messaging adapted to the product’s positioning

### Phase 5. Library And Evergreen Content

The next step was to make the site useful as a content property, not just a product landing site.

This added:

- `/library/`
- `/zh/library/`
- seeded evergreen pages
- article rendering pipeline
- article metadata and FAQ schema
- sitemap inclusion

Initial seeded pages:

- `content brief` guide
- `content frame` guide

### Phase 6. Automated Content Publishing

The final major step was adding a daily content generation mechanism for search growth and long-tail traffic capture.

This system:

- selects the next unpublished topics
- generates pages in English and Chinese
- runs validation and review gates
- writes static pages
- rebuilds library indexes
- rebuilds sitemap
- syncs output into the live site

## Routing And Content Strategy

Not all content should use the same generation depth.

The operating model is:

- Level 1: direct generation
  - summaries
  - rewrites
  - headlines
  - lightweight utility tasks

- Level 2: frame + draft
  - normal blog posts
  - value props
  - structured platform content

- Level 3: frame + outline + draft + review
  - flagship pieces
  - strategic content
  - evergreen content library pages
  - brand and industry content

The site automation system uses guarded multi-stage generation because these pages are public, indexable, and long-lived.

## SEO Decisions

SEO work was built into the site rather than added later.

Implemented items:

- canonical tags
- `hreflang`
- `x-default`
- `robots.txt`
- XML sitemap
- Open Graph tags
- Twitter card tags
- FAQ schema
- article schema
- bilingual page discovery

Important SEO files:

- [`site/robots.txt`](/Users/lu/sugeladi/site/robots.txt)
- [`site/sitemap.xml`](/Users/lu/sugeladi/site/sitemap.xml)
- [`site/library/index.html`](/Users/lu/sugeladi/site/library/index.html)
- [`site/zh/library/index.html`](/Users/lu/sugeladi/site/zh/library/index.html)

## Content Quality Controls

The automation system was intentionally designed not to behave like a spam page generator.

Built-in controls include:

- no fabricated stats
- no fake case studies
- no competitor attack copy
- no medical, legal, or financial claims
- no obvious clickbait phrases
- keyword stuffing checks
- duplicate heading checks
- meta description length checks
- publishability review gating

This is important because the goal is long-term search value, not low-quality page explosion.

## Current File Map For Replication

### Product And CLI

- [`src/socrates/cli.py`](/Users/lu/sugeladi/src/socrates/cli.py)
- [`src/socrates/client.py`](/Users/lu/sugeladi/src/socrates/client.py)
- [`src/socrates/config.py`](/Users/lu/sugeladi/src/socrates/config.py)
- [`src/socrates/providers/openai_compatible.py`](/Users/lu/sugeladi/src/socrates/providers/openai_compatible.py)
- [`src/socrates/site_automation.py`](/Users/lu/sugeladi/src/socrates/site_automation.py)

### Site

- [`site/`](/Users/lu/sugeladi/site)
- [`site/library/`](/Users/lu/sugeladi/site/library)
- [`site/zh/library/`](/Users/lu/sugeladi/site/zh/library)

### Automation State

- [`content/site_automation_state.json`](/Users/lu/sugeladi/content/site_automation_state.json)

### Deployment Scripts

- [`scripts/deploy_site.sh`](/Users/lu/sugeladi/scripts/deploy_site.sh)
- [`scripts/run_daily_site_automation.sh`](/Users/lu/sugeladi/scripts/run_daily_site_automation.sh)
- [`scripts/install_daily_content_cron.sh`](/Users/lu/sugeladi/scripts/install_daily_content_cron.sh)

### Tests

- [`tests/test_cli.py`](/Users/lu/sugeladi/tests/test_cli.py)
- [`tests/test_site_automation.py`](/Users/lu/sugeladi/tests/test_site_automation.py)
- [`tests/test_openai_compatible.py`](/Users/lu/sugeladi/tests/test_openai_compatible.py)

## Production Deployment Topology

### Live Site

- Domain: `ixinxiang.xyz`
- Docroot: `/www/wwwroot/ixinxiang.xyz`
- Nginx config: `/www/server/panel/vhost/nginx/ixinxiang.xyz.conf`

### Automation Workspace

- Repo: `/opt/socrates-site-automation/repo`
- Generated output: `/opt/socrates-site-automation/output/site`
- State file: `/opt/socrates-site-automation/state/site_automation_state.json`
- Cron file: `/etc/cron.d/socrates-site-automation`
- Log file: `/var/log/socrates-site-automation.log`

### Runtime Notes

- Python runtime used for automation: `python3.11`
- The public site is served from the docroot
- The automation job does not write directly into the tracked source tree
- Instead, it builds into an output directory and then syncs into the docroot

This separation matters because it avoids mixing daily generated pages with the repo working tree on the server.

## Reproducible Build Process

This is the recommended order for cloning the same pattern into a new project.

### Step 1. Build The Product Core

1. Define the typed models for request, frame, outline, draft, and review.
2. Build the provider abstraction.
3. Build the client wrapper.
4. Build a CLI that matches the real workflow.
5. Add presets for real content tasks.

### Step 2. Build The Static Site

1. Create a homepage that explains the product clearly.
2. Add product, docs, use-cases, and FAQ pages.
3. Create a shared CSS system.
4. Add structured metadata.
5. Add navigation and footer structure that can scale later.

### Step 3. Add Multilingual Support

1. Create localized copies of the core pages.
2. Add `hreflang` links on every relevant page.
3. Make sure navigation and footer links match across locales.
4. Add localized metadata, not just translated body copy.

### Step 4. Add Evergreen Library Support

1. Create library hub pages.
2. Create an article template renderer.
3. Add article schema and FAQ schema.
4. Add bilingual article paths.
5. Add sitemap support for generated pages.

### Step 5. Add Content Automation

1. Build a topic inventory.
2. Add persistent state to avoid republishing the same topics.
3. Add local validation.
4. Add model review gating.
5. Generate into a separate publish directory.
6. Rebuild indexes and sitemap.

### Step 6. Deploy Safely

1. Confirm the live docroot and active Nginx site.
2. Do not disturb other vhosts or services.
3. Sync the static site into the docroot.
4. Install a separate automation workspace under `/opt/...`.
5. Keep secrets out of Git.
6. Install cron.

## Exact Commands Used In Practice

### Local Validation

```bash
uv run ruff check .
uv run pytest
uv run mypy src
```

### Local Site Generation

```bash
uv run socrates site-generate \
  --publish-dir site \
  --state-file content/site_automation_state.json \
  --topics-per-run 2 \
  --locales en-US,zh-CN
```

### Server Runtime Pattern

The automation runner is:

```bash
/opt/socrates-site-automation/repo/scripts/run_daily_site_automation.sh
```

It performs:

1. best-effort `git pull --ff-only`
2. venv bootstrap if missing
3. package install
4. sync of base static site into output dir
5. sync of seeded library pages
6. execution of `socrates site-generate`
7. rsync into the live docroot

## Secret Management Rules

Never commit secrets into Git.

This includes:

- API keys
- server passwords
- provider credentials
- deployment-only tokens

The correct place for provider config is:

- `/opt/socrates-site-automation/repo/.socrates/config.toml`

Use placeholders in templates:

```toml
[provider]
kind = "openai-compatible"
base_url = "https://your-provider.example/v1"
api_key = "<YOUR_API_KEY>"

[models]
default_model = "auto"
temperature = 0.2

[generation]
fallback_to_prompt_json = true
timeout_seconds = 120.0
max_retries = 3
retry_backoff_seconds = 2.0
```

## Automation Reliability Notes

The current system is safe, but the LLM endpoint is not perfectly stable.

Observed behavior:

- the endpoint can be slow
- it can return `504`
- some runs skip topics instead of publishing them

The system was hardened to handle this safely:

- retries added to the provider adapter
- provider errors do not corrupt the site
- failed topics are skipped
- existing live pages remain intact
- cron can continue using the current checkout even if `git pull` fails

This means the site remains available even when generation is unreliable.

## Why The Server Layout Matters

The biggest operational lesson is this:

Do not run daily generation directly inside the live docroot and do not mutate the tracked repo in place.

Correct layout:

- Git repo in one place
- generated output in another place
- live docroot in another place
- secrets outside Git
- cron running from the repo but publishing through output sync

This avoids:

- Git conflicts
- accidental deletion of tracked assets
- unstable deploy state
- mixing generated content with code changes

## Recommended Template For Future Projects

For the next project, use this structure from day one:

```text
project-root/
  src/
  site/
  content/
  scripts/
  tests/
  SYSTEM_BUILD_AND_DEPLOY_PLAYBOOK.md
```

Server structure:

```text
/opt/<project>-automation/repo
/opt/<project>-automation/output/site
/opt/<project>-automation/state
/www/wwwroot/<domain>
/etc/cron.d/<project>-automation
```

## Suggested Replication Checklist

### Product Checklist

- typed models exist
- provider abstraction exists
- CLI exists
- presets exist
- review stage exists

### Website Checklist

- homepage exists
- product/docs/faq/use-cases pages exist
- bilingual pages exist
- sitemap exists
- robots exists

### Library Checklist

- article renderer exists
- article hub exists
- structured data exists
- seeded pages exist
- nav links to library exist

### Deployment Checklist

- domain resolves
- HTTPS works
- docroot confirmed
- Nginx vhost confirmed
- no unrelated site impacted

### Automation Checklist

- separate server workspace exists
- secrets are externalized
- cron installed
- logs available
- dry run tested

## Known Caveats

1. The content automation is deployment-safe, but LLM reliability still affects throughput.
2. The current server needed `python3.11` installed because the project requires Python `>=3.11`.
3. The server’s GitHub connectivity can be slow, so the automation runner is tolerant of `git pull` failure.
4. The server repo will show `.socrates/` as untracked by design because secrets are intentionally kept out of Git.

## Recommended Next Improvements

If this is turned into a reusable system template, the next improvements should be:

1. Add a bootstrap script that provisions server directories, Python, config, cron, and initial sync in one command.
2. Add a `.socrates/config.example.toml` template for safer onboarding.
3. Add a release script that bumps version, runs checks, commits, pushes, and optionally deploys.
4. Add a content quality dashboard that reports:
   - published topic count
   - skipped topic count
   - provider failures
   - sitemap size
   - last successful generation time
5. Add a stronger topic planning layer for better topical coverage over time.
6. Add optional manual approval for high-value generated pages before public publishing.

## Short Summary

This project was built in four real layers:

- product
- website
- deployment
- content automation

The key reason it is now reusable is not just that the code works.

It is reusable because the process has been separated into:

- product logic
- static presentation
- SEO structure
- content system
- deployment topology
- automation operations

That separation is what makes it possible to copy the pattern quickly for the next project.
