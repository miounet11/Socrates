from socrates.models import ContentRequest, GenerationMode
from socrates.router import resolve_mode


def test_resolve_mode_auto_direct() -> None:
    request = ContentRequest(
        topic="Summarize this memo",
        audience="Internal team",
        goal="Summarize a text",
        platform="internal",
        content_type="summary",
    )
    assert resolve_mode(request) == GenerationMode.DIRECT


def test_resolve_mode_auto_full() -> None:
    request = ContentRequest(
        topic="Plan a 30-day content calendar",
        audience="CMOs at SaaS companies",
        goal="Create a content series",
        platform="multi-platform",
        content_type="content_calendar",
    )
    assert resolve_mode(request) == GenerationMode.FULL


def test_resolve_mode_explicit_wins(content_request: ContentRequest) -> None:
    assert resolve_mode(content_request, GenerationMode.FULL) == GenerationMode.FULL
