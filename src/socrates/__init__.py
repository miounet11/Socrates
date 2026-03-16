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
from socrates.presets import PresetSpec, build_request_from_preset, list_presets

__all__ = [
    "ContentDraft",
    "ContentFrame",
    "ContentOutline",
    "ContentRequest",
    "ContentResult",
    "GenerationMode",
    "PresetSpec",
    "ReviewFinding",
    "ReviewReport",
    "Socrates",
    "SocratesConfig",
    "build_request_from_preset",
    "list_presets",
    "load_config",
]
