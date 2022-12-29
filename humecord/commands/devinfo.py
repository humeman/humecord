"""
/devinfo: humecord base commands

Gets dev info about various things.
"""

from typing import Optional, Union

import discord
import time

import humecord

from humecord.classes import (
    discordclasses
)

from humecord.utils import (
    dateutils,
    debug,
    discordutils,
    miscutils
)

class DevInfoCommand(humecord.Command):
    def __init__(
            self
        ) -> None:
        self.name = "devinfo"
        self.description = "Gets dev info about various things."
        self.command_tree = {
            "user %user%": self.user,
            "guild %guildid%": self.guild,
            "stats": self.stats
        }
        self.args = {
            "user": {
                "type": "user",
                "required": False,
                "description": "User to retrieve."
            },
            "guildid": {
                "type": "str",
                "required": True,
                "description": "Guild ID to retrieve."
            }
        }
        self.subcommand_details = {
            "user": {
                "description": "Gets information about a user."
            },
            "guild": {
                "description": "Gets information about a guild."
            },
            "stats": {
                "description": "Gets general stats."
            }
        }
        self.messages = {}
        self.dev = True
        self.perms = "bot.mod"
        self.default_perms = "guild.admin"

        global bot
        from humecord import bot

    async def user(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:

        members = []
        for guild in bot.client.guilds:
            member = guild.get_member(ctx.args.user.id)

            if member is not None:
                members.append(member)

        if len(members) == 0:
            await resp.error(
                ctx.user,
                f"Search failed!",
                f"No members located for `{str(ctx.args.user.id)}`."
            )
            return
        
        comp = []

        for member in members:
            comp.append(
                {
                    "name": f"→ {member.guild.name} ({member.guild.id})",
                    "value": "\n".join([
                        f"• Joined: `{dateutils.get_timestamp(member.joined_at)}`",
                        f"• Name: `{discordutils.get_member_descriptor(member)}`",
                        f"• Role: `{member.top_role.name} ({member.top_role.id})`"
                    ])
                }
            )

        await resp.embed(
            f"{ctx.args.user}'s shared guilds ({len(comp)})",
            fields = comp,
            footer = f"ID: {ctx.args.user.id}"
        )

    async def guild(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:

        try:
            gid = int(ctx.args.guildid)

        except:
            await resp.error(
                ctx.user,
                "Invalid arguments!",
                "Guild ID must be an integer."
            )
            return

        fields = []

        guild = bot.client.get_guild(gid)

        if guild is not None:
            fields.append(
                {
                    "name": "→ Guild info",
                    "value": "\n".join([
                        f"• **Name**: `{guild.name}`",
                        f"• **Members**: `{len(guild.members)}`",
                        f"• **Joined on**: `{dateutils.get_timestamp(guild.me.joined_at)}`"
                    ])
                }
            )

        # Internal info
        try:
            await bot.api.get(
                bot.config.self_api,
                "guild",
                {
                    "id": gid
                }
            )

        except:
            pass

        else:
            fields.append(
                {
                    "name": "→ Internal info",
                    "value": "\n".join([
                        f"• GDB exists: I've (probably) been in this guild before"
                    ])
                }
            )

        await resp.embed(
            f"Guild info: {gid}",
            fields = fields,
            footer = f"ID: {gid}"
        )

    async def stats(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:

        stats = await bot.api.get(
            "stats",
            "bot",
            {
                "bot": bot.config.self_api
            }
        )

        await resp.embed(
            "General stats",
            fields = [
                {
                    "name": "→ Guilds",
                    "value": f"`{len(bot.client.guilds)}`"
                },
                {
                    "name": "→ Uptime",
                    "value": f"• **Runtime**: `{miscutils.get_duration(time.time() - humecord.bot.timer)}`\n• **Session started**: `{dateutils.get_timestamp(humecord.bot.timer)}`"
                },
                {
                    "name": "→ Commands",
                    "value": f"• **Today**: `{miscutils.friendly_number(stats['commands']['day']['count'])}`\n• **Total**: `{miscutils.friendly_number(stats['commands']['total'])}`"
                }
            ]
        )
