from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Integer, BigInteger, String, DateTime


Base = declarative_base()


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
