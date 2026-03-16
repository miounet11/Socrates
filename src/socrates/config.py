"""Config loading and default project bootstrap helpers."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from socrates.exceptions import ConfigurationError

DEFAULT_CONFIG_PATH = Path(".socrates/config.toml")


class ProviderSettings(BaseModel):
    """Provider-level config."""

    model_config = ConfigDict(extra="forbid")

    kind: str = "openai-compatible"
    api_key: str | None = None
    base_url: str = "https://api.openai.com/v1"


class ModelSettings(BaseModel):
    """Stage model mapping."""

    model_config = ConfigDict(extra="forbid")

    default_model: str = "gpt-4.1-mini"
    frame_model: str | None = None
    outline_model: str | None = None
    draft_model: str | None = None
    review_model: str | None = None
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)

    def resolve(self, stage: str) -> str:
        return getattr(self, f"{stage}_model") or self.default_model


class GenerationSettings(BaseModel):
    """Runtime generation controls."""

    model_config = ConfigDict(extra="forbid")

    fallback_to_prompt_json: bool = True
    timeout_seconds: float = Field(default=60.0, gt=0.0)


class SocratesConfig(BaseModel):
    """Top-level config object."""

    model_config = ConfigDict(extra="forbid")

    provider: ProviderSettings = Field(default_factory=ProviderSettings)
    models: ModelSettings = Field(default_factory=ModelSettings)
    generation: GenerationSettings = Field(default_factory=GenerationSettings)


def _search_config_path(start: Path) -> Path | None:
    for candidate_root in [start, *start.parents]:
        candidate = candidate_root / DEFAULT_CONFIG_PATH
        if candidate.exists():
            return candidate
    return None


def find_config_path(start_path: Path | None = None) -> Path | None:
    """Return the discovered project config path, if any."""

    start = (start_path or Path.cwd()).resolve()
    return _search_config_path(start)


def load_config(start_path: Path | None = None) -> SocratesConfig:
    """Load config from `.socrates/config.toml` and overlay env vars."""

    config = SocratesConfig()
    start = (start_path or Path.cwd()).resolve()
    config_path = _search_config_path(start)
    if config_path:
        raw_data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        try:
            config = SocratesConfig.model_validate(raw_data)
        except ValidationError as exc:
            raise ConfigurationError(f"Invalid config file at {config_path}: {exc}") from exc

    env_api_key = os.getenv("SOCRATES_API_KEY") or os.getenv("OPENAI_API_KEY")
    env_base_url = os.getenv("SOCRATES_BASE_URL")
    env_default_model = os.getenv("SOCRATES_MODEL")
    env_frame_model = os.getenv("SOCRATES_FRAME_MODEL")
    env_outline_model = os.getenv("SOCRATES_OUTLINE_MODEL")
    env_draft_model = os.getenv("SOCRATES_DRAFT_MODEL")
    env_review_model = os.getenv("SOCRATES_REVIEW_MODEL")

    provider = config.provider.model_copy(
        update={
            "api_key": env_api_key or config.provider.api_key,
            "base_url": env_base_url or config.provider.base_url,
        }
    )
    models = config.models.model_copy(
        update={
            "default_model": env_default_model or config.models.default_model,
            "frame_model": env_frame_model or config.models.frame_model,
            "outline_model": env_outline_model or config.models.outline_model,
            "draft_model": env_draft_model or config.models.draft_model,
            "review_model": env_review_model or config.models.review_model,
        }
    )
    return config.model_copy(update={"provider": provider, "models": models})


def write_default_config(destination: Path | None = None, *, force: bool = False) -> Path:
    """Write a starter project config."""

    target = (destination or Path.cwd() / DEFAULT_CONFIG_PATH).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not force:
        raise ConfigurationError(f"Config already exists at {target}")

    template = """[provider]
kind = "openai-compatible"
base_url = "https://api.openai.com/v1"
api_key = ""

[models]
default_model = "gpt-4.1-mini"
frame_model = ""
outline_model = ""
draft_model = ""
review_model = ""
temperature = 0.2

[generation]
fallback_to_prompt_json = true
timeout_seconds = 60.0
"""
    target.write_text(template, encoding="utf-8")
    return target


def require_api_key(config: SocratesConfig) -> None:
    """Raise when the provider requires an API key and one is not configured."""

    if config.provider.kind == "openai-compatible" and not config.provider.api_key:
        raise ConfigurationError(
            "Missing API key. Set SOCRATES_API_KEY or OPENAI_API_KEY, "
            "or add `provider.api_key` in .socrates/config.toml."
        )
