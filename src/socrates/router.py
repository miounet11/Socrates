"""Mode routing for content jobs."""

from __future__ import annotations

from socrates.models import ContentRequest, GenerationMode
from socrates.presets import find_preset

DIRECT_TYPES = {
    "summary",
    "rewrite",
    "title_variants",
    "translation",
    "hashtags",
    "cta",
    "bullets",
    "json_cleanup",
}

GUIDED_TYPES = {
    "blog_post",
    "linkedin_long_post",
    "value_prop",
    "landing_page_section",
    "sales_email",
}

FULL_TYPES = {
    "brand_narrative",
    "industry_analysis",
    "content_calendar",
    "flagship_article",
    "content_series",
    "homepage_core_copy",
}


def resolve_mode(
    request: ContentRequest,
    requested_mode: GenerationMode | str = GenerationMode.AUTO,
) -> GenerationMode:
    """Resolve auto-routing into an executable mode."""

    mode = GenerationMode(requested_mode)
    if mode is not GenerationMode.AUTO:
        return mode

    content_type = request.content_type.strip().lower().replace("-", "_")
    preset = find_preset(content_type)
    if preset is not None:
        return preset.recommended_mode
    if content_type in DIRECT_TYPES:
        return GenerationMode.DIRECT
    if content_type in FULL_TYPES:
        return GenerationMode.FULL
    if content_type in GUIDED_TYPES:
        return GenerationMode.GUIDED
    return GenerationMode.GUIDED
