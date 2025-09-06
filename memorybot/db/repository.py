from __future__ import annotations

from typing import List, Optional
from datetime import datetime

from sqlalchemy import select

from .session import session
from .models import Message, Base
from sqlalchemy.ext.asyncio import AsyncEngine


class ConversationRepository:
    async def add_message(
        self,
        *,
        guild_id: Optional[int],
        channel_id: int,
        user_id: Optional[int],
        role: str,
        content: str,
    ) -> Message:
        async with session() as s:
            m = Message(
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                role=role,
                content=content,
                created_at=datetime.utcnow(),
            )
            s.add(m)
            await s.commit()
            await s.refresh(m)
            return m

    async def get_recent_messages(self, *, channel_id: int, limit: int = 20) -> List[Message]:
        async with session() as s:
            stmt = (
                select(Message)
                .where(Message.channel_id == channel_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
            res = await s.execute(stmt)
            rows = list(res.scalars())
            rows.reverse()
            return rows

    async def get_recent_messages_by_guild(self, *, guild_id: int, limit: int = 20) -> List[Message]:
        async with session() as s:
            stmt = (
                select(Message)
                .where(Message.guild_id == guild_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
            res = await s.execute(stmt)
            rows = list(res.scalars())
            rows.reverse()
            return rows

    async def create_all(self, engine: AsyncEngine) -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
