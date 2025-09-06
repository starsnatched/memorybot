from __future__ import annotations

from pydantic import BaseModel


class ChatMessage(BaseModel):
    content: str


class ChatResponse(BaseModel):
    message: ChatMessage
