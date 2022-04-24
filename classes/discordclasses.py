from typing import Union, Optional, Callable
import discord

import humecord
from humecord.utils import discordutils

class Button(discord.ui.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, interaction):
        await humecord.utils.errorhandler.discord_wrap(
            humecord.bot.interactions.recv_interaction(
                interaction
            ),
            interaction.message
        )

class Select(discord.ui.Select):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, interaction):
        await humecord.utils.errorhandler.discord_wrap(
            humecord.bot.interactions.recv_interaction(
                interaction
            ),
            interaction.message
        )

class TextInput(discord.ui.TextInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, interaction):
        await humecord.utils.errorhandler.discord_wrap(
            humecord.bot.interactions.recv_interaction(
                interaction
            ),
            interaction.message
        )

class Modal(discord.ui.Modal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_submit(
            self,
            interaction
        ):
        await humecord.utils.errorhandler.discord_wrap(
            humecord.bot.interactions.recv_interaction(
                interaction
            ),
            interaction.message
        )

class ResponseChannel:
    def __init__(
            self,
            type: str,
            channel: Union[discord.TextChannel, discord.DMChannel]
        ):

        self.type = type

        self.channel = channel

    async def send(self, *args):
        raise humecord.utils.exceptions.NotDefined(f"This function isn't defined for message type {self.type}.")

    async def edit(self, *args):
        raise humecord.utils.exceptions.NotDefined(f"This function isn't defined for message type {self.type}.")

    async def send_modal(self, *args):
        raise humecord.utils.exceptions.NotDefined(f"This function isn't defined for message type {self.type}.")

    async def embed(self, *args, **kwargs):
        await self.send(
            embed = discordutils.create_embed(
                *args,
                **kwargs
            )
        )

    async def error(self, *args, **kwargs):
        await self.send(
            embed = discordutils.error(
                *args,
                **kwargs
            )
        )

class ComponentResponseChannel(ResponseChannel):
    def __init__(self, interaction):
        self.interaction = interaction
        super().__init__("component", interaction.channel)

    async def send(self, *args, **kwargs):
        return await self.interaction.response.send_message(*args, **kwargs)

    async def edit(self, *args, **kwargs):
        return await self.interaction.response.edit_message(*args, **kwargs)

    async def send_modal(self, *args, **kwargs):
        return await self.interaction.response.send_modal(*args, **kwargs)

class MessageResponseChannel(ResponseChannel):
    def __init__(self, message):
        self.message = message
        super().__init__("message", message.channel)

    async def send(self, *args, **kwargs):
        return await self.message.channel.send(*args, **kwargs)

class ThreadResponseChannel(ResponseChannel):
    def __init__(self, message):
        self.channel = message.channel
        self.parent = self.channel.parent

    async def send(self, *args, **kwargs):
        return await self.channel.send(*args, **kwargs)