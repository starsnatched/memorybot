from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, async_sessionmaker, AsyncSession

_engine: Optional[AsyncEngine] = None
_session_maker: Optional[async_sessionmaker[AsyncSession]] = None


async def init_engine(database_url: str) -> None:
    global _engine, _session_maker
    if _engine is None:
        _engine = create_async_engine(database_url, pool_pre_ping=True, pool_recycle=1800)
        _session_maker = async_sessionmaker(_engine, expire_on_commit=False)


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("database engine is not initialized")
    return _engine


def session() -> AsyncSession:
    if _session_maker is None:
        raise RuntimeError("database session maker is not initialized")
    return _session_maker()


async def close_engine() -> None:
    global _engine, _session_maker
    eng = _engine
    _session_maker = None
    _engine = None
    if eng is None:
        return
    dispose = getattr(eng, "dispose", None)
    if dispose is None:
        return
    res = dispose()
    if hasattr(res, "__await__"):
        await res
