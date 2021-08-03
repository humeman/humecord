import time
import discord
import asyncio
import traceback

from typing import Optional

from humecord.utils import exceptions
import humecord


class Interactions:
    def __init__(
            self
        ):

        """
        Constructs an Interactions handler.

        This accepts incoming interactions, like slash commands
        and components, and forwards them to wherever they're
        supposed to go.
        """

        self.components = {}

    def register_component(
            self,
            _type: str,
            _id: str,
            callback,
            author: Optional[int]
        ):

        # Format the id
        try:
            mid, cid = _id.split(".", 1)
            mid = int(mid)

        except:
            raise exceptions.InvalidComponent(f"ID must be formatted as: [message ID].[custom ID]")

        # Append it
        if mid not in self.components:
            self.components[mid] = {
                "generated": int(time.time()),
                "interactions": {}
            }

        if cid in self.components[mid]:
            raise exceptions.InvalidComponent(f"ID {cid} is already registered for this message")

        self.components[mid]["interactions"][cid] = {
            "callback": callback,
            "author": author,
            "type": _type
        }

    def remove_expired(
            self
        ):

        remove = []
        for message_id, details in self.components.items():
            if details["generated"] < int(time.time()) - humecord.bot.config.component_expire_time:
                remove.append(message_id)

        for mid in remove:
            del self.components[mid]

    async def recv_interaction(
            self,
            interaction
        ):

        if interaction.type == discord.enums.InteractionType.component:
            # Forward it to the callback

            # First - find message
            int_message = interaction.message

            # Find ID
            cid = None
            if "data" in dir(interaction):
                if "custom_id" in interaction.data:
                    mid, cid = interaction.data["custom_id"].split(".", 1)

            if cid is None:
                humecord.utils.logger.log("int", "Incoming component interaction has an invalid ID. Skipping.")
                await interaction.response.send_message(
                    embed = humecord.utils.discordutils.error(
                        None,
                        "Couldn't respond to interaction!",
                        "This interaction's ID doesn't seem to be properly defined. Try running the command again."
                    )
                )
                return

            mid = int(mid)

            interaction_data = self.components[mid]["interactions"][cid]

            humecord.utils.logger.log("int", f"Dispatching interaction ID {str(hex(mid)).replace('0x', '')}.{cid}", bold = True)

            # Get user
            user = await humecord.bot.api.get(
                "users",
                "user",
                {
                    "id": interaction.user.id,
                    "autocreate": True
                }
            )

            # Check if banned
            if user["botban"] is not None:
                if user["botban"]["endsat"] > time.time():
                    humecord.utils.logger.log_step(f"User {interaction.user} ({interaction.user.id}) is botbanned, skipping", "red")
                    return

            # Get message
            try:
                message = await interaction.channel.fetch_message(mid)

                if not message:
                    raise Exception

            except:
                humecord.utils.logger.log_step("Original message not found - disregarding", "blue")
                await interaction.response.send_message(
                    embed = humecord.utils.discordutils.error(
                        None,
                        "Couldn't respond to interaction!",
                        "Original message could not be found. Was it deleted?"
                    )
                )
                return

            if mid not in self.components:
                humecord.utils.logger.log_step("Component not found in component store - disregarding", "blue")
                await interaction.response.send_message(
                    embed = humecord.utils.discordutils.error(
                        message.author,
                        "Couldn't respond to interaction!",
                        "Button presses expire after 60 minutes to save resources. If this error occured but you responded within this time period, please tell me and try again."
                    )
                )
                return

            if interaction_data["author"] is not None:
                if interaction_data["author"] != interaction.user.id:
                    try:
                        await interaction.message.channel.send(
                            embed = humecord.utils.discordutils.error(
                                interaction.user,
                                "Can't respond to interaction!",
                                f"I can only accept responses from the original sender, <@{interaction_data['author']}>."
                            )
                        )

                    except:
                        pass

                    return

            if cid is None:
                humecord.utils.logger.log_step("Component ID not registered in component store - disregarding", "blue")
                await interaction.response.send_message(
                    embed = humecord.utils.discordutils.error(
                        message.author,
                        "Couldn't respond to interaction!",
                        "The component you pressed isn't registered in the interaction handler. Did it expire?"
                    )
                )
                return
            
            # Create ResponseChannel
            resp = humecord.classes.discordclasses.ComponentResponseChannel(
                interaction
            )

            # Get GDB
            gdb = await humecord.bot.api.get(humecord.bot.config.self_api, "guild", {"id": message.guild.id})

            # Generate PDB
            pdb = {}

            for key in humecord.bot.config.preferred_gdb:
                pdb[key] = gdb[key]

            # Get type
            comp_type = interaction_data["type"]

            ext_args = []

            if comp_type == "select":
                # Append selection
                ext_args = [interaction.data["values"]]

            humecord.utils.logger.log_long(
                f"""Type:           components.button
                Component:      {cid}
                Guild:          {message.guild.id} ({message.guild.name})
                Channel:        {message.channel.id} ({message.channel.name})
                User:           {message.author.id} ({message.author.name}#{message.author.discriminator})""".replace("                ", ""),
                "blue",
                extra_line = False
            )

            # Call
            humecord.utils.logger.log_step("Creating callback task...", "blue")
            task = humecord.bot.client.loop.create_task(
                humecord.utils.errorhandler.discord_wrap(
                    self.components[mid]["interactions"][cid]["callback"](message, resp, [], user, gdb, None, pdb, *ext_args),
                    message
                )
            )

            while not task.done():
                await asyncio.sleep(0.01) # While I wait for discord.py devs to allow me to disable auto-defer

            humecord.terminal.log(" ", True)



            
