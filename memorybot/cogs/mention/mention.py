from __future__ import annotations

import logging
import re

import discord
from discord.ext import commands

from memorybot.services.openai_chat import OpenAIChatService
from memorybot.db.repository import ConversationRepository
from memorybot.utils.message_payload import build_message_json, build_server_info
import json


class MentionResponder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log = logging.getLogger("memorybot.cog.mention")
        self.ai = OpenAIChatService(getattr(bot, "settings"))
        self.repo = ConversationRepository()

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
            system_prompt = (
                f"You are {name}, a helpful Discord bot. "
                "Respond in a warm, human-like tone. Keep replies short and conversational, ideally under two sentences. "
                "Be clear and helpful, avoid long texts, and only include necessary details. "
                "If the user message lacks a direct question, offer brief, relevant guidance.\n"
                "Server Information (JSON):\n"
                f"{json.dumps(server_info, indent=2, ensure_ascii=False)}"
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
            await self.repo.add_message(
                guild_id=getattr(message.guild, "id", None),
                channel_id=message.channel.id,
                user_id=self.bot.user.id,
                role="assistant",
                content=json.dumps(parsed.model_dump(), indent=2, ensure_ascii=False),
            )
            await message.reply(parsed.message.content, mention_author=False)
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
