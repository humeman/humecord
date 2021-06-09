
from typing import Iterable, Optional

from humecord.utils import (
        exceptions
    )

class OverrideHandler:
    def __init__(
            self,
            bot_
        ):

        global bot
        bot = bot_

    async def check(
            self,
            guild_id: int,
            bots: Iterable[str],
            return_name: bool = False
        ):

        try:
            overrides = await bot.api.get(
                "main",
                "overrides",
                {
                    "guild": guild_id,
                    "bots": bots + [bot.config.self_api],
                    "autocreate": True
                }
            )

        except:
            raise exceptions.APIError(f"Overrides lookup failed for guild {guild_id}")

        if "bot" in overrides:
            if return_name:
                return overrides["bot"]

            return overrides["bot"] == bot.config.self_api

        raise exceptions.APIError(f"Bot not returned after overrides lookup")

    async def put_guilds(
            self,
            guild_ids: list
        ):

        await bot.api.put(
            "main",
            "overrides",
            {
                "bot": bot.config.self_api,
                "guilds": [{"id": x, "enabled": True} for x in guild_ids],
                "autocreate": True
            }
        )

    async def set_priority(
            self,
            guild_id: int,
            priority: int,
            bot: Optional[str] = None
        ):

        if not bot:
            bot = self.bot.config.self_api

        await bot.api.get(
            "main",
            "override_settings",
            {
                "bot": bot,
                "guild": guild_id,
                "priority": priority,
                "autocreate": True
            }
        )

    async def get_priorities(
            self,
            guild_id: int
        ):
        return (await bot.api.get(
            "main",
            "override_settings",
            {
                "guild": guild_id,
                "autocreate": True
            }
        ))["priorities"]