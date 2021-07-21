import discord
import humecord
from humecord.utils import (
    discordutils,
    miscutils,
    components,
    dateutils,
    miscutils,
    debug
)

import traceback
import asyncio
import time
import random

class BotBanCommand:
    def __init__(
            self
        ):

        self.name = "botban"

        self.description = "Bans users from using the bot."

        self.aliases = ["bban"]

        self.permission = "bot.dev"
        
        self.permission_hide = True

        self.subcommands = {
            "add": {
                "function": self.add,
                "description": "Bot bans a user.",
                "syntax": "[user] (duration) (reason)"
            },
            "remove": {
                "function": self.remove,
                "description": "Un-bot bans a user.",
                "syntax": "[user] (note)"
            }
        }

        global bot
        from humecord import bot

    async def add(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):
        # Check args

        # botban add [user] [duration] [reason]
        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a user, and optionally, a duration and reason.\nAdditionally, end the message with `-s` to not send a DM to the user."
                )
            )
            return

        try:
            user = discordutils.get_user(args[2])

        except:
            for char in "<@!>":
                user = user.replace(char, "")

            try:
                uid = int(user)

            except:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid user!",
                        f"Mention a user, or paste their ID."
                    )
                )
                return

            else:
                details = str(uid)

                dm = False
        
        else:
            # Get user's details
            uid = int(user.id)

            details = f"{user.name}#{user.discriminator} ({user.id})"

            dm = True

        if args[-1].lower() == "-s":
            silent = True
            args = args[:-1]

        else:
            silent = False

        # Check if duration is defined
        reason = "Not specified"
        try:
            duration = dateutils.parse_duration(args[3])

            if duration == 0:
                raise

            dur_details = {
                "duration": duration,
                "endsat": int(time.time()) + duration,
            }

            if len(args) > 4:
                reason = " ".join(args[4:])

        except:
            duration = None
            dur_details = {
                "duration": None,
                "endsat": None
            }

            if len(args) > 3:
                reason = " ".join(args[3:])

        # Get user
        udb = await bot.api.get(
            "users",
            "user",
            {
                "id": uid,
                "autocreate": True
            }
        )

        # Update variables
        udb["botban"] = {
            "active": True,
            "started": int(time.time()),
            "by": message.author.id,
            "reason": reason,
            **dur_details
        }

        await bot.api.put(
            "users",
            "user",
            {
                "id": uid,
                "db": {
                    "botban": udb["botban"]
                }
            }
        )

        # Check if we should dm
        dm_sent = False
        ext = ""
        if dm and (not silent):
            try:
                await user.send(
                    **(
                        await bot.messages.get(
                            gdb,
                            ["dev", "botban", "ban_dm"],
                            {
                                "duration": "Permanent" if duration is None else dateutils.get_duration(int(duration)),
                                "reason": reason,
                                "by": f"{message.author.name}#{message.author.discriminator}"
                            },
                            {
                                "permanent": duration is None
                            },
                            ext_placeholders = {
                                "message": message,
                                "user": user
                            }
                        )
                    )
                )

            except Exception as e:
                debug.print_traceback()
                dm_sent = False
                ext = f": `{e}`"

            else:
                dm_sent = True

        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']} Botbanned {details}.",
                description = f"**Duration:** `{'Permanent' if duration is None else dateutils.get_duration(int(duration))}`\n**Reason:** `{reason}`\n**User:** <@{uid}> (`{uid}`)\n\nDM {'not ' if not dm_sent else ''}sent{ext}.",
                color = "success"
            )
        )

    async def remove(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):
        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a user.\nAdditionally, end the message with `-s` to not send a DM to the user."
                )
            )
            return

        try:
            user = discordutils.get_user(args[2])

        except:
            for char in "<@!>":
                user = user.replace(char, "")

            try:
                uid = int(user)

            except:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid user!",
                        f"Mention a user, or paste their ID."
                    )
                )
                return

            else:
                details = str(uid)

                dm = False
        
        else:
            # Get user's details
            uid = int(user.id)

            details = f"{user.name}#{user.discriminator} ({user.id})"

            dm = True

        if args[-1].lower() == "-s":
            silent = True
            args = args[:-1]

        else:
            silent = False

        if len(args) > 3:
            note = " ".join(args[3:])

        else:
            note = None

        # Get user
        udb = await bot.api.get(
            "users",
            "user",
            {
                "id": uid,
                "autocreate": True
            }
        )

        send = False
        invalid = False
        if udb["botban"] is None:
            invalid = True

        else:
            if udb["botban"]["endsat"] is not None:
                if udb["botban"]["endsat"] < int(time.time()):
                    udb["botban"] = None
                    send = True
                    invalid = True

        # Update variables
        if not invalid:
            udb["botban_history"].append(udb["botban"])
            udb["botban"] = None
            send = True

        if send:
            await bot.api.put(
                "users",
                "user",
                {
                    "id": uid,
                    "db": {
                        "botban": udb["botban"],
                        "botban_history": udb["botban_history"]
                    }
                }
            )

        if invalid:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Can't unban this user!",
                    "They're not banned."
                )
            )
            return

        # Check if we should dm
        dm_sent = False
        ext = ""
        if dm and (not silent):
            try:
                await user.send(
                    **(
                        await bot.messages.get(
                            gdb,
                            ["dev", "botban", "unban_dm"],
                            {
                                "note": note,
                                "by": f"{message.author.name}#{message.author.discriminator}"
                            },
                            {
                                "note": note is not None
                            },
                            ext_placeholders = {
                                "message": message,
                                "user": user
                            }
                        )
                    )
                )

                print(note is not None)

            except Exception as e:
                debug.print_traceback()
                dm_sent = False
                ext = f": `{e}`"

            else:
                dm_sent = True

        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']} Un-botbanned {details}.",
                description = f"**Note:** {note if note is not None else 'Not specified'}\n\nDM {'not ' if not dm_sent else ''}sent.",
                color = "success"
            )
        )