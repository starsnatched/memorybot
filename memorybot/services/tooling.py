from __future__ import annotations

import json
import logging
from typing import Any, Optional

from memorybot.core.config import Settings
from memorybot.schemas.llm import ToolUsage
from memorybot.schemas.tools import TAVILY_TOOL_NAME
from memorybot.services.tavily_search import TavilySearchService


class ToolExecutor:
    def __init__(self, settings: Settings, *, logger: Optional[logging.Logger] = None):
        self._settings = settings
        self._log = logger or logging.getLogger("memorybot.service.tools")
        self._tavily = TavilySearchService(api_key=settings.tavily_api_key, logger=self._log)

    async def execute(self, tool: ToolUsage) -> dict[str, Any]:
        name = (tool.name or "").strip()
        if not name:
            return {"status": "error", "error": "missing tool name"}
        try:
            if name == TAVILY_TOOL_NAME:
                args = tool.arguments or {}
                q = str(args.get("query", "")).strip()
                include_answer = args.get("include_answer")
                search_depth = args.get("search_depth")
                max_results = args.get("max_results")
                result = await self._tavily.search(
                    q,
                    options={
                        "include_answer": include_answer,
                        "search_depth": search_depth,
                        "max_results": max_results,
                    },
                )
                return {"status": "ok", "tool": name, "arguments": args, "result": result}
            return {"status": "error", "error": f"unknown tool: {name}", "tool": name, "arguments": tool.arguments}
        except Exception as e:
            self._log.error("tool execution failed", exc_info=e)
            return {"status": "error", "error": str(e), "tool": name, "arguments": tool.arguments}

    @staticmethod
    def serialize_result(payload: dict[str, Any]) -> str:
        try:
            return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        except Exception:
            return json.dumps({"status": "error", "error": "failed to serialize tool result"})

