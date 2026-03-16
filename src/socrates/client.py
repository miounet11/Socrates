"""Public SDK surface."""

from __future__ import annotations

from pathlib import Path

from socrates.config import SocratesConfig, load_config
from socrates.models import (
    ContentDraft,
    ContentFrame,
    ContentOutline,
    ContentRequest,
    ContentResult,
    GenerationMode,
    ReviewReport,
)
from socrates.pipeline import generate_draft, generate_frame, generate_outline, generate_review
from socrates.providers import build_provider
from socrates.providers.base import LLMProvider
from socrates.router import resolve_mode


class Socrates:
    """Rubric-guided content generation client."""

    def __init__(self, provider: LLMProvider, *, config: SocratesConfig | None = None) -> None:
        self.provider = provider
        self.config = config or SocratesConfig()

    @classmethod
    def from_config(
        cls,
        config: SocratesConfig | None = None,
        *,
        start_path: Path | None = None,
    ) -> Socrates:
        loaded = config or load_config(start_path)
        provider = build_provider(loaded)
        return cls(provider, config=loaded)

    def frame(self, request: ContentRequest) -> ContentFrame:
        return generate_frame(
            self.provider,
            request,
            model=self.config.models.resolve("frame"),
            temperature=self.config.models.temperature,
        )

    def outline(self, request: ContentRequest, frame: ContentFrame) -> ContentOutline:
        return generate_outline(
            self.provider,
            request,
            frame,
            model=self.config.models.resolve("outline"),
            temperature=self.config.models.temperature,
        )

    def draft(
        self,
        request: ContentRequest,
        frame: ContentFrame | None = None,
        outline: ContentOutline | None = None,
    ) -> ContentDraft:
        return generate_draft(
            self.provider,
            request,
            model=self.config.models.resolve("draft"),
            temperature=self.config.models.temperature,
            frame=frame,
            outline=outline,
            direct=frame is None and outline is None,
        )

    def review(
        self,
        request: ContentRequest,
        draft: ContentDraft,
        frame: ContentFrame | None = None,
    ) -> ReviewReport:
        return generate_review(
            self.provider,
            request,
            draft,
            model=self.config.models.resolve("review"),
            temperature=self.config.models.temperature,
            frame=frame,
        )

    def generate(
        self,
        request: ContentRequest,
        mode: GenerationMode | str = GenerationMode.AUTO,
    ) -> ContentResult:
        resolved_mode = resolve_mode(request, mode)
        frame: ContentFrame | None = None
        outline: ContentOutline | None = None
        review: ReviewReport | None = None

        if resolved_mode is GenerationMode.DIRECT:
            draft = self.draft(request)
        elif resolved_mode is GenerationMode.GUIDED:
            frame = self.frame(request)
            draft = self.draft(request, frame=frame)
        else:
            frame = self.frame(request)
            outline = self.outline(request, frame)
            draft = self.draft(request, frame=frame, outline=outline)
            review = self.review(request, draft, frame=frame)

        return ContentResult(
            request=request,
            mode=resolved_mode,
            frame=frame,
            outline=outline,
            draft=draft,
            review=review,
        )
