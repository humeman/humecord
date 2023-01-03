"""
humecord/classes/interactions/InteractionManager

Handles interactions for everything but application commands.
"""
import discord
import asyncio
import time
import uuid

from typing import Any, Optional, Union, List, Callable

import humecord

from humecord.utils import (
    exceptions,
    discordutils
)

from . import (
    discordclasses
)

class InteractionManager:
    def __init__(
            self
        ) -> None:

        self.component_store = {}

        @humecord.event("on_interaction")
        async def interaction(interaction) -> None:
            await self.recv_interaction(interaction)

    async def recv_interaction(self, interaction) -> None:
        """
        Receives an Interaction from discord and forwards it to 
        the proper functions.
        
        Params:
            interaction: discord.Interaction
        """

        # We don't want to handle app commands, they're done via callbacks
        if interaction.type == discord.InteractionType.application_command:
            return
        
        # Find out if this component has an ID
        data = getattr(interaction, "data", {})

        if "custom_id" not in data:
            humecord.logger.log("interaction", "warn", "Received interaction with no component ID. Skipping.")
            return
        _id = data["custom_id"]

        # Check if this is a permanent interaction (signified by !)
        if _id.startswith("!"):
            task = await self.run_perma_interaction(
                _id[1:],
                interaction
            )

        else:
            task = await self.run_temp_interaction(
                _id,
                interaction
            )

        if task is None:
            # Failed
            await interaction.response.send_message(
                embed = discordutils.error(
                    interaction.user,
                    "Interaction failed!",
                    "This interaction appears to be expired (happened over an hour ago/bot just restarted). Please try running the command again."
                ),
                ephemeral = True
            )
            return

        while not task.done():
            await asyncio.sleep(0.01) # Prevents automatic defer from happening

    async def register_component(
            self,
            component_name: str,
            component_type: humecord.ComponentTypes,
            callback,
            sender: Optional[Union[discord.User, discord.Member]] = None
        ) -> None:
        """
        Registers a component to the internal component store.
        
        Params:
            component_name (str): Component name
            component_type (humecord.classes.interactions.humecord.ComponentTypes): MODAL, BUTTON, SELECT, TEXTINPUT
            callback: Async callback function
            sender (Optional[discord.User, discord.Member] = None): If supplied, only this user may use the component
        
        Returns:
            _id (str): Component store ID (uuid:name)
        """
        component = {}
        # Keys:
        # type, _id, sender, callback
        if sender is not None:
            component["sender"] = sender.id

        component["name"] = component_name
        # Generate a UUID
        _uuid = str(uuid.uuid4())
        # Turn it into a component ID
        _id = f"{_uuid.replace('-', '')}:{component_name}"

        # Set type
        component["type"] = component_type

        # Set timeout
        component["timeout"] = int(time.time()) + 3600

        # Set callback
        component["callback"] = callback

        # Store to component store
        self.component_store[_id] = component

        return _id
        
    async def generate_resp(
            self,
            interaction: discord.Interaction
        ) -> discordclasses.ResponseChannel:
        """
        Generates a ResponseChannel for an interaction.
        
        Params:
            interaction (discord.interaction)
            
        Returns:
            resp (discordclasses.ResponseChannel)
        """

        return discordclasses.InteractionResponseChannel(interaction, is_component = True)

    async def generate_ctx(
            self,
            _id: str,
            interaction: discord.Interaction,
            resp: discordclasses.ResponseChannel,
            extra: dict[str, Any] = {},
            perma: bool = False
        ) -> discordclasses.Context:
        """
        Generates a Context object for an interaction.
        
        Params:
            _id (str)
            interaction (discord.interaction)
            resp (discordclasses.ResponseChannel)
            extra (dict[str, Any] = {}): Extra values to store in ctx
            perma (bool = False): Whether or not the component is permanent
            
        Returns:
            ctx (discordclasses.Context
        """
        # Get UDB and GDB
        kw = {}
        if interaction.guild:
            gdb = await humecord.bot.api.get(
                humecord.bot.config.self_api,
                "guild",
                { "id": interaction.guild.id, "autocreate": True }
            )

            kw["gdb"] = gdb
            kw["guild"] = interaction.guild

        # Get UDB
        try:
            udb = await humecord.bot.api.get(
                humecord.bot.config.user_api,
                "user",
                { "id": interaction.user.id, "autocreate": True }
            )

        except Exception as e:
            humecord.logger.log("command", "warn", "Couldn't retrieve user's UDB. Is the section enabled in the API, and defined as 'users' in endpoints.yml?")
            return

        kw["udb"] = udb

        # Extract selected item and UUID from component name
        if perma:
            kw["component"] = _id

        else:
            if _id.count(":") == 0:
                raise exceptions.DevError(f"Component ID {_id} is malformed.")

            kw["component_uuid"], kw["component"] = _id.split(":", 1)

        return discordclasses.Context(
            type = humecord.ContextTypes.COMPONENT,
            resp = resp,
            interaction = interaction,
            channel = interaction.channel,
            component_id = _id,
            user = interaction.user,
            **kw,
            **extra
        )


    async def run_perma_interaction(
            self,
            _id: str,
            interaction: discord.Interaction
        ):
        """
        Creates a task for a permanent interaction.

        Params:
            _id (str): Perma ID
            interaction (discord.Interaction)
        """
        # Then, the name is everything after
        # We dispatch that directly as an event
        resp = await self.generate_resp(
            interaction
        )
        ctx = await self.generate_ctx(
            _id,
            interaction,
            resp,
            extra = {
                "component_type": humecord.ComponentArgTypes.PERMA,
                "perma": True,
                "perma_id": _id
            },
            perma = True
        )

        # Verify no botban
        if ctx.udb["botban"] is not None:
            if ctx.udb["botban"]["endsat"] > time.time():
                humecord.logger.log("interaction", "int", f"User {interaction.user} ({interaction.user.id}) is botbanned. Skipping interaction.")
                return

        return humecord.bot.client.loop.create_task(
            humecord.bot.events.call(
                "hc_on_perma_interaction",
                [_id, resp, ctx]
            )
        )
    
    async def run_temp_interaction(
            self,
            _id: str,
            interaction: discord.Interaction
        ):
        """
        Creates a task for a temporary (runtime) interaction.

        Params:
            _id (str): Interaction UUID
            interaction (discord.Interaction)
        """
        humecord.logger.log("interaction", "int", f"Dispatching interaction ID {_id}", bold = True)

        # Check if the ID is in the component store
        c_details = self.component_store.get(_id)
        if c_details is None:
            humecord.logger.log("interaction", "warn", "Component is not registered in the component store. Skipping.")
            return

        # Check if this has a user requirement
        if "sender" in c_details:
            if interaction.user.id != c_details["sender"]:
                await interaction.response.send_message(
                    embed = discordutils.error(
                        interaction.user,
                        "No permission!",
                        "Only the original message sender can use this."
                    ),
                    ephemeral = True
                )
                return
        
        # Get information: values or modal args
        ext_kw = {}
        component_type = c_details.get("type")
        arg_type = humecord.ComponentArgTypes.ANY
        if component_type == humecord.ComponentTypes.SELECT:
            # Values, or the items in the list that are checked
            ext_kw["values"] = interaction.data["values"] or []
            arg_type = humecord.ComponentArgTypes.SELECT

        elif component_type == humecord.ComponentTypes.MODAL:
            ext_kw["modal_args"] = {}

            valid = True
            if "components" not in interaction.data:
                valid = False

            if len(interaction.data["components"]) != 1:
                valid = False
            
            components = interaction.data["components"][0].get("components")
            if components is None:
                valid = False

            if valid:
                # Iterate over each component in the modal
                for modal_component in components:
                    name = modal_component.get("custom_id")

                    if name is None:
                        continue

                    ext_kw["modal_args"][name] = modal_component.get("value")

            arg_type = humecord.ComponentArgTypes.MODAL

        # Generate args
        resp = await self.generate_resp(
            interaction
        )
        ctx = await self.generate_ctx(
            _id,
            interaction,
            resp,
            extra = {
                "component_type": arg_type,
                "perma": False,
                **ext_kw
            },
            perma = False
        )

        # Check for botban
        if ctx.udb["botban"] is not None:
            if ctx.udb["botban"]["endsat"] > time.time():
                humecord.logger.log("interaction", "int", f"User {interaction.user} ({interaction.user.id}) is botbanned. Skipping interaction.")
                return
            
        # Run the component's callback
        humecord.logger.log_long(
            "interaction",
            "int",
            [
                f"Type:           components.{argtype_to_str.get(arg_type)}",
                f"Component:      {_id}",
                f"Channel:        {interaction.channel.id} ({getattr(interaction.channel, 'name', None)})",
                f"User:           {interaction.user.id} ({interaction.user})"
            ]
        )

        return humecord.bot.client.loop.create_task(
            humecord.utils.errorhandler.wrap(
                c_details["callback"](resp, ctx)
            )
        )


    # --- Actual component generators ---
    async def create_view(
            self,
            components: List[discord.ui.Item] = []
        ) -> discord.ui.View:
        """
        Generates a view from a list of components.
        
        Params:
            components (List[discord.ui.Item]): Components
                Generate using one of:
                .create_button()
                .create_select()
                .create_modal()
                .create_textinput

        Returns:
            view (discord.ui.View)
        """
        view = discord.ui.View(timeout = 3600)

        for component in components:
            view.add_item(component)
        
        return view

    async def create_button(
            self,
            name: str,
            callback: Optional[Callable] = None,
            row: int = 0,
            perma: bool = False,
            disabled: bool = False,
            sender: Optional[Union[discord.Member, discord.User]] = None,
            label: str = "",
            style: humecord.ButtonStyles = humecord.ButtonStyles.PRIMARY,
            emoji: Optional[Union[str, discord.Emoji, discord.PartialEmoji]] = None,
            url: Optional[str] = None
        ) -> discord.ui.Button:
        """
        Generates a button and registers a callback to it.
        
        Params:
            -> General component args
                name (str): Component name/ID (20 chars or less) - unique per message
                callback (Optional[Callable] = None): Async function to call (args: ctx, resp)
                    Does nothing if component is permanent.
                    Tip - extra args:
                    `lambda *a: func(*a, "my_arg_1", 1234, ...)`
                    `async def func(ctx, resp, my_arg_1, my_arg_2, ...)`
                row (int): Row, 0-4, to place the item in (max 5 buttons/1 select per row)
                perma (bool = False): Permanent or not
                    (Need hc_on_perma_interaction event hook to receive)
                disabled (bool = False): Disable the button
                sender (Optional[discord.User, discord.Member]): Sender to restrict usage to
            -> Button specific args
                label (str): User-facing button label
                style (humecord.ButtonStyles): Button style
                    PRIMARY, SECONDARY, SUCCESS, DANGER, URL
                    or GRAY, BLUE, GREEN, RED, URL
                emoji (Optional[str, discord.Emoji, discord.PartialEmoji]): Emoji to display before item
                url (Optional[str]): URL to forward to. Style must be .URL, and callback will be ignored.
        
        Returns:
            button (discord.ui.Button)
        """

        # Verify name is valid
        if len(name) > 30:
            raise exceptions.InvalidComponent(f"Name must be <=30 chars (current: '{name}')") 

        # Create a callback
        if perma:
            _id = f"!{name}"

        elif (style != humecord.ButtonStyles.URL) or (callback is not None):
            _id = await self.register_component(
                component_name = name,
                component_type = humecord.ComponentTypes.BUTTON,
                callback = callback,
                sender = sender
            )

        else:
            _id = f"!nocallback:{name}"

        button = discord.ui.Button(
            style = style_to_discord[style],
            custom_id = _id,
            url = url,
            disabled = disabled,
            label = label,
            row = row,
            emoji = emoji
        )

        return button

    async def create_select(
            self,
            name: str,
            callback: Optional[Callable] = None,
            row: int = 0,
            perma: bool = False,
            disabled: bool = False,
            sender: Optional[Union[discord.Member, discord.User]] = None,
            placeholder: str = "",
            min_values: int = 1,
            max_values: int = 1,
            options: dict[str, dict[str, Any]] = {}
        ) -> discord.ui.Select:
        """
        Generates a dropdown/select menu and registers a callback to it.
        
        Params:
            -> General component args
                name (str): Component name/ID (20 chars or less) - unique per message
                callback (Optional[Callable] = None): Async function to call (args: ctx, resp)
                    Does nothing if component is permanent.
                    Tip - extra args:
                    `lambda *a: func(*a, "my_arg_1", 1234, ...)`
                    `async def func(ctx, resp, my_arg_1, my_arg_2, ...)`
                row (int): Row, 0-4, to place the item in (max 5 buttons/1 select per row)
                perma (bool = False): Permanent or not
                    (Need hc_on_perma_interaction event hook to receive)
                disabled (bool = False): Disable the button
                sender (Optional[discord.User, discord.Member]): Sender to restrict usage to
            -> Select specific args
                placeholder (str): Description which is displayed before a value is selected
                min_values (int = 1): Minimum options checked before callback is run
                max_values (int = 1): Maximum options which can be checked at once
                options (dict[str, dict[str, Any]] = {}): Dropdown options
                    Format:
                    ```python
                    options = {
                        "option_1": {
                            "name": "Sample option",
                            "description": "A really cool option.",
                            "emoji": "👍", # Optional
                            "default": True # Optional -- if True, it's selected at send. Defaults to False.
                        }
                    }
                    ```

        Returns:
            select (discord.ui.Select)
        """

        # Verify name is valid
        if len(name) > 30:
            raise exceptions.InvalidComponent(f"Name must be <=30 chars (current: '{name}')") 

        # Generate options
        items = []
        for option, details in options.items():
            items.append(
                discord.SelectOption(
                    label = details["name"],
                    value = option,
                    description = details.get("description"),
                    emoji = details.get("emoji"),
                    default = details.get("default") or False
                )
            )

        # Create a callback
        if perma:
            _id = f"!{name}"

        elif callback is not None:
            _id = await self.register_component(
                component_name = name,
                component_type = humecord.ComponentTypes.SELECT,
                callback = callback,
                sender = sender
            )

        else:
            _id = f"!nocallback:{name}"

        return discord.ui.Select(
            custom_id = _id,
            placeholder = placeholder,
            min_values = min_values,
            max_values = max_values,
            options = items,
            disabled = disabled,
            row = row
        )

    async def create_modal(
            self,
            name: str,
            callback,
            sender: Union[discord.Member, discord.User],
            title: str = None,
            components: List[discord.ui.Item] = []
        ) -> discord.ui.Button:
        """
        Generates a modal from a list of components.
        
        Params:
            -> General component args
                name (str): Component name/ID (20 chars or less) - unique per message
                callback (Optional[Callable] = None): Async function to call (args: ctx, resp)
                    Does nothing if component is permanent.
                    Tip - extra args:
                    `lambda *a: func(*a, "my_arg_1", 1234, ...)`
                    `async def func(ctx, resp, my_arg_1, my_arg_2, ...)`
                sender (Optional[discord.User, discord.Member]): Sender to restrict usage to
            -> Select specific args
                title (str): Title to display to user
                components (list[discord.ui.Item]): Components to render

        Returns:
            modal (discord.ui.Modal)
        """

        if callback is not None:
            _id = await self.register_component(
                component_name = name,
                component_type = humecord.ComponentTypes.MODAL,
                callback = callback,
                sender = sender
            )

        else:
            _id = f"!nocallback:{_id}"

        modal = discord.ui.Modal(
            title = title,
            timeout = 3600,
            custom_id = _id
        )

        for component in components:
            modal.add_item(component)

        return modal

    async def create_textinput(
            self,
            name: str,
            label: str = "",
            default: Optional[str] = None,
            placeholder: Optional[str] = None,
            required: bool = False,
            min_length: int = 1,
            max_length: int = 128,
            long: bool = False
        ) -> discord.ui.TextInput:
        """
        Generates a textinput.
        Must be used in a modal.
        
        Params:
            -> General component args
                name (str): Component name/ID (20 chars or less) - unique per message
            -> Select specific args
                label (str): Input label
                default (Optional[str]): Default text
                placeholder (Optional[str]): Placeholder string before anything is input
                required (bool = False): Whether or not the textinput is required
                min_length (int = 1): Minimum text length to submit
                max_length (int = 128): Maximum text length to submit
                long (bool = False): If True, turns into a paragraph style input

        Returns:
            modal (discord.ui.Modal)
        """

        if long:
            style = discord.TextStyle.long

        else:
            style = discord.TextStyle.short

        return discord.ui.TextInput(
            custom_id = name,
            label = label,
            placeholder = placeholder,
            default = default,
            min_length = min_length,
            max_length = max_length,
            style = style,
            required = required
        )

    async def skip(
            self,
            *args,
            **kwargs
        ) -> None:
        """
        Placeholder function for dynamically generating callbacks which
        accepts any args and does nothing.
        """
        pass
    

