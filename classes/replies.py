import time
import discord

import humecord
from humecord.utils import (
    discordutils,
    exceptions
)

class Replies:
    def __init__(
            self
        ):
        """
        Constructs a ReplyHandler.
        This allows you to easily catch replies to 
            messages, and run a callback when it
            happens.
        """

        self.messages = {}

    def add_callback(
            self,
            message_id: int,
            author_id: int,
            callback,
            data: dict = {},
            delete_after: bool = True
        ):
        """
        Registers a reply callback.

        Parameters:
            message_id: int
            author_id: int
            callback: Callable (usual command args + data)
            data: dict - Data returned on callback
        """

        self.messages[message_id] = {
            "message": message_id,
            "author": author_id,
            "callback": callback,
            "data": data,
            "created": int(time.time()),
            "delete_after": delete_after
        }

    async def read_reply(
            self,
            message
        ):

        # Check if message is reply
        if message.reference is not None and message.type == discord.MessageType.reply:
            if message.author.id == humecord.bot.client.user.id:
                return

            # Get reference
            if message.reference.resolved is not None:
                replied_to = message.reference.resolved
                replied_id = message.reference.message_id

            else:
                replied_to = None
                replied_id = message.reference.message_id

            # Check if in refs
            if replied_id not in self.messages:
                return

            message_data = self.messages[replied_id]

            # Get user
            user = await humecord.bot.api.get(
                "users",
                "user",
                {
                    "id": message.author.id,
                    "autocreate": True
                }
            )

            # Check if banned
            if user["botban"] is not None:
                if user["botban"]["endsat"] > time.time():
                    humecord.utils.logger.log_step(f"User {message.author} ({message.author.id}) is botbanned, skipping", "red")
                    return

            # Check if user is right
            if message.author.id != message_data["author"]:
                await message.reply(
                    embed = discordutils.error(
                        message.author,
                        "Can't run reply command!",
                        f"I can only accept responses from the original sender, <@{message_data['author']}>."
                    )
                )

                return

            # Create ResponseChannel
            resp = humecord.classes.discordclasses.MessageResponseChannel(
                message
            )

            # Get GDB
            gdb = await humecord.bot.api.get(humecord.bot.config.self_api, "guild", {"id": message.guild.id})

            # Generate PDB
            pdb = {}

            for key in humecord.bot.config.preferred_gdb:
                pdb[key] = gdb[key]

            # Call the function
            mid = int(message.id)

            humecord.utils.logger.log("cmd", f"Dispatching reply ID {str(hex(mid)).replace('0x', '')}", bold = True)

            humecord.utils.logger.log_long(
                f"""Type:           message.reply
                Message:        {mid}
                Replied to:     {replied_id}
                Guild:          {message.guild.id} ({message.guild.name})
                Channel:        {message.channel.id} ({message.channel.name})
                User:           {message.author.id} ({message.author.name}#{message.author.discriminator})""".replace("                ", ""),
                "blue",
                extra_line = False
            )

            humecord.utils.logger.log_step("Creating callback task...", "blue")
            task = humecord.bot.client.loop.create_task(
                humecord.utils.errorhandler.discord_wrap(
                    message_data["callback"](message, resp, message.content.split(" "), user, gdb, None, pdb, message_data["data"]),
                    message
                )
            )
            
            # Delete it
            if message_data["delete_after"]:
                del self.messages[replied_id]


            