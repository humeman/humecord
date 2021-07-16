import discord
import humecord
from humecord.utils import (
    discordutils,
    miscutils,
    components,
    dateutils,
    miscutils,
    hcutils,
    debug
)

import traceback
import asyncio
import time
import random
import aiohttp
import aiofiles

class ProfileCommand:
    def __init__(
            self
        ):

        self.name = "profile"

        self.description = "Manages my Discord profile."

        self.aliases = []

        self.permission = "bot.dev"
        
        self.permission_hide = True

        self.subcommands = {
            "picture": {
                "function": self.picture,
                "description": "Changes my profile picture.",
                "syntax": "(url)"
            },
            "username": {
                "function": self.username,
                "description": "Changes my username.",
                "syntax": "[username]"
            },
            "activity": {
                "function": lambda *args: self.activity_visibility(*args, "activity", "activities"),
                "description": "Changes my activity.",
                "syntax": "[activity]"
            },
            "visibility": {
                "function": lambda *args: self.activity_visibility(*args, "visibility", "visibilities"),
                "description": "Changes my visibility.",
                "syntax": "[visibility]"
            },
            "status": {
                "function": self.status,
                "description": "Changes my status.",
                "syntax": "[status]"
            }
        }

        global bot
        from humecord import bot

    async def picture(
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
            if len(message.attachments) == 0:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid syntax!",
                        "Attach an image, or send the URL to an image that I should change my profile picture to."
                    )
                )
                return

            else:
                url = message.attachments[0]

        else:
            url = args[2]

            filename = url.split("?")[0].strip()
            
            if filename.split(".")[-1].lower() not in ["png", "jpeg", "jpg"]:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid profile picture!",
                        "Specify a PNG or JPEG image."
                    )
                )
                return

            if not filename.lower().startswith("https://media.discordapp.net/attachments/"): 
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid profile picture!",
                        "I can only accept images from Discord's CDN. Copy the image and attach it as a file instead."
                    )
                )
                return

        try:
            content = await discordutils.download_file(url)

        except Exception as e:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Couldn't download profile picture!",
                    f"Download failed: `{e}`"
                )
            )
            return

        try:
            task = bot.client.loop.create_task(
                bot.client.user.edit(
                    avatar = content
                )
            )

            count = 0
            while not task.done() and count < 50:
                await asyncio.sleep(0.1)
                count += 1

            if count >= 50:
                task.cancel()
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Couldn't upload profile picture!",
                        f"Task timed out after 5 seconds. Am I being rate limited?"
                    )
                )
                return

            # Check if failed
            if task.exception() is not None:
                raise task.exception()

        except:
            debug.print_traceback()
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Couldn't upload profile picture!",
                    "Upload raised an error."
                )
            )
            return

        await resp.send(
            embed = discordutils.create_embed(
                title = f"{bot.config.lang['emoji']['success']}  Changed profile picture!",
                image = bot.client.user.avatar.url,
                color = "success"
            )
        )

    async def username(
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
                    "Specify a new username."
                )
            )
            return

        username = " ".join(args[2:])

        if len(username) > 32 or len(username) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid username!",
                    "Usernames must be between 3 and 32 characters in length."
                )
            )
            return

        try:
            await bot.client.user.edit(
                username = username
            )

        except:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Couldn't change username!",
                    "Task raised an error."
                )
            )
            return

        await resp.send(
            embed = discordutils.create_embed(
                title = f"{bot.config.lang['emoji']['success']}  Changed username!",
                description = f"My new username is: `{username}`",
                color = "success"
            )
        )

    async def update_status(
            self
        ):
        for loop in bot.loops.loops:
            if loop.name == "refresh_status":
                await loop.run()
                return True

    async def activity_visibility(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb,
            cat,
            cat_full
        ):
        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    f"Specify a new {cat}."
                )
            )
            return

        new = args[2].lower()

        if new not in eval(f"bot.config.{cat_full}"):
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    f"Invalid {cat}!",
                    f"Valid {cat_full} include: {', '.join([f'`{x}`' for x in eval(f'bot.config.{cat_full}')])}."
                )
            )
            return

        if cat == "activity":
            bot.files.files["__bot__.json"][cat]["type"] = new

        else:
            bot.files.files["__bot__.json"][cat] = new

        bot.files.write("__bot__.json")

        await self.update_status()

        await resp.send(
            embed = discordutils.create_embed(
                title = f"{bot.config.lang['emoji']['success']}  Changed {cat}!",
                description = f"My new {cat} is: `{new}`",
                color = "success"
            )
        )

    async def status(
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
                    f"Specify a new status (or `disable` to disable)."
                )
            )
            return

        status = " ".join(args[2:])

        if status.lower() in ["disable", "off", "none"]:
            status = None
            detail = "*Disabled*"

        else:
            if bot.files.files["__bot__.json"]["activity"]["type"] == "streaming":
                write_status = False
                # Gather details - game, url, twitch_name, platform
                if status.count("|") != 3:
                    await resp.send(
                        embed = discordutils.error(
                            message.author,
                            "Invalid status!",
                            f"Since your activity is set to `streaming`, you have to specify a game, url, twitch name, and platform, separated by `|`."
                        )
                    )
                    return

                game, url, name, platform = status.split("|", 3)

                for val in [game, url, name, platform]:
                    if len(val) > 128:
                        await resp.send(
                            embed = discordutils.error(
                                message.author,
                                "Invalid status!",
                                f"Statuses can't exceed 128 characters."
                            )
                        )

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
                    await resp.send(
                        embed = discordutils.error(
                            message.author,
                            "Invalid status!",
                            f"Statuses can't exceed 128 characters."
                        )
                    )

        # Write
        bot.files.files["__bot__.json"]["status"] = status
        bot.files.write("__bot__.json")

        await self.update_status()

        await resp.send(
            embed = discordutils.create_embed(
                title = f"{bot.config.lang['emoji']['success']}  Changed status!",
                description = f"My new status is: {detail}",
                color = "success"
            )
        )