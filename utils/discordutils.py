from typing import Union
import discord

from .colors import Colors

def create_embed(
        title = discord.Embed.Empty,
        description = discord.Embed.Empty,
        fields: list = [],
        color: str = "invisible",
        footer: Union[str, None] = None,
        thumbnail: Union[str, None] = None,
        image: Union[str, None] = None,
        author: Union[discord.User, discord.Member, None] = None,
        profile: Union[list, None] = None
    ):

    color = Colors.get_color(color)

    embed = discord.Embed(title = title, description = description, color = color)

    if footer:
        embed.set_footer(text = footer)

    for field in fields:
        inline = field.get("inline") if "inline" in field else None

        embed.add_field(name = field["name"], value = field["value"], inline = field["inline"])

    if thumbnail:
        embed.set_thumbnail(url = thumbnail)

    if image:
        embed.set_image(url = image)

    if profile or author:
        if author:
            name = f"{profile.name}#{profile.discriminator}"

            if type(author) == discord.Member:
                if profile.nick:
                    name = f"{profile.nick} ({profile.name}#{profile.discriminator})"
                    
            embed.set_author(name = name, icon_url = profile.avatar_url)

        if profile:
            if len(profile) == 3:
                embed.set_author(name = profile[0], icon_url = profile[1], url = profile[2])

            else:
                embed.set_author(name = profile[0], icon_url = profile[1])
            
    return embed

        
        