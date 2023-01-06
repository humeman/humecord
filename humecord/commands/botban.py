"""
/botban: humecord base commands

Bans someone from using the bot.
"""

from typing import Optional

import time

import humecord

from humecord.classes import (
    discordclasses
)

from humecord.utils import (
    discordutils,
    dateutils
)

class BotBanCommand(humecord.Command):
    def __init__(
            self
        ) -> None:
        self.name = "botban"
        self.description = "Bans someone from using the bot."
        self.command_tree = {
            "add %user% %duration% %reason%": self.add,
            "remove %user% %note%": self.remove
        }
        self.args = {
            "user": {
                "type": "user",
                "required": True,
                "description": "Mentionable user to add botban to."
            },
            "duration": {
                "type": "str",
                "required": False,
                "description": "Duration to ban the user for (or 'perm')."
            },
            "reason": {
                "type": "str",
                "required": False,
                "description": "Reason for the ban. Displayed to the user."
            },
            "note": {
                "type": "str",
                "required": False,
                "description": "Reason for unbanning the user."
            }
        }
        self.subcommand_details = {
            "add": {
                "description": "Bans a user."
            },
            "remove": {
                "description": "Clear's a user's ban."
            }
        }
        self.messages = {}
        self.dev = True
        self.perms = "bot.mod"
        self.default_perms = "guild.admin"

        global bot
        from humecord import bot

    async def add(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:

        target = ctx.args.user.id
        target_user = ctx.args.user
        user_details = f"{target_user} "

        # Set up duration
        length = None
        if ctx.args.exists("duration"):
            if not ctx.args.duration.lower().startswith("perm"):
                try:
                    length = dateutils.parse_duration(ctx.args.duration)

                except:
                    await resp.error(
                        ctx.user,
                        "Invalid length!",
                        "Duration value is incorrectly formatted. Examples: `3d`, `4h`, `1w`, etc."
                    )
                    return

                duration = {
                    "duration": length,
                    "endsat": int(time.time()) + length
                }

        if length is None:
            duration = {
                "duration": None,
                "endsat": None
            }
        
        # Get reason
        if ctx.args.exists("reason"):
            reason = ctx.args.reason

        else:
            reason = "Not specified."

        if reason.endswith(" silent"):
            reason = reason.rsplit(" ", 1)[0]
            silent = True

        else:
            silent = False

        # Post botban data
        botban_data = {
            "active": True,
            "started": int(time.time()),
            "by": ctx.user.id,
            "reason": reason,
            **duration
        }

        # Post to API
        await bot.api.put(
            "users",
            "user",
            {
                "id": target,
                "db": {
                    "botban": botban_data
                }
            }
        )

        # Check for DM
        dm_sent = False
        dm_ext = ""
        if (not silent) and (target_user is not None):
            try:
                await target_user.send(
                    **(
                        await bot.messages.get(
                            ctx.gdb,
                            ["dev", "botban", "ban_dm"],
                            {
                                "duration": "Permanent" if length is None else dateutils.get_duration(int(length)),
                                "reason": reason,
                                "by": f"{ctx.user}"
                            },
                            {
                                "permanent": length is None
                            },
                            ext_placeholders = {
                                "user": target_user
                            }
                        )
                    )
                )
                dm_sent = True

            except Exception as e:
                dm_ext = f": `{e}`"

        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']} Botbanned {user_details}({target}).",
                description = f"**Duration:** `{'Permanent' if length is None else dateutils.get_duration(int(length))}`\n**Reason:** `{reason}`\n**User:** <@{target}> (`{target}`)\n\nDM {'not ' if not dm_sent else ''}sent{dm_ext}.",
                color = "success"
            )
        )
                

    async def remove(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:

        target = ctx.args.user.id
        target_user = ctx.args.user
        user_details = f"{target_user} "

        if ctx.args.exists("note"):
            note = ctx.args.note

        else:
            note = "Not specified."

        if note.endswith(" silent"):
            note = note.rsplit(" ", 1)[0]
            silent = True

        else:
            silent = False

        # Get a UDB
        udb = await bot.api.get(
            "users",
            "user",
            {
                "id": target,
                "autocreate": True
            }
        )

        is_banned = True
        if udb["botban"] is None:
            is_banned = False

        elif udb["botban"]["endsat"] is not None:
            if udb["botban"]["endsat"] < time.time():
                is_banned = False

        if not is_banned:
            await resp.error(
                ctx.user,
                "Can't unban this user!",
                "They're not currently banned."
            )
            return

        # Post to API
        await bot.api.put(
            "users",
            "user",
            {
                "id": target,
                "db": {
                    "botban": None,
                    "botban_history": [
                        *udb["botban_history"],
                        {
                            **udb["botban"],
                            "end_reason": note
                        }
                    ]
                }
            }
        )

        dm_sent = False
        dm_ext = ""
        if (not silent) and (target_user is not None):
            try:
                await target_user.send(
                    **(
                        await bot.messages.get(
                            ctx.gdb,
                            ["dev", "botban", "unban_dm"],
                            {
                                "note": note,
                                "by": f"{ctx.user}"
                            },
                            {
                                "note": note is not None
                            },
                            ext_placeholders = {
                                "user": target_user
                            }
                        )
                    )
                )

            except Exception as e:
                dm_ext = f": `{e}`"

        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']} Un-botbanned {user_details}({target}).",
                description = f"**Note:** {note if note is not None else 'Not specified'}\n**User:** <@{target}> (`{target}`)\n\nDM {'not ' if not dm_sent else ''}sent{dm_ext}.",
                color = "success"
            )
        )