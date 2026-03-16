"""Custom exceptions exposed by the package."""


class SocratesError(RuntimeError):
    """Base error for Socrates failures."""


class ConfigurationError(SocratesError):
    """Raised when config or environment is incomplete."""


class ProviderError(SocratesError):
    """Raised when an LLM provider call fails."""

