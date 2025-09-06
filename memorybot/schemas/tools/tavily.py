from __future__ import annotations

from typing import Any


TAVILY_TOOL_NAME = "tavily_search"


def tavily_tool_schema() -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": TAVILY_TOOL_NAME,
            "description": "Searches the web for up-to-date information using Tavily. Use for recent, factual, or source-backed queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "minLength": 1,
                        "description": "Clear, specific search query phrased for a web search engine.",
                    },
                    "include_answer": {
                        "type": "string",
                        "enum": ["none", "basic", "advanced"],
                        "default": "advanced",
                        "description": "Controls inclusion of synthesized answer; use 'advanced' for rich summaries.",
                    },
                    "search_depth": {
                        "type": "string",
                        "enum": ["basic", "advanced"],
                        "default": "advanced",
                        "description": "Depth of search exploration; 'advanced' for broader sources.",
                    },
                    "max_results": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 7,
                        "description": "Maximum number of results to retrieve (1-50).",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    }


def tavily_tool_instructions() -> str:
    return (
        "You can call a web search tool when external, current, or factual information is needed. "
        "Use it when questions require recent events, statistics, sources, or verification. "
        "Always pass a concise, specific 'query' and prefer include_answer='advanced', search_depth='advanced', max_results up to 7. "
        "If the user asks to browse, verify facts, find sources, or requests up-to-date info, call the tool. "
        "If the answer is purely conceptual or self-contained with no need for current data, do not call the tool. "
        "After a tool call, summarize the findings with attributions and note uncertainty if applicable."
    )

