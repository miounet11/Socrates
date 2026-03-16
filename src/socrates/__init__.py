"""Public package surface for Socrates."""

from socrates.client import Socrates
from socrates.config import SocratesConfig, load_config
from socrates.models import (
    ContentDraft,
    ContentFrame,
    ContentOutline,
    ContentRequest,
    ContentResult,
    GenerationMode,
    ReviewFinding,
    ReviewReport,
)

__all__ = [
    "ContentDraft",
    "ContentFrame",
    "ContentOutline",
    "ContentRequest",
    "ContentResult",
    "GenerationMode",
    "ReviewFinding",
    "ReviewReport",
    "Socrates",
    "SocratesConfig",
    "load_config",
]

