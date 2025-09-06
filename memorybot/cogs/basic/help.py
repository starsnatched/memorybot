from __future__ import annotations

import logging
from typing import Iterable, List, Tuple

import discord
from discord import app_commands, Interaction
from discord.ext import commands


def _format_option(param: discord.app_commands.AppCommandParameter) -> str:
    name = getattr(param, "name", "")
    required = bool(getattr(param, "required", False))
    t = getattr(param, "type", None)
    tname = getattr(t, "name", None) or str(t).split(".")[-1].lower()
    core = f"{name}:{tname}" if tname else name
    return f"<{core}>" if required else f"[{core}]"


def _signature(cmd: discord.app_commands.AppCommand) -> str:
    params = list(getattr(cmd, "parameters", []) or [])
    if not params:
        return f"/{cmd.qualified_name}"
    opts = " ".join(_format_option(p) for p in params)
    return f"/{cmd.qualified_name} {opts}"


def _collect_commands(tree: discord.app_commands.CommandTree) -> Tuple[List[discord.app_commands.AppCommand], List[discord.app_commands.AppCommand]]:
    cmds: List[discord.app_commands.AppCommand] = []
    ctx: List[discord.app_commands.AppCommand] = []
    for c in tree.get_commands():
        if isinstance(c, discord.app_commands.AppCommandGroup):
            for sc in c.walk_commands():
                if isinstance(sc, discord.app_commands.AppCommand) and sc.type == discord.AppCommandType.chat_input:
                    cmds.append(sc)
        elif isinstance(c, discord.app_commands.AppCommand):
            if c.type == discord.AppCommandType.chat_input:
                cmds.append(c)
            else:
                ctx.append(c)
    cmds = sorted(cmds, key=lambda x: x.qualified_name)
    ctx = sorted(ctx, key=lambda x: x.name)
    return cmds, ctx


def _chunk(text: str, limit: int = 1900) -> Iterable[str]:
    start = 0
    n = len(text)
    while start < n:
        end = min(start + limit, n)
        yield text[start:end]
        start = end


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log = logging.getLogger("memorybot.cog.help")

    @app_commands.command(name="help", description="Show available commands and usage")
    async def help(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        cmds, ctx = _collect_commands(self.bot.tree)
        lines: List[str] = []
        if cmds:
            lines.append("Slash Commands:")
            for c in cmds:
                sig = _signature(c)
                desc = getattr(c, "description", "") or ""
                lines.append(f"• {sig} — {desc}")
        if ctx:
            if lines:
                lines.append("")
            lines.append("Context Menus:")
            for c in ctx:
                ctype = "User" if c.type == discord.AppCommandType.user else "Message"
                lines.append(f"• {c.name} ({ctype})")
        if not lines:
            lines.append("No commands available.")
        payload = "\n".join(lines)
        chunks = list(_chunk(payload))
        if not chunks:
            await interaction.followup.send("No commands available.", ephemeral=True)
            self.log.debug("help empty")
            return
        first, rest = chunks[0], chunks[1:]
        await interaction.followup.send(first, ephemeral=True)
        for part in rest:
            await interaction.followup.send(part, ephemeral=True)
        self.log.debug("help listed slash=%d ctx=%d parts=%d", len(cmds), len(ctx), 1 + len(rest))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))

