from __future__ import annotations

import enum
from typing import Optional
import logging

import discord
from discord import app_commands, Interaction
from discord.ext import commands

from ...core.checks import is_owner_check


class SyncMode(enum.Enum):
    global_ = "global"
    guild = "guild"
    copy = "copy"
    clear = "clear"


class SyncCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log = logging.getLogger("memorybot.cog.mgmt")

    @app_commands.command(name="sync", description="Synchronize application commands")
    @is_owner_check()
    @app_commands.describe(
        mode="Target mode",
        guild_id="Target guild id (optional)",
    )
    async def sync(self, interaction: Interaction, mode: SyncMode, guild_id: Optional[int] = None):
        await interaction.response.defer(ephemeral=True)
        m = mode.value
        guilds = [guild_id] if guild_id else None
        res = await self.bot.sync_app_commands(mode=m, guilds=guilds)
        if res is None:
            await interaction.followup.send("No sync performed", ephemeral=True)
            self.log.debug("sync skipped mode=%s guild_id=%s", m, guild_id)
            return
        await interaction.followup.send("Sync complete", ephemeral=True)
        self.log.debug("sync done mode=%s guild_id=%s count=%s", m, guild_id, res and len(res))

    @sync.error
    async def sync_error(self, interaction: Interaction, error: Exception):
        if isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message("Not authorized", ephemeral=True)
            self.log.debug("sync not authorized user=%s", interaction.user and interaction.user.id)
            return
        await interaction.response.send_message("Sync failed", ephemeral=True)
        self.log.error("sync failed", exc_info=error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SyncCog(bot))
