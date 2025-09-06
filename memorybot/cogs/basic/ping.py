from __future__ import annotations

import time

import discord
import logging
from discord import app_commands, Interaction
from discord.ext import commands


class Basic(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log = logging.getLogger("memorybot.cog.basic")

    @app_commands.command(name="ping", description="Latency check")
    async def ping(self, interaction: Interaction):
        ts = time.perf_counter()
        await interaction.response.defer(ephemeral=True)
        delta = (time.perf_counter() - ts) * 1000
        hb = self.bot.latency * 1000
        await interaction.followup.send(f"ws {hb:.0f}ms | rt {delta:.0f}ms", ephemeral=True)
        self.log.debug("ping ws=%.0f rt=%.0f", hb, delta)

    @app_commands.context_menu(name="User ID")
    async def user_id(self, interaction: Interaction, user: discord.User):
        await interaction.response.send_message(str(user.id), ephemeral=True)
        self.log.debug("user_id target=%s by=%s", user.id, interaction.user and interaction.user.id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Basic(bot))
