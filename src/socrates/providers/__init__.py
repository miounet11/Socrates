"""Provider construction helpers."""

from socrates.config import SocratesConfig, require_api_key
from socrates.exceptions import ConfigurationError
from socrates.providers.base import LLMProvider
from socrates.providers.openai_compatible import OpenAICompatibleProvider


def build_provider(config: SocratesConfig) -> LLMProvider:
    """Construct the configured provider."""

    if config.provider.kind != "openai-compatible":
        raise ConfigurationError(f"Unsupported provider kind: {config.provider.kind}")

    require_api_key(config)
    assert config.provider.api_key is not None
    return OpenAICompatibleProvider(
        api_key=config.provider.api_key,
        base_url=config.provider.base_url,
        timeout_seconds=config.generation.timeout_seconds,
        fallback_to_prompt_json=config.generation.fallback_to_prompt_json,
    )
