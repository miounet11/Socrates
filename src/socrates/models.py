"""Typed request and response objects used by the generation pipeline."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GenerationMode(StrEnum):
    AUTO = "auto"
    DIRECT = "direct"
    GUIDED = "guided"
    FULL = "full"


class ReviewSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ContentRequest(BaseModel):
    """Input contract for any Socrates content job."""

    model_config = ConfigDict(extra="forbid")

    topic: str
    audience: str
    goal: str
    platform: str = "blog"
    content_type: str = "blog_post"
    constraints: list[str] = Field(default_factory=list)
    voice_notes: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    source_material: list[str] = Field(default_factory=list)
    length_hint: str | None = None
    locale: str = "en-US"
    include_cta: bool = True
    cta_goal: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("topic", "audience", "goal", "platform", "content_type", "locale")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("constraints", "voice_notes", "keywords", "source_material")
    @classmethod
    def validate_string_lists(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        return cleaned


class ContentFrame(BaseModel):
    """Stage-1 rubric for the requested content."""

    model_config = ConfigDict(extra="forbid")

    audience_pains: list[str] = Field(min_length=1)
    desired_takeaway: str
    persuasion_triggers: list[str] = Field(min_length=1)
    credibility_requirements: list[str] = Field(min_length=1)
    tone_rules: list[str] = Field(min_length=1)
    anti_patterns: list[str] = Field(min_length=1)
    core_angle: str


class OutlineSection(BaseModel):
    """Section-level execution note for stage 2."""

    model_config = ConfigDict(extra="forbid")

    heading: str
    purpose: str
    key_points: list[str] = Field(min_length=1)
    evidence_needs: list[str] = Field(default_factory=list)
    cta_hint: str | None = None


class ContentOutline(BaseModel):
    """Structured outline for longer publishable content."""

    model_config = ConfigDict(extra="forbid")

    opening_hook: str
    thesis: str
    sections: list[OutlineSection] = Field(min_length=1)
    closing_cta: str | None = None
    platform_adaptations: list[str] = Field(default_factory=list)


class ContentDraft(BaseModel):
    """Final outward-facing draft."""

    model_config = ConfigDict(extra="forbid")

    title: str
    body: str
    summary: str | None = None
    cta: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewFinding(BaseModel):
    """An actionable editorial issue or approval note."""

    model_config = ConfigDict(extra="forbid")

    severity: ReviewSeverity
    category: str
    evidence: str
    recommendation: str


class ReviewReport(BaseModel):
    """Review stage output."""

    model_config = ConfigDict(extra="forbid")

    publishability_score: int = Field(ge=0, le=100)
    summary: str
    findings: list[ReviewFinding] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    repetition_flags: list[str] = Field(default_factory=list)
    ai_tone_flags: list[str] = Field(default_factory=list)
    passes: bool


class ContentResult(BaseModel):
    """Result returned by `Socrates.generate`."""

    model_config = ConfigDict(extra="forbid")

    request: ContentRequest
    mode: GenerationMode
    frame: ContentFrame | None = None
    outline: ContentOutline | None = None
    draft: ContentDraft
    review: ReviewReport | None = None

