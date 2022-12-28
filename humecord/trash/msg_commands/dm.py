import discord
import humecord
from humecord.utils import (
    discordutils,
    miscutils,
    components,
    dateutils,
    miscutils,
    hcutils
)

import traceback
import asyncio
import time
import random
import aiohttp
import aiofiles

class DMCommand:
    def __init__(
            self
        ):

        self.name = "dm"

        self.description = "Sends DMs to users as the bot."

        self.aliases = []

        self.permission = "bot.dev"
        
        self.permission_hide = True

        self.subcommands = {
            "__default__": {
                "function": self.dm,
                "description": "Sends a DM."
            },
            "__syntax__": {
                "function": self.dm,
                "description": "Sends a DM.",
            },
            "reply": {
                "function": self.reply,
                "description": "Replies to the last user that DMed me.",
                "syntax": "[message]"
            }
        }

        self.shortcuts = {
            "reply": "dm reply"
        }

        global bot
        from humecord import bot

    async def dm(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):
        if len(args) < 2:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a user to DM."
                )
            )
            return

        if len(args) < 3:
            if len(message.attachments) == 0:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid syntax!",
                        "Specify a message to send, or attach something."
                    )
                ) 
                return

            else:
                msg_args = []

        else:
            msg_args = args[2:]

        await self.send_direct(
            args[1], # User ID
            message,
            resp,
            msg_args # Message
        )

    async def reply(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):

        if bot.mem_storage["reply"] is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Can't reply!",
                    "No one has messaged me recently."
                )
            )
            return

        # dev dm reply [message]

        # Get user ID
        if len(args) < 2:
            if len(message.attachments) == 0:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid syntax!",
                        "Specify a message to send, or attach something."
                    )
                ) 
                return

            else:
                msg_args = []

        else:
            msg_args = args[2:]

        await self.send_direct(
            bot.mem_storage["reply"], # User ID
            message,
            resp,
            msg_args # Message
        )

    async def send_direct(
            self,
            user_id,
            message,
            resp,
            msg_args
        ):

        # Get user
        try:
            user = discordutils.get_user(
                user_id,
                True,
                message
            )

        except Exception as e:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid user!",
                    str(e)
                )
            )
            return

        # Compile message
        # 1 - check if it's an embed
        if len(msg_args) != 0:
            if msg_args[0].lower() == "--embed":
                # No
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Not implemented yet!",
                        "This feature is disabled until I finish the embed parser."
                    )
                )
                return
                
                msg_args = msg_args[1:]

        # Check for attachments
        kw = {
            "content": ""
        }
        warn = []
        fields = []

        if len(message.attachments) > 0:
            # Try to attach

            attachment = message.attachments[0]

            attach_manual = False
            if attachment.size < 8000000:
                filename = f"data/tmp/{attachment.filename}"
                # Download & re-attach
                await resp.send(
                    embed = discordutils.create_embed(
                        "Downloading attachment...",
                        f"• **Name**: `{attachment.filename}`\n• **Size**: `{miscutils.get_size(attachment.size)}`",
                        color = "yellow"
                    )
                )

                async with aiohttp.ClientSession(headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.95 Safari/537.11"}) as session:
                    async with session.get(attachment.url) as resp_:
                        if resp_.status == 200:
                            async with aiofiles.open(filename, mode = "wb") as f:
                                await f.write(await resp_.read())

                            # Attach
                            kw["file"] = discord.File(filename, attachment.filename)

                            fields.append(
                                {
                                    "name": "→ Attachment",
                                    "value": f"• **Name**: `{attachment.filename}`\n• **Size**: `{miscutils.get_size(attachment.size)}`"
                                }
                            )

                        else:
                            attach_manual = True
                            

            else:
                attach_manual = True

            if attach_manual:
                # Just append the link to content
                kw["content"] = f"{attachment.url}\n"
                fields.append(
                    {
                        "name": "→ Attachment (not embedded)",
                        "value": f"• **URL**: {attachment.url}\n• **Name**: `{attachment.filename}`\n• **Size**: `{miscutils.get_size(attachment.size)}`"
                    }
                )


        kw["content"] += " ".join(msg_args)

        if len(kw["content"]) > 2000:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Can't send message!",
                    f"Your message was {len(kw['content'])} characters long, which exceeds the limit of 2000. Shorten it and try again."
                )
            )
            return

        # Send it
        try:
            await user.send(
                **kw
            )

        except:
            traceback.print_exc()
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Failed to send DM!",
                    "Either the user blocked me, or I don't share mutual servers with them."
                )
            )
            return

        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']}  Sent DM to {user.name}#{user.discriminator}!",
                description = f"→ **Content**:\n{kw['content'][:1900]}{'**...**' if len(kw['content']) > 1900 else ''}",
                fields = fields,
                color = "success"
            )
        )