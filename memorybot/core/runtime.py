import asyncio
import logging
import os
import platform
import signal
import sys

from dotenv import load_dotenv

from .config import Settings, load_settings
from .logging import configure_logging
from .bot import MemoryBot


def _install_signal_handlers(bot: MemoryBot) -> None:
    loop = asyncio.get_running_loop()
    for sig in (getattr(signal, "SIGINT", None), getattr(signal, "SIGTERM", None)):
        if sig is None:
            continue
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(bot.close()))
        except NotImplementedError:
            pass


async def start_bot() -> None:
    load_dotenv()
    settings = load_settings()
    configure_logging(settings.log_level)
    log = logging.getLogger("startup")
    try:
        import discord as _discord
        _discord_ver = getattr(_discord, "__version__", "unknown")
    except Exception:
        _discord_ver = "unknown"
    log.debug(
        "starting app_id=%s owners=%d level=%s py=%s.%s discord.py=%s pid=%s platform=%s",
        settings.application_id,
        len(settings.owner_ids),
        settings.log_level,
        sys.version_info.major,
        sys.version_info.minor,
        _discord_ver,
        os.getpid(),
        platform.platform(),
    )
    bot = MemoryBot(settings)
    _install_signal_handlers(bot)
    token = settings.token
    if not token or not token.strip():
        log.error("missing DISCORD_TOKEN; set it in environment or .env")
        raise SystemExit(2)
    try:
        await bot.start(token)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        if not bot.is_closed():
            await bot.close()
