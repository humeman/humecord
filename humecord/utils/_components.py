from typing import Union, Optional
import discord

from humecord.utils import exceptions
from humecord.classes.discordclasses import (
    Button,
    Select,
    TextInput,
    Modal
)
import humecord
import time

button_styles = {
    "primary": "primary",
    "secondary": "secondary",
    "success": "success",
    "danger": "danger",
    "url": "hyperlink"
}

styles = {
    "primary": discord.ButtonStyle.primary,
    "secondary": discord.ButtonStyle.secondary,
    "success": discord.ButtonStyle.success,
    "danger": discord.ButtonStyle.danger,
    "hyperlink": discord.ButtonStyle.link
}

class CoolView(discord.ui.View):
    def __init__(self, children):
        self.children = children

def create_view(
        components: list = [],
        timeout = 3600
    ):

    view = discord.ui.View(timeout = timeout)

    for component in components:
        view.add_item(component)

    return view

def create_action_row(
        components: list = []
    ):

    pass

def create_button(
        style: str = "primary",
        label: str = "",
        id: Optional[str] = None,
        callback = None,
        url: Optional[str] = None,
        disabled: bool = False,
        emoji: Optional[str] = None,
        sender: Optional[Union[discord.Member, discord.User]] = None,
        row: int = 0,
        permanent: bool = False,
        permanent_id: Optional[str] = None
    ):

    # Parse type
    if style not in button_styles:
        raise exceptions.InvalidComponent(f"Style {style} does not exist")

    _style = button_styles[style] # Discordify

    # Generate the ID
    if id is None:
        raise exceptions.InvalidComponent("ID must be defined")

    # Format: {messageid}-{buttonid}-{id}
    if len(id) > 64:
        raise exceptions.InvalidComponent("ID must be 64 characters or shorter")

    if permanent:
        id = f"hcperma_{permanent_id}"


    # Parse label
    if len(label) > 80:
        raise exceptions.InvalidComponent("Label must be 80 characters or shorter")

    # Store the callback
    if _style != "link":
        if sender is not None:
            arg = [sender.id]

        else:
            arg = [None]

        if (not permanent) and (callback is not None):
            humecord.bot.interactions.register_component(
                "button",
                id,
                callback,
                *arg
            )

    # Update component type
    d_style = styles[_style]

    # Generate the component

    kw = {}

    if emoji:
        kw["emoji"] = emoji

    if _style == "link":
        if not url:
            raise exceptions.InvalidComponent("URL must be specified for url-style components")

        return Button(
            style = d_style,
            custom_id = id,
            url = url,
            disabled = disabled,
            label = label,
            row = row,
            **kw
        )

    else:
        return Button(
            style = d_style,
            custom_id = id,
            disabled = disabled,
            label = label,
            row = row,
            **kw
        )
        
def create_dropdown(
        placeholder: str = "",
        min_values: int = 1,
        max_values: int = 1,
        id: Optional[str] = None,
        callback = None,
        options: dict = {},
        row: int = 0,
        sender: Optional[Union[discord.Member, discord.User]] = None,
        permanent: bool = False,
        permanent_id: Optional[str] = None
    ):

    # Define items
    items = []

    for opt_id, option in options.items():
        items.append(
            discord.SelectOption(
                label = option["name"],
                value = opt_id,
                description = option.get("description"),
                emoji = option.get("emoji"),
                default = option.get("default") if "default" in option else False
            )
        )

    if permanent:
        id = f"hcperma_{permanent_id}"

    
    if sender is not None:
        arg = [sender.id]

    else:
        arg = [None]

    if (not permanent) and (callback is not None):
        humecord.bot.interactions.register_component(
            "select",
            id,
            callback,
            *arg
        )

    return Select(
        custom_id = id,
        placeholder = placeholder,
        min_values = min_values,
        max_values = max_values,
        options = items,
        row = row
    )

def create_modal(
        title: str = None,
        id: Optional[str] = None,
        callback = None,
        components = [],
        timeout: int = 3600,
        sender: Union[discord.Member, discord.User] = None
    ):

    modal = Modal(
        title = title,
        timeout = timeout,
        custom_id = id
    )
    
    for component in components:
        modal.add_item(component)

    if callback is not None:
        humecord.bot.interactions.register_component(
            "modal",
            id,
            callback,
            sender.id
        )

    return modal

def create_textinput(
        label: str = "",
        placeholder: str = "",
        default: str = None,
        id: Optional[str] = None,
        min_length: int = 1,
        max_length: int = 1024,
        required: bool = True,
        text_style: Optional[discord.TextStyle] = None,
        permanent: bool = False,
        permanent_id: Optional[str] = None
    ):

    if permanent:
        id = f"hcperma_{permanent_id}"


    if text_style is not None:
        style = text_style

    elif max_length > 128:
        style = discord.TextStyle.long

    else:
        style = discord.TextStyle.short

    return TextInput(
        custom_id = id,
        label = label,
        placeholder = placeholder,
        default = default,
        min_length = min_length,
        max_length = max_length,
        style = style,
        required = required
    )

async def skip(*args, **kwargs) -> None:
    """
    Does nothing.
    For creating callbacks which do nothing easily
    (ie: user presses a button for the active item)
    """
    pass