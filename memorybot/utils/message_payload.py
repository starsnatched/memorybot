from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

import discord


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if isinstance(dt, datetime) else None


def _user_info(user: discord.abc.User) -> Dict[str, Any]:
    return {
        "id": getattr(user, "id", None),
        "name": getattr(user, "name", None),
        "display_name": getattr(user, "display_name", None) or getattr(user, "global_name", None),
        "bot": getattr(user, "bot", None),
    }


def _channel_info(channel: discord.abc.Messageable) -> Dict[str, Any]:
    base: Dict[str, Any] = {"id": getattr(channel, "id", None), "type": channel.__class__.__name__}
    name = getattr(channel, "name", None)
    if name:
        base["name"] = name
    topic = getattr(channel, "topic", None)
    if topic:
        base["topic"] = topic
    nsfw = getattr(channel, "nsfw", None)
    if nsfw is not None:
        base["nsfw"] = nsfw
    category = getattr(channel, "category", None)
    if category is not None:
        base["category"] = {"id": getattr(category, "id", None), "name": getattr(category, "name", None)}
    return base


def _reference_info(message: discord.Message) -> Optional[Dict[str, Any]]:
    ref = message.reference
    if not ref:
        return None
    data: Dict[str, Any] = {"message_id": getattr(ref, "message_id", None), "channel_id": getattr(ref, "channel_id", None), "guild_id": getattr(ref, "guild_id", None)}
    resolved = getattr(ref, "resolved", None)
    if isinstance(resolved, discord.Message):
        data["resolved"] = {
            "id": resolved.id,
            "author": _user_info(resolved.author),
            "created_at": _iso(resolved.created_at),
            "content_preview": (resolved.content[:500] if resolved.content else None),
            "has_attachments": bool(resolved.attachments),
        }
    return data


def build_server_info(guild: Optional[discord.Guild]) -> Dict[str, Any]:
    if guild is None:
        return {"type": "DM", "guild": None}
    return {
        "id": guild.id,
        "name": guild.name,
        "description": getattr(guild, "description", None),
        "owner_id": getattr(guild, "owner_id", None),
        "approx_member_count": getattr(guild, "member_count", None),
        "created_at": _iso(getattr(guild, "created_at", None)),
        "features": list(getattr(guild, "features", []) or []),
        "nsfw_level": getattr(guild, "nsfw_level", None).name if getattr(guild, "nsfw_level", None) else None,
        "premium_tier": getattr(guild, "premium_tier", None),
        "verification_level": getattr(guild, "verification_level", None).name if getattr(guild, "verification_level", None) else None,
        "region": getattr(guild, "preferred_locale", None),
    }


def build_message_json(message: discord.Message, cleaned_content: str) -> str:
    payload: Dict[str, Any] = {
        "message": {
            "id": message.id,
            "created_at": _iso(message.created_at),
            "content": cleaned_content,
            "reference": _reference_info(message),
        },
        "author": _user_info(message.author),
        "channel": _channel_info(message.channel),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
