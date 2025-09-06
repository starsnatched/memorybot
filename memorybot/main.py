import asyncio
from .core.runtime import start_bot


def run() -> None:
    asyncio.run(start_bot())

