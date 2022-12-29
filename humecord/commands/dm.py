"""
/dm: humecord base commands

Sends a direct message to someone.
"""

from typing import Optional, Union
import aiofiles
import aiohttp

import discord

import humecord

from humecord.classes import (
    discordclasses
)

from humecord.utils import (
    debug,
    discordutils,
    dateutils,
    miscutils
)

class DMCommand(humecord.Command):
    def __init__(
            self
        ) -> None:
        self.name = "dm"
        self.description = "Sends a direct message to someone."
        self.command_tree = {
            "send %user% %content%": self.send,
            "reply %content%": self.reply
        }
        self.args = {
            "user": {
                "type": "user",
                "required": False,
                "description": "Mentionable user to add botban to."
            },
            "content": {
                "type": "str",
                "required": False,
                "description": "Content/message text to send."
            },
            "attachment": {
                "type": "attachment",
                "required": False,
                "description": "Attachment to send."
            }
        }
        self.subcommand_details = {
            "send": {
                "description": "Sends a DM to any user."
            },
            "reply": {
                "description": "Replies to the previously received message."
            }
        }
        self.messages = {
            "shortcuts": {
                "reply": "dm reply"
            }
        }
        self.dev = True
        self.perms = "bot.mod"
        self.default_perms = "guild.admin"

        global bot
        from humecord import bot

    async def send(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        # Get user
        target = ctx.args.user

        # Get attachment. Could be a message argument or slash argument.
        if ctx.type == humecord.ContextTypes.SLASH:
            attachment = getattr(ctx.args, "attachment", None)

        elif ctx.type == humecord.ContextTypes.MESSAGE:
            if len(ctx.message.attachments) > 0:
                attachment = ctx.message.attachments[0]

            else:
                attachment = None

        else:
            attachment = None

        await self._send_message(
            resp,
            ctx,
            target,
            content = getattr(ctx.args, "content", None),
            attachment = attachment
        )

    async def reply(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ):

        # Look in the bot's message store for the previously sent message
        if bot.mem_storage["reply"] is None:
            await resp.error(
                ctx.user,
                "Can't reply!",
                "No one has messaged me recently."
            )
            return

        target = bot.client.get_user(bot.mem_storage["reply"])

        if target is None:
            await resp.error(
                ctx.user,
                "Can't reply!",
                "Couldn't get user. They might not share a server with me anymore."
            )
            return

        # Get attachment. Could be a message argument or slash argument.
        if ctx.type == humecord.ContextTypes.SLASH:
            attachment = getattr(ctx.args, "attachment", None)

        elif ctx.type == humecord.ContextTypes.MESSAGE:
            if len(ctx.message.attachments) > 0:
                attachment = ctx.message.attachments[0]

            else:
                attachment = None

        else:
            attachment = None

        await self._send_message(
            resp,
            ctx,
            target,
            content = getattr(ctx.args, "content", None),
            attachment = attachment
        )

    async def _send_message(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context,
            target: Union[discord.User, discord.Member],
            content: Optional[str],
            attachment: Optional[discord.Attachment]
        ) -> None:
        # Verify fields satisfied
        if (attachment is None) and (content is None):
            await resp.error(
                ctx.user,
                "Can't send message!",
                "Specify message content, an attachment, or both."
            )
            return

        # resp.send kwargs
        kw = {}
        fields = []

        content_prefix = ""
        if attachment is not None:
            manual_attach = False # Just links the content for Discord to embed if True. Used when we can't download/reupload the content.

            if attachment.size > 8000000:
                manual_attach = True

            else:
                # Try to download
                filename = f"data/tmp/{attachment.filename}"

                await resp.edit(
                    embed = discordutils.create_embed(
                        f"{bot.config.lang['emoji']['loading']}  Downloading attachment...",
                        f"• **Name**: `{attachment.filename}`\n• **Size**: `{miscutils.get_size(attachment.size)}`",
                        color = "blue"
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
                            manual_attach = True

            if manual_attach:
                content_prefix = f"{attachment.url}\n" # Preface message with it
                # Add some info
                fields.append(
                    {
                        "name": "→ Attachment (not embedded)",
                        "value": f"• **URL**: {attachment.url}\n• **Name**: `{attachment.filename}`\n• **Size**: `{miscutils.get_size(attachment.size)}`"
                    }
                )

        if content is not None:
            kw["content"] = f"{content_prefix}{content}"
            fields.append(
                {
                    "name": "→ Content",
                    "value": f"`{kw['content'][:1900]}{'**...**' if len(kw['content']) > 1900 else ''}`",
                }
            )

            if len(kw["content"]) > 2000:
                await resp.edit(
                    embed = discordutils.error(
                        ctx.user,
                        "Can't send message!",
                        f"Your message was {len(kw['content'])} characters long, which exceeds the limit of 2000. Shorten it and try again."
                    )
                )
                return

        try:
            await target.send(
                **kw
            )

        except:
            await resp.edit(
                embed = discordutils.error(
                    ctx.user,
                    "Failed to send DM!",
                    "Either the user blocked me, or I don't share mutual servers with them."
                )
            )
            return

        await resp.edit(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']}  Sent DM to {target} (`{target.id}`)!",
                fields = fields,
                color = "success"
            )
        )