from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from socrates.models import ContentRequest
from socrates.providers.base import LLMProvider, Message, T


class StubProvider(LLMProvider):
    def __init__(self, responses: list[BaseModel | dict[str, Any]]) -> None:
        self.responses = responses[:]
        self.calls: list[dict[str, Any]] = []

    def structured_completion(
        self,
        *,
        messages: list[Message],
        response_model: type[T],
        model: str,
        temperature: float,
    ) -> T:
        self.calls.append(
            {
                "messages": messages,
                "response_model": response_model,
                "model": model,
                "temperature": temperature,
            }
        )
        if not self.responses:
            raise AssertionError("No stubbed provider responses remain.")
        response = self.responses.pop(0)
        if isinstance(response, BaseModel):
            return response_model.model_validate(response.model_dump())
        return response_model.model_validate(response)


@pytest.fixture()
def content_request() -> ContentRequest:
    return ContentRequest(
        topic="Why AI product messaging fails",
        audience="Product marketers at AI startups",
        goal="Create a publishable blog post draft",
        platform="blog",
        content_type="blog_post",
        constraints=["Avoid vague value props"],
        voice_notes=["Specific", "credible"],
        keywords=["AI messaging"],
        include_cta=True,
        cta_goal="Book a strategy call",
    )
