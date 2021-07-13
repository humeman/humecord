from typing import Union, Optional
import discord

from humecord.utils import exceptions
from humecord.classes.discordclasses import (
    Button,
    Select
)
import humecord

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
        components: list = []
    ):

    view = discord.ui.View(timeout = 3600)

    for component in components:
        view.add_item(component)

    return view

def create_action_row(
        components: list = []
    ):

    pass

def create_button(
        message,
        style: str = "primary",
        label: str = "",
        id: Optional[str] = None,
        callback = None,
        url: Optional[str] = None,
        disabled: bool = False,
        emoji: Optional[str] = None,
        only_sender: bool = True,
        row: int = 0
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

    _mid = message.id

    _id = f"{_mid}.{id}"

    # Parse label
    if len(label) > 80:
        raise exceptions.InvalidComponent("Label must be 80 characters or shorter")

    # Store the callback
    if _style != "link":
        if only_sender:
            arg = [message.author.id]

        else:
            arg = [None]

        humecord.bot.interactions.register_component(
            "button",
            _id,
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
            custom_id = _id,
            url = url,
            disabled = disabled,
            label = label,
            row = row,
            **kw
        )

    else:
        return Button(
            style = d_style,
            custom_id = _id,
            disabled = disabled,
            label = label,
            row = row,
            **kw
        )
        
def create_dropdown(
        message,
        placeholder: str = "",
        min_values: int = 1,
        max_values: int = 1,
        id: Optional[str] = None,
        callback = None,
        options: dict = {},
        row: int = 0
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

    _id = f"{message.id}.{id}"

    humecord.bot.interactions.register_component(
        "select",
        _id,
        callback,
        message.author.id
    )

    return Select(
        custom_id = _id,
        placeholder = placeholder,
        min_values = min_values,
        max_values = max_values,
        options = items,
        row = row
    )