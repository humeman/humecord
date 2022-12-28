import humecord
import discord
from humecord.utils import (
    exceptions
)

async def get_gdb(
        guild: discord.Guild,
        botapi: str = None
    ):

    if botapi is None:
        botapi = humecord.bot.config.self_api

    try:
        gdb = await humecord.bot.api.get(
            botapi,
            "guild",
            {
                "id": guild.id,
                "autocreate": True
            }
        )

    except:
        raise exceptions.APIError(f"Guild database could not be retrieved for {guild.id}.")

    return gdb

async def put_gdb(
        guild: discord.Guild,
        changes: dict,
        botapi: str = None
    ):

    if botapi is None:
        botapi = humecord.bot.config.self_api

    try:
        gdb = await humecord.bot.api.put(
            botapi,
            "guild",
            {
                "id": guild.id,
                "db": changes,
                "autocreate": True
            }
        )

    except:
        raise exceptions.APIError(f"Guild database could not be pushed for {guild.id}.")