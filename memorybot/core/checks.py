from __future__ import annotations

import logging
from discord import app_commands, Interaction


def is_owner_check():
    async def predicate(interaction: Interaction) -> bool:
        client = interaction.client
        user_id = interaction.user.id
        owner_ids = getattr(client, "owner_ids", set())
        ok = user_id in owner_ids
        logging.getLogger("memorybot.checks").debug("is_owner user=%s ok=%s", user_id, ok)
        return ok

    return app_commands.check(predicate)
