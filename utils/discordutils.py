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

    if type(member) in [discord.Member, discord.User, discord.ClientUser]:
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

def generate_activity(
        type: str,
        details: str,
        streaming: Optional[dict],
    ):

    if type == "streaming":
        return discord.Streaming(
            name = details,
            game = streaming.get("game"),
            url = streaming.get("url"),
            twitch_name = streaming.get("name"),
            platform = streaming.get("platform")
        )

    else:
        activity = discord.Activity(name = details)

        activity.type = eval(humecord.bot.config.activities[type], globals())

        return activity

def get_user(
        user: str,
        allow_guild_lookup: bool = False,
        message = None
    ):

    if type(user) != int:
        # Format out characters
        for char in "<@!>":
            user = user.replace(char, "")

        # Try to turn into int
        try:
            user = int(user)

        except:
            # Check if the user's in the guild
            if allow_guild_lookup:
                if message is None:
                    raise humecord.utils.exceptions.NotFound(f"Specify a user's ID, or mention them.")

                matches = []
                name = user.lower()

                if len(name) > 5:
                    if name[-5] == "#":
                        name, discrim = name.rsplit("#", 1)

                        try:
                            discrim = int(discrim)

                        except:
                            name = f"{name}#{discrim}"
                            discrim = None

                    else:
                        discrim = None

                else:
                    discrim = None

                for member in message.guild.members:
                    if name in member.name.lower():
                        if discrim is not None:
                            if int(member.discriminator) != discrim:
                                continue

                        matches.append(member)

                if len(matches) == 0:
                    raise humecord.utils.exceptions.NotFound(f"Member `{user}` doesn't exist.")

                elif len(matches) > 1:
                    raise humecord.utils.exceptions.NotFound(f"Too many matches found for `{user}` in this server. Mention them instead.")
        
                else:
                    return matches[0]

            else:
                raise humecord.utils.exceptions.NotFound(f"Specify a user's ID, or mention them.")

    user_ = humecord.bot.client.get_user(
        user
    )

    if user_ is None:
        raise humecord.utils.exceptions.NotFound(f"User `{user}` doesn't exist.")

    return user_
