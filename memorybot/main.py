import asyncio
from dotenv import load_dotenv
from .core.runtime import start_bot


def run() -> None:
    load_dotenv()
    asyncio.run(start_bot())
