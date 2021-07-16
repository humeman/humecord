import discord
import time
import asyncio
import traceback
import aiohttp
import aiofiles
import math

import humecord

from humecord.utils import (
    dateutils,
    discordutils,
    hcutils,
    miscutils,
    components
)

class DevCommand:
    def __init__(self):
        self.name = "dev"

        self.description = "Extra Humecord development controls."

        self.aliases = ["development"]

        self.permission = "bot.dev"

        self.subcommands = {
            "error": {
                "function": self.error,
                "description": "Forces an error."
            },
            "reload": {
                "function": self.reload,
                "description": "Reloads the bot."
            },
            "close": {
                "function": self.close,
                "description": "Closes the bot."
            }
        }

        self.shortcuts = {
            "reload": "dev reload",
            "close": "dev close",
            "literallyjustfuckingdieihateyousomuch": "dev close"
        }

        global bot
        from humecord import bot

    async def error(
            self, 
            message,
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb,
            preferred_gdb
        ):
        raise humecord.utils.exceptions.TestException("dev.error call")

    async def reload(
            self, 
            message,
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb,
            preferred_gdb
        ):
        if len(args) > 2:
            safe = args[2].lower() not in ["f", "force"]

        else:
            safe = True

        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['loading']}  Reloading bot...",
                description = f"Safe reload: `{'Yes' if safe else 'No'}`",
                color = "icon_blue"
            )
        )

        await bot.loader.load(safe_stop = safe)

        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']}  Reloaded!",
                color = "success"
            )
        )

    async def close(
            self, 
            message,
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb,
            preferred_gdb
        ):
        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['loading']}  Shutting down...",
                color = "icon_blue"
            )
        )
        
        raise KeyboardInterrupt