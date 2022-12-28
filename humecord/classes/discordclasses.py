from typing import Union, Optional, Callable
import discord
from enum import Enum

import humecord
from humecord.utils import (
    discordutils,
    exceptions
)

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

    async def send(self, *args, **kwargs):
        raise humecord.utils.exceptions.NotDefined(f"This function isn't available for message type {self.type}.")

    async def edit(self, *args, **kwargs):
        raise humecord.utils.exceptions.NotDefined(f"This function isn't available for message type {self.type}.")

    async def send_modal(self, *args, **kwargs):
        raise humecord.utils.exceptions.NotDefined(f"This function isn't available for message type {self.type}.")

    async def embed(self, *args, **kwargs):
        ext_kw = {}
        if "ephemeral" in kwargs:
            kwargs = {x: y for x, y, in kwargs.items() if x != "ephemeral"}
            ext_kw = {"ephemeral": True}

        await self.send(
            embed = discordutils.create_embed(
                *args,
                **kwargs
            ),
            **ext_kw
        )

    async def error(self, *args, **kwargs):
        ext_kw = {}
        if "ephemeral" in kwargs:
            kwargs = {x: y for x, y, in kwargs.items() if x != "ephemeral"}
            ext_kw = {"ephemeral": True}

        await self.send(
            embed = discordutils.error(
                *args,
                **kwargs
            ),
            **ext_kw
        )

    async def defer(self, *args):
        raise humecord.utils.exceptions.NotDefined(f"This function isn't available for message type {self.type}.")

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
        self.initial_action = False
        self.message = message
        super().__init__("message", message.channel)

    async def send(self, *args, **kwargs):
        if "ephemeral" in kwargs:
            kwargs = {x: y for x, y, in kwargs.items() if x != "ephemeral"}
                
        self.sent_msg = await self.message.channel.send(*args, **kwargs)
        self.initial_action = True
        return self.sent_msg

    async def edit(self, *args, **kwargs):
        if self.initial_action:
            await self.sent_msg.edit(*args, **kwargs)

        else:
            await self.send(*args, **kwargs)

class ThreadResponseChannel(ResponseChannel):
    def __init__(self, message):
        self.channel = message.channel
        self.parent = self.channel.parent

    async def send(self, *args, **kwargs):
        return await self.channel.send(*args, **kwargs)

class InteractionResponseChannel(ResponseChannel):
    def __init__(self, interaction):
        self.interaction = interaction
        self.response = interaction.response
        self.followup = interaction.followup
        self.initial_action = False

        super().__init__("interaction", None)

    async def send(self, *args, **kwargs):
        if not self.initial_action:
            await self.response.send_message(*args, **kwargs)
            self.initial_action = True

        else:
            # Reply using the followup instead
            await self.followup.send(*args, **kwargs)

    async def edit(self, *args, **kwargs):
        if self.initial_action:
            await self.interaction.edit_original_response(*args, **kwargs)

        else:
            await self.response.send_message(*args, **kwargs)
            self.initial_action = True


class Context:
    def __init__(self, **kwargs) -> None:
        for name, val in kwargs.items():
            setattr(self, name, val)

class Args:
    def __init__(self, **kwargs) -> None:
        self._arg_dir = []

        for name, val in kwargs.items():
            setattr(self, name, val)
            self._arg_dir.append(name)

    def exists(self, key: str) -> bool:
        return key in self._arg_dir