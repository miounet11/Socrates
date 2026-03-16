from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from socrates.providers.openai_compatible import OpenAICompatibleProvider


class SimplePayload(BaseModel):
    value: str


class StubResponse:
    def __init__(
        self,
        *,
        status_code: int,
        payload: dict[str, Any] | None = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict[str, Any]:
        return self._payload


def test_openai_compatible_provider_retries_retryable_status(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []
    responses = [
        StubResponse(status_code=504, text="gateway timeout"),
        StubResponse(
            status_code=200,
            payload={"choices": [{"message": {"content": '{"value":"ok"}'}}]},
        ),
    ]

    def fake_post(*_args: Any, **kwargs: Any) -> StubResponse:
        calls.append(kwargs)
        return responses.pop(0)

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr("socrates.providers.openai_compatible.time.sleep", lambda _seconds: None)

    provider = OpenAICompatibleProvider(
        api_key="test-key",
        base_url="https://example.com/v1",
        timeout_seconds=30.0,
        max_retries=1,
        retry_backoff_seconds=0.0,
    )

    result = provider.structured_completion(
        messages=[{"role": "user", "content": "hello"}],
        response_model=SimplePayload,
        model="auto",
        temperature=0.2,
    )

    assert result.value == "ok"
    assert len(calls) == 2
