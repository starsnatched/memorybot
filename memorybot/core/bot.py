from __future__ import annotations

import asyncio
import logging
from typing import Iterable

import discord
from discord.ext import commands

from .config import Settings
from .loader import discover_extensions, load_extensions
from .logging import set_request_id, reset_request_id


class MemoryBot(commands.Bot):
    def __init__(self, settings: Settings):
        intents = discord.Intents.all()
        super().__init__(
            command_prefix=commands.when_mentioned_or(",,"),
            intents=intents,
            application_id=settings.application_id,
        )
        self.settings = settings
        self.owner_ids: set[int] = set(settings.owner_ids)
        self.log = logging.getLogger("memorybot")
        self.synced = asyncio.Event()

    async def setup_hook(self) -> None:
        self.log.debug("setup_hook begin")
        target_exts: list[str] = discover_extensions("memorybot.cogs")
        loaded, failed = await load_extensions(self, target_exts)
        if loaded:
            self.log.info("loaded %d extensions", len(loaded))
            self.log.debug("extensions loaded: %s", ", ".join(loaded))
        if failed:
            self.log.warning("%d extensions failed to load", len(failed))
            self.log.debug("extensions failed: %s", ", ".join(m for m, _ in failed))
        await self._populate_owner_ids()
        await self.sync_app_commands(mode="global")
        self.synced.set()
        self.tree.on_error = self.on_app_command_error
        self.log.debug("setup_hook complete")

    async def on_ready(self) -> None:
        self.log.info("ready as %s (%s)", self.user, self.user and self.user.id)
        self.log.debug("guilds=%d latency_ms=%.0f", len(self.guilds), self.latency * 1000)
        await self.change_presence(activity=discord.Game(name="/sync to update commands"))

    async def on_connect(self) -> None:
        self.log.debug("gateway connect")

    async def on_disconnect(self) -> None:
        self.log.warning("gateway disconnect")

    async def on_resumed(self) -> None:
        self.log.info("gateway resumed")

    async def _populate_owner_ids(self) -> None:
        try:
            info = await self.application_info()
        except Exception:
            return
        if info.team:
            self.owner_ids.update({m.user.id for m in info.team.members})
        if info.owner:
            self.owner_ids.add(info.owner.id)
        self.log.debug("owner_ids=%s", ",".join(map(str, sorted(self.owner_ids))))

    async def sync_app_commands(self, *, mode: str = "guild", guilds: Iterable[int] | None = None) -> list[discord.app_commands.AppCommand] | None:
        self.log.debug("sync_app_commands mode=%s guilds=%s", mode, list(guilds) if guilds else None)
        if mode == "none":
            return None
        if mode not in {"global", "guild", "copy", "clear"}:
            mode = "guild"
        if mode == "global":
            cmds = await self.tree.sync()
            self.log.info("synced %d global commands", len(cmds))
            return cmds
        target_guild_ids = list(guilds) if guilds else []
        if mode == "guild" and not target_guild_ids:
            cmds = await self.tree.sync()
            self.log.info("no guilds configured; synced %d global commands", len(cmds))
            return cmds
        results: list[discord.app_commands.AppCommand] = []
        for gid in target_guild_ids:
            guild_obj = discord.Object(id=gid)
            if mode == "clear":
                self.tree.clear_commands(guild=guild_obj)
                await self.tree.sync(guild=guild_obj)
                self.log.info("cleared commands for guild %s", gid)
                continue
            if mode == "copy":
                self.tree.copy_global_to(guild=guild_obj)
            cmds = await self.tree.sync(guild=guild_obj)
            results.extend(cmds)
            self.log.info("synced %d commands for guild %s", len(cmds), gid)
        return results

    async def on_app_command_error(self, interaction: discord.Interaction, error: Exception) -> None:
        self.log.error(
            "app command error cmd=%s user=%s guild=%s",
            getattr(interaction.command, "qualified_name", None),
            getattr(interaction.user, "id", None),
            getattr(interaction.guild, "id", None),
            exc_info=error,
        )
        try:
            if interaction.response.is_done():
                await interaction.followup.send("An error occurred.", ephemeral=True)
            else:
                await interaction.response.send_message("An error occurred.", ephemeral=True)
        except Exception:
            pass

    async def on_command_error(self, ctx: commands.Context, error: Exception) -> None:
        self.log.error(
            "prefix command error cmd=%s user=%s guild=%s",
            getattr(ctx.command, "qualified_name", None),
            getattr(ctx.author, "id", None),
            getattr(ctx.guild, "id", None),
            exc_info=error,
        )

    async def on_error(self, event_method: str, /, *args, **kwargs) -> None:  # type: ignore[override]
        self.log.error("event error event=%s", event_method, exc_info=True)

    async def on_guild_join(self, guild: discord.Guild) -> None:
        self.log.info("guild join id=%s name=%s members=%s", guild.id, guild.name, guild.member_count)

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        self.log.info("guild remove id=%s name=%s", guild.id, guild.name)

    async def on_interaction(self, interaction: discord.Interaction) -> None:
        rid = str(getattr(interaction, "id", "-"))
        token = set_request_id(rid)
        try:
            self.log.debug(
                "interaction received type=%s command=%s user=%s guild=%s",
                getattr(interaction, "type", None),
                getattr(interaction.command, "qualified_name", None),
                getattr(interaction.user, "id", None),
                getattr(interaction.guild, "id", None),
            )
            await super().on_interaction(interaction)
        finally:
            reset_request_id(token)

    async def on_socket_event_type(self, event_type: str) -> None:
        self.log.debug("socket event type=%s", event_type)
