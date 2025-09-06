from __future__ import annotations

import logging
from typing import Iterable, Mapping, Optional

from openai import AsyncOpenAI

from memorybot.schemas.llm import ChatResponse
from memorybot.core.config import Settings


class OpenAIChatService:
    def __init__(self, settings: Settings, model: str | None = None):
        self._settings = settings
        self._client: Optional[AsyncOpenAI] = None
        self._model = model or settings.openai_model
        self._log = logging.getLogger("memorybot.service.openai")

    def _client_instance(self) -> AsyncOpenAI:
        if self._client is None:
            kwargs: dict = {}
            if self._settings.openai_api_key:
                kwargs["api_key"] = self._settings.openai_api_key
            base = self._settings.openai_base_url or self._settings.openai_api_base
            if base:
                kwargs["base_url"] = base
            self._client = AsyncOpenAI(**kwargs) if kwargs else AsyncOpenAI()
        return self._client

    async def chat(
        self,
        text: str,
        *,
        system_prompt: str | None = None,
        history: Iterable[Mapping[str, str]] | None = None,
    ) -> ChatResponse:
        msgs: list[dict] = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        if history:
            for m in history:
                r = m.get("role")
                c = m.get("content")
                if r in {"user", "assistant"} and c:
                    msgs.append({"role": r, "content": c})
        msgs.append({"role": "user", "content": text})
        client = self._client_instance()
        try:
            resp = await client.chat.completions.parse(
                model=self._model,
                messages=msgs,
                response_format=ChatResponse,
            )
            return resp.choices[0].message.parsed
        except Exception:
            self._log.warning("parse failed; falling back to create", exc_info=True)
        try:
            created = await client.chat.completions.create(model=self._model, messages=msgs)
            content = None
            try:
                content = created.choices[0].message.content if created.choices else None
            except Exception:
                content = None
            return ChatResponse(message=self._fallback_message(content or ""))
        except Exception as e:
            self._log.error("openai chat error", exc_info=e)
            raise
        
    def _fallback_message(self, content: str):
        from memorybot.schemas.llm import ChatMessage
        return ChatMessage(content=content)
