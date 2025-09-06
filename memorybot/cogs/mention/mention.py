from __future__ import annotations

import logging
import re

import discord
from discord.ext import commands

from memorybot.services.openai_chat import OpenAIChatService
from memorybot.db.repository import ConversationRepository
from memorybot.utils.message_payload import build_message_json, build_server_info
from memorybot.schemas.tools import tavily_tool_schema, tavily_tool_instructions
from memorybot.prompt.system_prompt import build_system_prompt
import json
from memorybot.services.tooling import ToolExecutor


class MentionResponder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log = logging.getLogger("memorybot.cog.mention")
        self.ai = OpenAIChatService(getattr(bot, "settings"))
        self.repo = ConversationRepository()
        self.tools = ToolExecutor(getattr(bot, "settings"))

    def cog_unload(self) -> None:
        try:
            loop = getattr(self.bot, "loop", None)
            if loop and loop.is_running():
                loop.create_task(self.ai.aclose())
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not self.bot.user:
            return
        if message.author.bot:
            return
        if self.bot.user not in message.mentions:
            return
        try:
            cleaned = self._strip_bot_mentions(message.content, self.bot.user.id).strip()
            if not cleaned:
                return
            name = self.bot.user.display_name or self.bot.user.name
            server_info = build_server_info(message.guild)
            system_prompt = build_system_prompt(
                bot_name=name,
                server_info=server_info,
                tool_schemas=[tavily_tool_schema()],
                tool_instructions=[tavily_tool_instructions()],
            )
            await self.repo.add_message(
                guild_id=getattr(message.guild, "id", None),
                channel_id=message.channel.id,
                user_id=message.author.id,
                role="user",
                content=build_message_json(message, cleaned),
            )
            gid = getattr(message.guild, "id", None)
            if gid is not None:
                history = await self.repo.get_recent_messages_by_guild(guild_id=gid, limit=20)
            else:
                history = await self.repo.get_recent_messages(channel_id=message.channel.id, limit=20)
            mapped = [{"role": m.role, "content": m.content} for m in history]
            current_payload = build_message_json(message, cleaned)
            parsed = await self.ai.chat(current_payload, system_prompt=system_prompt, history=mapped)
            if not parsed or not getattr(parsed, "message", None) or not getattr(parsed.message, "content", None):
                return
            assistant_payload = json.dumps(parsed.model_dump(), indent=2, ensure_ascii=False)
            await self.repo.add_message(
                guild_id=getattr(message.guild, "id", None),
                channel_id=message.channel.id,
                user_id=self.bot.user.id,
                role="assistant",
                content=assistant_payload,
            )

            initial_msg = await message.reply(parsed.message.content, mention_author=False)

            if getattr(parsed, "tool", None):
                tool_result = await self.tools.execute(parsed.tool)
                tool_content = self.tools.serialize_result(tool_result)
                await self.repo.add_message(
                    guild_id=getattr(message.guild, "id", None),
                    channel_id=message.channel.id,
                    user_id=self.bot.user.id,
                    role="tool",
                    content=tool_content,
                )
                history = await (
                    self.repo.get_recent_messages_by_guild(guild_id=gid, limit=22)
                    if gid is not None
                    else self.repo.get_recent_messages(channel_id=message.channel.id, limit=22)
                )
                mapped = [{"role": m.role, "content": m.content} for m in history]
                followup = await self.ai.chat(current_payload, system_prompt=system_prompt, history=mapped)
                if followup and getattr(followup, "message", None) and getattr(followup.message, "content", None):
                    await self.repo.add_message(
                        guild_id=getattr(message.guild, "id", None),
                        channel_id=message.channel.id,
                        user_id=self.bot.user.id,
                        role="assistant",
                        content=json.dumps(followup.model_dump(), indent=2, ensure_ascii=False),
                    )
                    try:
                        await initial_msg.reply(followup.message.content, mention_author=False)
                    except Exception:
                        pass
            self.log.debug("responded to mention guild=%s channel=%s author=%s", getattr(message.guild, "id", None), message.channel.id, message.author.id)
        except Exception:
            self.log.error("mention handler error", exc_info=True)

    def _strip_bot_mentions(self, text: str, bot_id: int) -> str:
        patterns = [rf"<@{bot_id}>", rf"<@!{bot_id}>"]
        s = text
        for p in patterns:
            s = re.sub(p, "", s)
        return s


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MentionResponder(bot))
