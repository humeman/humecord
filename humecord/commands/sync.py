"""
/sync: humecord base commands

Syncs the command tree.
"""

import asyncio
from typing import Optional

import humecord

from humecord.classes import (
    discordclasses
)

from humecord.utils import (
    discordutils,
    debug
)

class SyncCommand(humecord.Command):
    def __init__(
            self
        ) -> None:
        self.name = "sync"
        self.description = "Syncs the slash command tree to Discord."
        self.command_tree = {
            "guild %guildid% %copy%": self.sync_guild,
            "global": self.sync_global,
            "clear %guildid%": self.clear
        }
        self.args = {
            "guildid": {
                "type": "str",
                "description": "Guild ID to sync the tree to.",
                "required": True
            },
            "copy": {
                "type": "bool",
                "description": "Whether to copy global commands to this guild first.",
                "required": True
            }
        }
        self.subcommand_details = {
            "guild": {
                "description": "Syncs to a single guild."
            },
            "global": {
                "description": "Syncs globally."
            },
            "clear": {
                "description": "Clears a guild's local commands."
            }
        }
        self.messages = {
            "aliases": ["slashsync"]
        }
        self.dev = True
        self.perms = "bot.dev"
        self.default_perms = "guild.admin"

        global bot
        from humecord import bot

    async def sync_guild(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        try:
            guild_id = int(ctx.args.guildid)

        except:
            await resp.error(
                ctx.user,
                "Invalid args!",
                "Guild ID couldn't be converted to an integer."
            )
            return

        guild = bot.client.get_guild(guild_id)

        if guild is None:
            await resp.error(
                ctx.user,
                "Failed to sync tree!",
                "Guild ID could not be resolved."
            )
            return

        await resp.defer(thinking = True)

        try:
            cmd_count = await bot.commands.sync_to(guild, copy = ctx.args.copy)

        except Exception as e:
            debug.print_traceback("An error occured during command tree sync.")
            await debug.log_traceback("Command tree sync")
            await resp.error(
                ctx.user,
                "Failed to sync command tree.",
                "Check the debug channel and/or logs for information."
            )
            return

        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']}  Synced command tree successfully!",
                f"**{cmd_count}** commands were registered to guild {guild.name} (`{guild.id}`).",
                color = "success"
            )
        )

    async def sync_global(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['warning']}  Are you sure?",
                "This will sync the local slash command tree to all of Discord irreversibly.\n\nIt is **strongly** encouraged that you test all commands locally using `/sync guild [id]` before proceeding.\n\n**Press the button to confirm.**",
                color = "warning"
            ),
            view = await bot.interactions.create_view(
                [
                    await bot.interactions.create_button(
                        name = "confirm",
                        callback = self.confirm_sync,
                        label = "Confirm",
                        style = humecord.ButtonStyles.DANGER
                    ),
                    await bot.interactions.create_button(
                        name = "cancel",
                        callback = self.cancel_sync,
                        label = "Cancel",
                        style = humecord.ButtonStyles.GRAY
                    )
                ]
            )
        )

    async def confirm_sync(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        await resp.defer(thinking = True)

        try:
            cmd_count = await bot.commands.sync_global()

        except Exception as e:
            debug.print_traceback("An error occured during command tree sync.")
            await debug.log_traceback("Command tree sync")
            await resp.error(
                ctx.user,
                "Failed to sync command tree.",
                "Check the debug channel and/or logs for information."
            )
            return

        await resp.edit(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']}  Command tree synced successfully!",
                f"**{cmd_count}** commands were synced. Changes may take a while to propogate everywhere.",
                color = "success"
            ),
            view = None
        )

    async def cancel_sync(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        await resp.edit(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['error']}  Command sync cancelled.",
                color = "error"
            ),
            view = None
        )

    async def clear(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        try:
            guild_id = int(ctx.args.guildid)

        except:
            await resp.error(
                ctx.user,
                "Invalid args!",
                "Guild ID couldn't be converted to an integer."
            )
            return

        guild = bot.client.get_guild(guild_id)

        if guild is None:
            await resp.error(
                ctx.user,
                "Failed to sync tree!",
                "Guild ID could not be resolved."
            )
            return

        await bot.commands.clear_tree(guild)

        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']}  Cleared command tree successfully!",
                f"{guild.name} (`{guild.id}`) has been cleared.",
                color = "success"
            )
        )