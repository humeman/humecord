import humecord

from humecord.utils import (
    discordutils,
    miscutils
)

import discord

class OnMessageEvent:
    def __init__(
            self
        ):
        self.name = "hh_on_message"
        self.description = "Internal Humecord hooks for Discord's on_message event."

        self.event = "on_message"

        self.functions = {
            "check_ping": {
                "function": self.check_ping,
                "priority": 5
            },
            "check_reply": {
                "function": self.check_reply,
                "priority": 5
            },
            "check_dm": {
                "function": self.check_dm,
                "priority": 5
            },
            "run_command": {
                "function": self.run_command,
                "priority": 5
            },
            "check_debug_console": {
                "function": self.check_debug_console,
                "priority": 5
            }
        }

        global bot
        from humecord import bot

    async def check_bot(
            self,
            message
        ):

        if message.author.id == bot.client.user.id:
            return False

        if message.author.bot:
            return False

    async def check_blocked(
            self,
            message
        ):
        if message.author.id in bot.files.files["__users__.json"]["blocked"]:
            return

    async def check_ping(
            self,
            message
        ):
        if not message.author.bot and message.author.id != humecord.bot.client.user.id:
            if message.content.startswith("<@"):
                if message.content in [f"<@{humecord.bot.client.user.id}>", f"<@!{humecord.bot.client.user.id}>"]:
                    # Create a resp instance
                    resp = humecord.classes.discordclasses.MessageResponseChannel(
                        message
                    )

                    # Get GDB
                    if humecord.bot.config.use_api:
                        gdb = await humecord.bot.api.get(humecord.bot.config.self_api, "guild", {"id": message.guild.id, "autocreate": True})

                    else:
                        gdb = await humecord.bot.db.get("guild", {"id": message.guild.id})

                    # Generate pdb
                    pdb = {}
                    for key in humecord.bot.config.preferred_gdb:
                        pdb[key] = gdb[key]

                    await humecord.bot.commands.get_command("info", "about").run(
                        message,
                        resp,
                        [],
                        {},
                        None,
                        None,
                        pdb
                    )

    async def check_reply(
            self,
            message
        ):
        await humecord.bot.replies.read_reply(
            message
        )

    async def check_dm(
            self,
            message
        ):
        if type(message.channel) == discord.DMChannel and message.author.id != humecord.bot.client.user.id:
            # Send the
            msg_kw = {}
            kw = {}
            if len(message.attachments) > 0:
                for i, attachment in enumerate(message.attachments):
                    extra = "\n"
                    name = attachment.filename.lower()

                    embedded = False
                    for mtype in humecord.bot.config.embeddable_media:
                        if name.endswith(f".{mtype}"):
                            # Embed
                            kw["image"] = attachment.url
                            embedded = True

                    if not embedded:
                        if "content" not in msg_kw:
                            msg_kw["content"] = ""
                            extra = ""

                        msg_kw["content"] += f"{extra}{attachment.url}"

                    if "fields" not in kw:
                        kw["fields"] = []

                    kw["fields"].append(
                        {
                            "name": f"→ Attachment {i + 1}",
                            "value": f"• **Filename**: `{attachment.filename}`\n• **URL**: `{attachment.url}`\n• **Size**: `{miscutils.get_size(attachment.size, True)}`"
                        }
                    )
                    

            msg_long = len(message.content) > 1900

            """
            if " " not in message.content:
                if message.content.startswith("https://") or message.content.startswith("http://"):
                    extra = "\n"
                    if "content" not in msg_kw:
                        msg_kw["content"] = ""
                        extra = ""

                    msg_kw["content"] += f"{extra}{message.content}"
            """

            if msg_long:
                # Attach file
                with open("data/msg_tmp.txt", "w+") as f:
                    f.write(message.content)

                msg_kw["file"] = discord.File("data/msg_tmp.txt", "message.txt")

            await humecord.bot.debug_channel.send(
                embed = discordutils.create_embed(
                    description = f"{message.content[:1900]}{'**...**' if msg_long else ''}",
                    author = message.author,
                    footer = f"ID: {message.author.id}",
                    **kw
                ),
                **msg_kw
            )

            # Update mem storage
            humecord.bot.mem_storage["reply"] = message.author.id

            return False

    async def run_command(
            self,
            message
        ):
        if not message.author.bot and message.author.id != humecord.bot.client.user.id:
            await humecord.bot.commands.run(message)

    async def check_debug_console(
            self,
            message
        ):
        if humecord.bot.debug_console.channel and message.author.id != humecord.bot.client.user.id:
            if message.channel.id == humecord.bot.debug_console.channel.id:
                await humecord.bot.debug_console.execute(message)