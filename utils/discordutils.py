from typing import Union, Optional
import discord

from .colors import Colors
import humecord

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

        embed.add_field(name = field["name"], value = field["value"], inline = inline)

    if thumbnail:
        embed.set_thumbnail(url = thumbnail)

    if image:
        embed.set_image(url = image)

    if profile or author:
        embed = get_profile(profile or author, embed)
            
    return embed

def get_profile(
        member: Union[discord.Member, discord.User, list],
        embed: discord.Embed
    ):

    if type(member) in [discord.Member, discord.User]:
        name = f"{member.name}#{member.discriminator}"

        if type(member) == discord.Member:
            if member.nick:
                name = f"{member.nick} ({member.name}#{member.discriminator})"
                
        embed.set_author(name = name, icon_url = member.avatar.url)

    else:
        kw = {}
        if len(member) == 3:
            kw = {"url": member[2]}
            
        embed.set_author(name = member[0], icon_url = member[1], **kw)

    return embed


def error(
        member: Optional[Union[discord.Member, discord.User]],
        title: Optional[str],
        description: Optional[str]
    ):

    embed = create_embed(
        description = f"{humecord.bot.config.lang['emoji']['error']}  **{title}**\n{description}",
        color = "error"
    )

    if member is not None:
        embed = get_profile(member, embed)

    return embed


def check_perms(
        member: discord.Member
    ):

    pass 