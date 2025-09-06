from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    content: str


class ToolUsage(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("name is required")
        return s


class ChatResponse(BaseModel):
    message: ChatMessage
    tool: Optional[ToolUsage]
