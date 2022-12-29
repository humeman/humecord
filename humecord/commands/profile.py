"""
/profile: humecord base commands

Manages the bot's profile.
"""

import asyncio
from typing import Optional

import time

import discord

import humecord

from humecord.classes import (
    discordclasses
)

from humecord.utils import (
    debug,
    discordutils,
    dateutils
)

class ProfileCommand(humecord.Command):
    def __init__(
            self
        ) -> None:
        self.name = "profile"
        self.description = "Manages the bot's profile."
        self.command_tree = {
            "picture %attachment%": self.picture,
            "username %username%": self.username,
            "activity %activity%": self.activity,
            "visibility %visibility%": self.visibility,
            "status %status%": self.status
        }
        self.args = {
            "attachment": {
                "type": "attachment",
                "required": False,
                "description": "My new profile picture."
            },
            "username": {
                "type": "str",
                "required": True,
                "description": "My new username."
            },
            "activity": {
                "type": "str",
                "required": True,
                "description": "My new activity type.",
                "choices": list(humecord.ACTIVITIES)
            },
            "visibility": {
                "type": "str",
                "required": True,
                "description": "My new visibility.",
                "choices": list(humecord.VISIBILITIES)
            },
            "status": {
                "type": "str",
                "required": True,
                "description": "My new status text.",
                "choices": []
            }
        }
        self.subcommand_details = {
            "picture": {
                "description": "Changes my profile picture."
            },
            "username": {
                "description": "Changes my username."
            },
            "activity": {
                "description": "Changes my activity (playing, listening, etc)."
            },
            "visibility": {
                "description": "Changes my visibility (online, away, etc)."
            },
            "status": {
                "description": "Changes my status."
            }
        }
        self.messages = {}
        self.dev = True
        self.perms = "bot.dev"
        self.default_perms = "guild.admin"

        global bot
        from humecord import bot

    async def picture(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:

        if ctx.type == humecord.ContextTypes.SLASH:
            # Verify arg is in ctx.args
            if not ctx.args.exists("attachment"):
                await resp.error(
                    ctx.user,
                    "Missing arguments!",
                    "Add a new profile picture to the `attachment:` argument."
                )
                return

            attachment = ctx.args.attachment

        else:
            # Check message attachments
            if len(ctx.message.attachments) == 0:
                await resp.error(
                    ctx.user,
                    "Missing arguments!",
                    "Attach a new profile picture."
                )
                return

            attachment = ctx.message.attachments[0]

        try:
            content = await discordutils.download_file(attachment.url)

        except Exception as e:
            await resp.error(
                ctx.user,
                "Couldn't download profile picture!",
                f"Download failed: `{e}`"
            )
            return

        try:
            task = bot.client.loop.create_task(
                bot.client.user.edit(
                    avatar = content
                )
            )

            count = 0
            while not task.done() and count < 20:
                await asyncio.sleep(0.1)
                count += 1

            if count >= 20:
                task.cancel()
                await resp.error(
                    ctx.user,
                    "Couldn't upload profile picture!",
                    f"Task timed out after 2 seconds. Am I being rate limited?"
                )
                return

            # Check if failed
            if task.exception() is not None:
                raise task.exception()

        except:
            debug.print_traceback()
            await resp.error(
                ctx.user,
                "Couldn't upload profile picture!",
                "Upload raised an error."
            )
            return

        await resp.edit(
            embed = discordutils.create_embed(
                title = f"{bot.config.lang['emoji']['success']}  Changed profile picture!",
                image = bot.client.user.avatar.url,
                color = "success"
            )
        )

    async def username(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        username = ctx.args.username

        if len(username) > 32 or len(username) < 3:
            await resp.error(
                ctx.user,
                "Invalid username!",
                "Usernames must be between 3 and 32 characters in length."
            )
            return

        try:
            await bot.client.user.edit(
                username = username
            )

        except:
            await resp.error(
                ctx.user,
                "Couldn't change username!",
                "Task raised an error."
            )
            return

        await resp.embed(
            title = f"{bot.config.lang['emoji']['success']}  Changed username!",
            description = f"My new username is: `{username}`",
            color = "success"
        )

    async def activity(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        new = ctx.args.activity.lower()

        if new not in humecord.ACTIVITIES:
            await resp.error(
                ctx.user,
                "Invalid syntax!",
                f"Activity must be one of: {', '.join([f'`{x}`' for x in humecord.ACTIVITIES])}"
            )
            return

        bot.files.files["__bot__.json"]["activity"]["type"] = new

        await bot.loops.run_once("refresh_status")

        await resp.embed(
            title = f"{bot.config.lang['emoji']['success']}  Changed visibility!",
            description = f"My visibility is now `{new}`.",
            color = "success"
        )

    async def visibility(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        new = ctx.args.visibility.lower()

        if new not in humecord.VISIBILITIES:
            await resp.error(
                ctx.user,
                "Invalid syntax!",
                f"Visibility must be one of: {', '.join([f'`{x}`' for x in humecord.VISIBILITIES])}"
            )
            return

        bot.files.files["__bot__.json"]["visibility"] = new

        await bot.loops.run_once("refresh_status")

        await resp.embed(
            title = f"{bot.config.lang['emoji']['success']}  Changed visibility!",
            description = f"My visibility is now `{new}`.",
            color = "success"
        )

    async def status(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        status = ctx.args.status

        write = True
        if status.lower() in ["disable", "off", "none"]:
            status = None
            detail = "*Disabled*"

        else:
            if bot.files.files["__bot__.json"]["activity"]["type"] == "streaming":
                write = False
                # Gather details - game, url, twitch_name, platform
                if status.count("|") != 3:
                    await resp.error(
                        ctx.user,
                        "Invalid status!",
                        f"Since your activity is set to `streaming`, you have to specify a game, url, twitch name, and platform separated by `|`."
                    )
                    return

                game, url, name, platform = status.split("|", 3)

                for val in [game, url, name, platform]:
                    if len(val) > 128:
                        await resp.error(
                            ctx.user,
                            "Invalid status!",
                            f"Statuses can't exceed 128 characters."
                        )
                        return

                bot.files.files["__bot__.json"]["activity"]["streaming"].update(
                    {
                        "game": game.strip(),
                        "url": url.strip(),
                        "twitch_name": name.strip(),
                        "platform": platform.strip()
                    }
                )

                status = game.strip()

                detail = f"\n**Game:** `{game.strip()}`\n**URL:** `{url.strip()}`\n**Name:** `{name.strip()}`\n**Platform:** `{platform.strip()}`"

            else:
                detail = f"`{status}`"

                if len(status) > 128:
                    await resp.error(
                        ctx.user,
                        "Invalid status!",
                        f"Statuses can't exceed 128 characters."
                    )
                    return

        # Store changes
        if write:
            bot.files.files["__bot__.json"]["status"] = status
        
        bot.files.write("__bot__.json")

        await bot.loops.run_once("refresh_status")

        await resp.embed(
            title = f"{bot.config.lang['emoji']['success']}  Changed status!",
            description = f"My new status is: {detail}",
            color = "success"
        )