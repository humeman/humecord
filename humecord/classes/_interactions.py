import time
import discord
import asyncio
import traceback
import json

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

        @humecord.event("on_interaction")
        async def on_perma_int(interaction):
            _id = None

            if interaction.type == discord.InteractionType.application_command:
                # Forward to the command receiver
                # update: nevermind
                #await humecord.bot.commands.call_command(interaction)
                return

            # Modals, buttons, etc all use this class's interaction handler
            else:
                if "data" in dir(interaction):
                    if "custom_id" in interaction.data:
                        _id = interaction.data["custom_id"]

                if _id is None:
                    return

                if _id.startswith("hcperma_"):
                    humecord.logger.log("interaction", "int", "Incoming perma interaction. Dispatching now.")
                    await self.recv_interaction(interaction, perma_override = True)
                    
                    try:
                        await interaction.response.defer()

                    except:
                        pass

        global bot
        from humecord import bot

    def register_component(
            self,
            _type: str,
            _id: str,
            callback: Optional[str],
            author: Optional[int],
            permanent: bool = False
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
            
    async def recv_interaction_old(
            self,
            interaction,
            perma_override = False
        ):

        humecord.terminal.log("interaction", True)

        if interaction.type in [discord.enums.InteractionType.component, discord.enums.InteractionType.modal_submit]:
            # Forward it to the callback

            # Find ID
            _id = None
            if "data" in dir(interaction):
                if "custom_id" in interaction.data:
                    _id = interaction.data["custom_id"]

            if _id is None:
                humecord.logger.log("interaction", "int", "Incoming component interaction has an invalid ID. Skipping.")
                await interaction.response.send_message(
                    embed = humecord.utils.discordutils.error(
                        None,
                        "Couldn't respond to interaction!",
                        "This interaction's ID doesn't seem to be properly defined. Try running the command again."
                    )
                )
                return

            # Get user
            udb = await humecord.bot.api.get(
                "users",
                "user",
                {
                    "id": interaction.user.id,
                    "autocreate": True
                }
            )

            if _id.startswith(f"hcperma_"):
                if not perma_override:
                    return

                perma = True
                perma_id = _id.split("_", 1)[1]
                cid = perma_id

                message = interaction.message
                duser = interaction.user

            else:
                perma = False
                mid, cid = interaction.data["custom_id"].split(".", 1)

                mid = int(mid)
                interaction_data = self.components[mid]["interactions"][cid]

            humecord.logger.log("interaction", "int", f"Dispatching interaction ID {_id}", bold = True)

            # Check if banned
            if udb["botban"] is not None:
                if udb["botban"]["endsat"] > time.time():
                    humecord.logger.log_step("interaction", "int", f"User {interaction.user} ({interaction.user.id}) is botbanned, skipping")
                    return

            # Get message
            if not perma:
                try:
                    message = await interaction.channel.fetch_message(mid)

                    if not message:
                        raise Exception

                except:
                    humecord.logger.log_step("interaction", "int", "Original message not found - disregarding")
                    await interaction.response.send_message(
                        embed = humecord.utils.discordutils.error(
                            None,
                            "Couldn't respond to interaction!",
                            "Original message could not be found. Was it deleted?"
                        ),
                        ephemeral = True
                    )
                    return

                if mid not in self.components:
                    humecord.logger.log_step("interaction", "int", "Component not found in component store - disregarding")
                    await interaction.response.send_message(
                        embed = humecord.utils.discordutils.error(
                            message.author,
                            "Couldn't respond to interaction!",
                            "Button presses expire after 60 minutes to save resources. If this error occured but you responded within this time period, please tell me and try again."
                        ),
                        ephemeral = True
                    )
                    return

                if interaction_data["author"] is not None:
                    if interaction_data["author"] != interaction.user.id:
                        try:
                            await interaction.response.send_message(
                                embed = humecord.utils.discordutils.error(
                                    interaction.user,
                                    "Can't respond to interaction!",
                                    f"I can only accept responses from the original sender, <@{interaction_data['author']}>."
                                ),
                                ephemeral = True
                            )

                        except:
                            pass

                        return

                if cid is None:
                    humecord.logger.log_step("interaction", "int", "Component ID not registered in component store - disregarding")
                    await interaction.response.send_message(
                        embed = humecord.utils.discordutils.error(
                            message.author,
                            "Couldn't respond to interaction!",
                            "The component you pressed isn't registered in the interaction handler. Did it expire?"
                        ),
                        ephemeral = True
                    )
                    return
            
            # Create ResponseChannel
            resp = humecord.classes.discordclasses.ComponentResponseChannel(
                interaction
            )

            # Get GDB
            gdb = await humecord.bot.api.get(humecord.bot.config.self_api, "guild", {"id": interaction.message.guild.id})

            # Get type
            kw = {}
            if not perma:
                comp_type = interaction_data["type"]

                if comp_type == "select":
                    # Append selection
                    kw["values"] = interaction.data["values"]

                elif comp_type == "modal":
                    kw["modal_args"] = {}
                    for mcomponent in interaction.data["components"]:
                        mcomponent = mcomponent["components"][0]
                        kw["modal_args"][mcomponent["custom_id"].split(".", 1)[1]] = mcomponent["value"]

            # Create Args
            args = humecord.classes.discordclasses.Args()

            # Create Context class
            ctx = humecord.classes.discordclasses.Context(
                {
                    "type": humecord.classes.discordclasses.ContextTypes.COMPONENT,
                    "resp": resp,
                    "interaction": interaction,
                    "channel": interaction.channel,
                    "gdb": gdb,
                    "udb": udb,
                    "component": cid,
                    **kw
                }
            )

            humecord.logger.log_long(
                "interaction",
                "int",
                [
                    f"Type:           components.{comp_type}",
                    f"Component:      {cid}",
                    f"Channel:        {message.channel.id} ({message.channel.name})",
                    f"User:           {message.author.id} ({message.author.name}#{message.author.discriminator})"
                ],
                extra_line = False
            )

            # Call   
            humecord.logger.log_step("interaction", "int", "Creating callback task...")
            if perma:
                task = humecord.bot.client.loop.create_task(
                    humecord.bot.events.call(
                        "hc_on_perma_interaction",
                        [perma_id, resp, ctx]
                    )
                )

            else:
                task = humecord.bot.client.loop.create_task(
                    humecord.utils.errorhandler.wrap(
                        self.components[mid]["interactions"][cid]["callback"](resp, ctx)
                    )
                )

            while not task.done():
                await asyncio.sleep(0.01) # While I wait for discord.py devs to allow me to disable auto-defer

            humecord.terminal.log(" ", True)



            
