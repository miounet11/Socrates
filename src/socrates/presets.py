"""Built-in preset metadata and starter request generation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from socrates.models import ContentRequest, GenerationMode


class PresetSpec(BaseModel):
    """A built-in content preset exposed to users."""

    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    summary: str
    platform: str
    content_type: str
    recommended_mode: GenerationMode
    default_length_hint: str
    sample_topic: str
    sample_audience: str
    sample_goal: str
    starter_constraints: list[str] = Field(default_factory=list)
    starter_voice_notes: list[str] = Field(default_factory=list)
    starter_keywords: list[str] = Field(default_factory=list)


PRESETS: dict[str, PresetSpec] = {
    "blog_post": PresetSpec(
        key="blog_post",
        label="B2B Blog Post",
        summary="Structured long-form articles with a differentiated thesis and clear CTA.",
        platform="blog",
        content_type="blog_post",
        recommended_mode=GenerationMode.GUIDED,
        default_length_hint="1200-1600 words",
        sample_topic="Why AI onboarding copy underperforms even when the product is strong",
        sample_audience="B2B SaaS product marketers",
        sample_goal="Generate a publishable blog draft with a clear point of view",
        starter_constraints=[
            "Avoid generic thought leadership phrasing",
            "Use concrete examples and buyer-language",
        ],
        starter_voice_notes=["Specific", "Credible", "Sharp"],
        starter_keywords=["B2B SaaS", "messaging", "onboarding"],
    ),
    "linkedin_long_post": PresetSpec(
        key="linkedin_long_post",
        label="LinkedIn Long Post",
        summary="Operator-style posts with tight pacing, strong hooks, and audience-aware CTAs.",
        platform="linkedin",
        content_type="linkedin_long_post",
        recommended_mode=GenerationMode.GUIDED,
        default_length_hint="700-900 words",
        sample_topic=(
            "Most AI positioning fails because it explains capability "
            "before business friction"
        ),
        sample_audience="Founders and GTM leaders at AI startups",
        sample_goal="Generate a publishable LinkedIn post with a strong opening and crisp close",
        starter_constraints=[
            "Keep paragraphs short",
            "Lead with a concrete hook, not a generic statement",
        ],
        starter_voice_notes=["Operator tone", "Clear point of view"],
        starter_keywords=["AI positioning", "go-to-market", "LinkedIn"],
    ),
    "value_prop": PresetSpec(
        key="value_prop",
        label="Value Proposition",
        summary="Landing-page copy that translates product capability into buyer-relevant value.",
        platform="web",
        content_type="value_prop",
        recommended_mode=GenerationMode.GUIDED,
        default_length_hint="Short landing page section",
        sample_topic="A workflow copilot for RevOps teams",
        sample_audience="Revenue operations leaders evaluating automation platforms",
        sample_goal=(
            "Generate landing-page value proposition copy that could ship "
            "with minimal edits"
        ),
        starter_constraints=[
            "Avoid empty efficiency claims",
            "Prioritize buyer pain and credibility signals",
        ],
        starter_voice_notes=["Confident", "Buyer-aware"],
        starter_keywords=["RevOps", "workflow copilot", "landing page"],
    ),
    "industry_analysis": PresetSpec(
        key="industry_analysis",
        label="Industry Analysis",
        summary="Deeper market or category analysis with stronger structure and review coverage.",
        platform="blog",
        content_type="industry_analysis",
        recommended_mode=GenerationMode.FULL,
        default_length_hint="1800-2500 words",
        sample_topic="What buyers actually expect from AI workflow products in 2026",
        sample_audience="Product marketers and founders in B2B AI software",
        sample_goal=(
            "Generate a publishable analysis with differentiated conclusions "
            "and a credible tone"
        ),
        starter_constraints=[
            "Avoid inflated certainty",
            "Map claims to the type of evidence they would require",
        ],
        starter_voice_notes=["Analytical", "Measured", "Specific"],
        starter_keywords=["industry analysis", "AI software", "buyer expectations"],
    ),
    "content_calendar": PresetSpec(
        key="content_calendar",
        label="Content Calendar",
        summary=(
            "Multi-post planning for professional content programs, not "
            "isolated one-off drafts."
        ),
        platform="multi-platform",
        content_type="content_calendar",
        recommended_mode=GenerationMode.FULL,
        default_length_hint="30 entries",
        sample_topic="A 30-day content calendar for a compliance automation platform",
        sample_audience="Security and compliance leaders at mid-market companies",
        sample_goal="Generate a differentiated content calendar across blog, LinkedIn, and email",
        starter_constraints=[
            "Avoid repeated angles across the series",
            "Balance educational and commercial intent",
        ],
        starter_voice_notes=["Expert", "Practical"],
        starter_keywords=["content calendar", "compliance automation", "editorial planning"],
    ),
    "brand_narrative": PresetSpec(
        key="brand_narrative",
        label="Brand Narrative",
        summary=(
            "High-stakes positioning and point-of-view content where "
            "structure and differentiation matter most."
        ),
        platform="web",
        content_type="brand_narrative",
        recommended_mode=GenerationMode.FULL,
        default_length_hint="900-1400 words",
        sample_topic=(
            "Why workflow software should feel like decision support, not "
            "dashboard sprawl"
        ),
        sample_audience="Operators evaluating modern workflow products",
        sample_goal="Generate a clear brand narrative with a distinct thesis and controlled tone",
        starter_constraints=[
            "Avoid inspirational cliches",
            "Make the core angle unmistakably differentiated",
        ],
        starter_voice_notes=["Intentional", "Strategic", "Direct"],
        starter_keywords=["brand narrative", "positioning", "messaging"],
    ),
}


def list_presets() -> list[PresetSpec]:
    """Return all presets in stable display order."""

    return [PRESETS[key] for key in sorted(PRESETS)]


def get_preset(name: str) -> PresetSpec:
    """Return a preset or raise `KeyError`."""

    normalized = name.strip().lower().replace("-", "_")
    return PRESETS[normalized]


def find_preset(name: str) -> PresetSpec | None:
    """Return a preset if it exists."""

    normalized = name.strip().lower().replace("-", "_")
    return PRESETS.get(normalized)


def build_request_from_preset(
    name: str,
    *,
    topic: str | None = None,
    audience: str | None = None,
    goal: str | None = None,
) -> ContentRequest:
    """Generate a starter request object from a built-in preset."""

    preset = get_preset(name)
    return ContentRequest(
        topic=topic or preset.sample_topic,
        audience=audience or preset.sample_audience,
        goal=goal or preset.sample_goal,
        platform=preset.platform,
        content_type=preset.content_type,
        constraints=preset.starter_constraints,
        voice_notes=preset.starter_voice_notes,
        keywords=preset.starter_keywords,
        length_hint=preset.default_length_hint,
        include_cta=True,
        cta_goal="Drive the next meaningful step for the reader",
    )
