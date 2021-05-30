from typing import Union, Optional
import discord

from humecord.utils import exceptions
from humecord.classes.discordclasses import Button
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

def create_action_row(
        components: list = []
    ):

    view = discord.ui.View()

    for component in components:
        view.add_item(component)

    return view

def create_button(
        message,
        style: str = "primary",
        label: str = "",
        id: Optional[str] = None,
        callback = None,
        url: Optional[str] = None,
        disabled: bool = False,
        emoji: Optional[str] = None
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
        humecord.bot.interactions.register_component(
            "button",
            _id,
            callback
        )

    # Update component type
    d_style = styles[_style]

    # Generate the component

    if _style == "emoji":
        if not emoji:
            raise exceptions.InvalidComponent("Emoji must be specified for emoji-style components")

        return Button(
            style = d_style,
            custom_id = _id,
            emoji = emoji,
            disabled = disabled,
            label = label,
            callback = humecord.bot.interactions.process_interaction()
        )

    elif _style == "link":
        if not url:
            raise exceptions.InvalidComponent("URL must be specified for url-style components")

        return Button(
            style = d_style,
            custom_id = _id,
            url = url,
            disabled = disabled,
            label = label
        )

    else:
        return Button(
            style = d_style,
            custom_id = _id,
            disabled = disabled,
            label = label
        )
        
def create_dropdown(
        message,
        placeholder: str = "",
        min_values: int = 1,
        max_values: int = 1,
        id: Optional[str] = None,
        callback = None,
        options: dict = {}
    ):

    # Define items
    items = []

    for _id, option in options.items():
        items.append(
            discord.SelectOption(
                label = option["name"],
                value = _id,
                description = option.get("description"),
                emoji = option.get("emoji"),
                default = option.get("default") if "default" in option else False
            )
        )

    _id = f"{message.id}.{id}"

    humecord.bot.interactions.register_component(
        "select",
        _id,
        callback
    )

    return discord.ui.Select(
        custom_id = _id,
        placeholder = placeholder,
        min_values = min_values,
        max_values = max_values,
        options = items
    )