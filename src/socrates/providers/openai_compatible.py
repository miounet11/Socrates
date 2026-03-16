"""OpenAI-compatible chat completions adapter."""

from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import ValidationError

from socrates.exceptions import ProviderError
from socrates.providers.base import LLMProvider, Message, T


class OpenAICompatibleProvider(LLMProvider):
    """HTTP adapter for chat-completions style providers."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout_seconds: float = 60.0,
        fallback_to_prompt_json: bool = True,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.fallback_to_prompt_json = fallback_to_prompt_json

    def structured_completion(
        self,
        *,
        messages: list[Message],
        response_model: type[T],
        model: str,
        temperature: float,
    ) -> T:
        schema = response_model.model_json_schema()
        try:
            payload = self._post_chat_completions(
                messages=messages,
                model=model,
                temperature=temperature,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": response_model.__name__,
                        "strict": True,
                        "schema": schema,
                    },
                },
            )
            content = self._extract_content(payload)
            return response_model.model_validate_json(content)
        except (ProviderError, ValidationError):
            if not self.fallback_to_prompt_json:
                raise
            fallback_messages = self._with_json_schema_instruction(
                messages,
                schema,
                response_model.__name__,
            )
            payload = self._post_chat_completions(
                messages=fallback_messages,
                model=model,
                temperature=temperature,
                response_format=None,
            )
            content = self._extract_content(payload)
            parsed = self._coerce_json_string(content)
            try:
                return response_model.model_validate(parsed)
            except ValidationError as exc:
                raise ProviderError(
                    f"Provider returned invalid JSON for {response_model.__name__}: {exc}"
                ) from exc

    def _post_chat_completions(
        self,
        *,
        messages: list[Message],
        model: str,
        temperature: float,
        response_format: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format is not None:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
        except httpx.HTTPError as exc:
            raise ProviderError(f"Provider request failed: {exc}") from exc

        if response.status_code >= 400:
            raise ProviderError(
                f"Provider returned {response.status_code}: {response.text[:400]}"
            )

        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise ProviderError("Provider returned non-JSON HTTP response.") from exc
        if not isinstance(payload, dict):
            raise ProviderError("Provider returned a non-object JSON response.")
        return payload

    def _extract_content(self, payload: dict[str, Any]) -> str:
        try:
            message = payload["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("Provider response did not include a completion choice.") from exc

        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
            joined = "".join(text_parts).strip()
            if joined:
                return joined
        raise ProviderError("Provider response did not contain textual content.")

    def _with_json_schema_instruction(
        self,
        messages: list[Message],
        schema: dict[str, Any],
        schema_name: str,
    ) -> list[Message]:
        instruction = {
            "role": "system",
            "content": (
                "Return only valid JSON for the requested response. "
                f"It must validate against this schema named {schema_name}:\n"
                f"{json.dumps(schema, indent=2, sort_keys=True)}"
            ),
        }
        return [instruction, *messages]

    def _coerce_json_string(self, content: str) -> dict[str, Any]:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ProviderError("Provider fallback mode returned invalid JSON.") from exc
        if not isinstance(parsed, dict):
            raise ProviderError("Provider fallback mode returned a non-object JSON payload.")
        return parsed
