from typing import Union, Optional, Callable
import discord
from enum import Enum

import humecord
from humecord.utils import (
    discordutils,
    exceptions
)

class ResponseChannel:
    def __init__(
            self
        ):

        self.type = humecord.RespTypes.NONE

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

    async def defer(self, *args, **kwargs):
        return

class MessageResponseChannel(ResponseChannel):
    def __init__(self, message):
        self.type = humecord.RespTypes.MESSAGE

        self.channel = message.channel
        self.initial_action = False
        self.message = message
        super().__init__()

    async def send(self, *args, **kwargs):
        if "ephemeral" in kwargs:
            kwargs = {x: y for x, y, in kwargs.items() if x != "ephemeral"}
                
        self.sent_msg = await self.channel.send(*args, **kwargs)
        self.initial_action = True
        return self.sent_msg

    async def edit(self, *args, **kwargs):
        if self.initial_action:
            await self.sent_msg.edit(*args, **kwargs)

        else:
            await self.send(*args, **kwargs)

class ThreadResponseChannel(ResponseChannel):
    def __init__(self, message):
        self.type = humecord.RespTypes.THREAD

        self.channel = message.channel
        self.parent = self.channel.parent

        super().__init__()

    async def send(self, *args, **kwargs):
        return await self.channel.send(*args, **kwargs)

class InteractionResponseChannel(ResponseChannel):
    def __init__(self, interaction, is_component: bool = False):
        self.type = humecord.RespTypes.INTERACTION

        self.interaction = interaction
        self.response = interaction.response
        self.followup = interaction.followup
        self.initial_action = is_component
        self.is_component = is_component
        self.deferred = False

        super().__init__()

    async def send(self, *args, **kwargs):
        if (not self.initial_action) and (not self.deferred):
            await self.response.send_message(*args, **kwargs)
            self.initial_action = True

        else:
            # Reply using the followup instead
            if "view" in kwargs:
                if kwargs["view"] is None:
                    del kwargs["view"]

            self.msg = await self.followup.send(*args, **kwargs)

    async def edit(self, *args, **kwargs):
        if self.initial_action and (not self.deferred):
            await self.response.edit_message(*args, **kwargs)

        elif self.deferred:
            if "view" in kwargs:
                if kwargs["view"] is None:
                    del kwargs["view"]

            await self.followup.send(*args, **kwargs)

        else:
            self.msg = await self.response.send_message(*args, **kwargs)
            self.initial_action = True

    async def send_modal(self, *args, **kwargs):
        return await self.interaction.response.send_modal(*args, **kwargs)

    async def defer(self, *args, **kwargs):
        await self.response.defer(*args, **kwargs)
        self.deferred = True


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