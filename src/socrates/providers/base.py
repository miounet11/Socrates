"""Provider protocol and shared types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

Message = dict[str, str]
T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Minimal provider surface needed by the pipeline."""

    @abstractmethod
    def structured_completion(
        self,
        *,
        messages: list[Message],
        response_model: type[T],
        model: str,
        temperature: float,
    ) -> T:
        """Return a typed response from the model."""

