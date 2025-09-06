from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator
from tavily import TavilyClient


class TavilySearchOptions(BaseModel):
    include_answer: Optional[Literal["none", "basic", "advanced"]] = None
    search_depth: Optional[Literal["basic", "advanced"]] = None
    max_results: Optional[int] = Field(default=None, ge=1, le=50)

    def to_kwargs(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class TavilySearchService:
    def __init__(self, api_key: Optional[str] = None, *, logger: Optional[logging.Logger] = None):
        self._api_key = api_key
        self._client: Optional[TavilyClient] = None
        self._log = logger or logging.getLogger("memorybot.service.tavily")

    def _resolve_api_key(self) -> str:
        key = self._api_key or os.getenv("TAVILY_API_KEY", "").strip()
        if not key:
            raise RuntimeError("TAVILY_API_KEY is not configured")
        return key

    def _client_instance(self) -> TavilyClient:
        if self._client is None:
            key = self._resolve_api_key()
            self._client = TavilyClient(key)
        return self._client

    async def search(
        self,
        query: str,
        *,
        options: TavilySearchOptions | dict[str, Any] | None = None,
        timeout: float = 20.0,
    ) -> dict[str, Any]:
        q = (query or "").strip()
        if not q:
            raise ValueError("query is required")
        opts: TavilySearchOptions
        if options is None:
            opts = TavilySearchOptions()
        elif isinstance(options, TavilySearchOptions):
            opts = options
        else:
            try:
                opts = TavilySearchOptions(**options)
            except ValidationError as e:
                raise ValueError(str(e))

        kwargs = opts.to_kwargs()
        client = self._client_instance()
        loop = asyncio.get_running_loop()

        def _call() -> dict[str, Any]:
            return client.search(query=q, **kwargs)

        try:
            raw = await asyncio.wait_for(loop.run_in_executor(None, _call), timeout=timeout)
            if isinstance(raw, dict):
                ans = raw.get("answer")
            else:
                ans = None
            return {"answer": ans}
        except asyncio.TimeoutError:
            self._log.error("tavily search timed out", extra={"timeout": timeout})
            raise
        except Exception as e:
            self._log.error("tavily search failed", exc_info=e)
            raise

    async def aclose(self) -> None:
        self._client = None