argtype_to_str = {
    humecord.ComponentArgTypes.ANY: "any",
    humecord.ComponentArgTypes.SELECT: "select",
    humecord.ComponentArgTypes.MODAL: "modal",
    humecord.ComponentArgTypes.PERMA: "perma"
}

style_to_discord = {
    humecord.ButtonStyles.PRIMARY: discord.ButtonStyle.primary,
    humecord.ButtonStyles.BLUE: discord.ButtonStyle.primary,
    humecord.ButtonStyles.SECONDARY: discord.ButtonStyle.secondary,
    humecord.ButtonStyles.GRAY: discord.ButtonStyle.secondary,
    humecord.ButtonStyles.GREY: discord.ButtonStyle.secondary,
    humecord.ButtonStyles.SUCCESS: discord.ButtonStyle.success,
    humecord.ButtonStyles.GREEN: discord.ButtonStyle.success,
    humecord.ButtonStyles.DANGER: discord.ButtonStyle.danger,
    humecord.ButtonStyles.RED: discord.ButtonStyle.danger,
    humecord.ButtonStyles.HYPERLINK: discord.ButtonStyle.link,
    humecord.ButtonStyles.LINK: discord.ButtonStyle.link,
    humecord.ButtonStyles.URL: discord.ButtonStyle.link,
}