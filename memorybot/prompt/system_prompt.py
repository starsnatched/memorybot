from __future__ import annotations

import json
from typing import Any, Iterable


def build_system_prompt(
    *,
    bot_name: str,
    server_info: dict[str, Any] | None = None,
    tool_schemas: Iterable[dict[str, Any]] | None = None,
    tool_instructions: Iterable[str] | None = None,
) -> str:
    name = bot_name.strip() or "Assistant"
    info = server_info or {}
    schemas = list(tool_schemas or [])
    instructions = [s for s in (tool_instructions or []) if isinstance(s, str) and s.strip()]
    persona = (
        f"You are {name}, a helpful Discord bot. "
        "Respond in a warm, human-like tone. Keep replies short and conversational, ideally under two sentences. "
        "Be clear and helpful, avoid long texts, and only include necessary details. "
        "If the user message lacks a direct question, offer brief, relevant guidance."
    )
    contract = (
        "Response Contract:\n"
        "- Always return JSON matching: { message: { content: string }, tool?: { name: string, arguments: object } | null }\n"
        "- If no tool is needed, set tool to null or omit it.\n"
        "- Use only the tools described below and validate arguments against the given JSON Schemas."
    )
    tooling_policy = (
        "Tool Usage Policy:\n"
        "- Consider a tool call when external, current, or source-backed information is required.\n"
        "- Do not call tools for conversational, opinionated, or self-contained questions.\n"
        "- When calling a tool, set tool.name and tool.arguments to valid values.\n"
        "- Do not invent tools or parameters that are not in the schemas."
    )
    tools_block = (
        "Available Tools (as JSON Schemas):\n" + json.dumps(schemas, indent=2, ensure_ascii=False)
        if schemas
        else "Available Tools: []"
    )
    tool_guides = (
        "Tool-Specific Guidance:\n" + "\n".join(instructions)
        if instructions
        else "Tool-Specific Guidance:\nNone"
    )
    server = "Server Information (JSON):\n" + json.dumps(info, indent=2, ensure_ascii=False)
    parts = [persona, server, contract, tooling_policy, tools_block, tool_guides]
    return "\n\n".join(parts)

