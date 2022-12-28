from humecord.utils import (
    exceptions,
    colors,
    discordutils
)

from humecord.utils.exceptions import InvalidData as IE
import humecord

import re
import discord
from typing import Union



class ParseStr:
    async def main(
            inp
        ):

        try:
            inp = str(inp)

        except:
            raise IE(f"Unable to convert to string")

        return inp

    async def len(
            inp,
            args
        ):
        l = len(inp)

        if l < args[0] or l > args[1]:
            raise IE(f"Value's length isn't within bounds: {args[0]} to {args[1]}")

    async def includes(
            inp,
            args
        ):

        inp = inp.lower()

        for arg in args:
            arg = arg.lower()

            if arg in inp:
                return

        raise IE(f"Value doesn't include any of required words: {', '.join(args)}")

    async def alnum(
            inp,
            args
        ):

        if not inp.replace("-", "").replace("_", "").isalnum():
            raise IE("Value isn't alphanumeric")

    async def in_(
            inp,
            args
        ):

        args = [x.lower() for x in args]

        if inp.lower() not in args:
            raise IE(f"Value isn't one of required phrases: {', '.join(args)}")
    
    async def regex(
            inp,
            args
        ):

        for arg in args:
            if not re.match(arg, inp):
                raise IE(f"Value failed regex check: {arg}")

    async def format(
            inp
        ):

        return str(inp)

class ParseInt:
    async def main(
            inp
        ):

        try:
            inp = int(inp)

        except:
            raise IE(f"Unable to convert to int")

        return inp

    async def between(
            inp,
            args
        ):

        if inp < args[0] or inp > args[1]:
            raise IE(f"Value is outside of bounds: {args[0]} to {args[1]}")

    async def less(
            inp,
            args
        ):

        if inp >= args[0]:
            return IE(f"Value isn't less than {args[0]}")

    async def greater(
            inp,
            args
        ):

        if inp <= args[0]:
            return IE(f"Value isn't greater than {args[0]}")

    async def format(
            inp
        ):

        return str(inp)
    
class ParseFloat:
    async def main(
            inp
        ):

        try:
            inp = float(inp)

        except:
            raise IE(f"Unable to convert to float")

        return inp
    
    async def format(
            inp
        ):

        return str(round(inp, 2))

class ParseBool:
    async def main(
            inp
        ):

        inp = inp.lower()

        if inp in ["yes", "y", "true", "t", "enable", "on"]:
            return True

        elif inp in ["no", "n", "false", "f", "disable", "off"]:
            return False

        else:
            raise IE("Unable to convert into bool")

    async def format(
            inp
        ):

        return "Yes" if inp else "No"

class ParseEmbed:
    async def main(
            inp,
            return_embed: bool = False
        ):

        # Our valid keys are:
        keys = {
            "title": [], # 
            "description": [], #
            "field": [], #
            "footer": [], #
            "profile": [], #
            "color": [], #
            "image": [],
            "thumbnail": []
        }

        # Pad the message so we can check for each key as an independent word.
        inp = f" {inp.strip()}"

        current_key = None
        current = []
        # Start checking for keys
        for word in inp.split(" "):
            # Check if there's an = in this word
            if "=" in word:
                # Split from before & after
                key, content = word.split("=", 1)

                # Check if the key is valid
                key = key.lower()
                if key in keys:
                    # Found a valid key
                    # So, we should append everything in current to the last key
                    # to 'complete' it - then make a new 'current', and define
                    # what key we're working with.
                    if current_key is not None:
                        # Append to old
                        keys[current_key].append(" ".join(current))
                        current = []

                    # Define the current key
                    current_key = key

                    # Add the rest of the word to current
                    current.append(content)

                    # Stop running
                    continue

            current.append(word)

        # When we're done, finish off current
        keys[current_key].append(" ".join(current))

        # Validate the rest of it, and start compiling to kwargs
        # Each of these keys should only have 1 or 0 total. Make sure that's the case.
        for key in ["title", "description", "profile", "footer", "color", "image", "thumbnail"]:
            if len(keys[key]) > 1:
                raise IE(f"Can't have more than one value for {key}")

        kw = {}

        # Also keep a running total of char count.
        total = 0

        # Title validation
        if len(keys["title"]) > 0:
            title = keys["title"][0]

            # Check length
            l = len(title)

            if l > 256 or l < 1:
                raise IE(f"Title must be between 1 and 256 characters, not {l}")

            # Append
            kw["title"] = title

            total += l

        # Description validation
        if len(keys["description"]) > 0:
            description = keys["description"][0]

            # Check length
            l = len(description)

            if l > 4096 or l < 1:
                raise IE(f"Description must be between 1 and 4096 characters, not {l}")

            # Append
            kw["description"] = description

            total += l

        # Field validation
        if len(keys["field"]) > 0:
            if len(keys["field"]) > 25:
                raise IE(f"Field count can't exceed 25")

            fields = []

            for i, field in enumerate(keys["field"]):
                # Parse it - name|title|inline
                    # (inline optional)

                if "|" not in field:
                    raise IE(f"Fields must have a name and a value, separated by `|`: `name|value`")

                name, value = field.split("|", 1)

                # Check name length
                l = len(name)

                if l < 1 or l > 256:
                    raise IE(f"Field names must be between 1 and 256 characters, but field #{i + 1} has a length of {l}")

                total += l

                # Same thing with the value
                # But first, check if inline is defined
                end = value.split(" ")[-1]
                il = False
                if "|" in end:
                    # Split it out
                    __, inline = end.rsplit("|", 1)

                    inline = inline.lower()

                    if inline in ["y", "yes", "true", "inline", "i", "il", "t", "enable"]:
                        il = True
                        # Remove end from message
                        value = value.rsplit("|", 1)[0]

                    elif inline in ["n", "no", "false", "f", "disable"]:
                        il = False
                        # Remove end from message
                        value = value.rsplit("|", 1)[0]

                l = len(value)

                if l < 1 or l > 1024:
                    raise IE(f"Field values must be between 1 and 1024 characters, but field #{i + 1} has a length of {l}")

                total += l

                # Append
                kw["fields"].append(
                    {
                        "name": name,
                        "value": value,
                        "inline": il
                    }
                )

        # Check color
        if len(keys["color"]) > 0:
            color = keys["color"][0].lower()

            # Check if it exists
            try:
                color = colors.Colors.get_color(color)

            except:
                raise IE(f"Color {color} doesn't exist")

            # Append
            kw["color"] = color

        # Check footer
        if len(keys["footer"]) > 0:
            footer = keys["footer"][0]

            final = None

            # Check if image included
            if "|" in footer:
                footer, image = footer.rsplit("|", 1)

                # Validate image
                try:
                    image = await ParseURL.main(image)

                except:
                    # Revert
                    footer = f"{footer}|{image}"

                else:
                    final = [footer, image]

            
            l = len(footer)

            if l < 1 or l > 2048:
                raise IE(f"Footers must be between 1 and 2048 characters, not {l}")

            if not final:
                final = footer

            total += l

            # Append
            kw["footer"] = final

        # Check profile
        if len(keys["profile"]) > 0:
            profile = keys["profile"][0]
            
            result = []

            # Insert in icon
            if "|" in profile:
                profile, icon = profile.split("|", 1)

                # Check if the icon also has a |
                if "|" in icon:
                    icon, url = icon.split("|", 1)

                    # Check if URL is valid
                    try:
                        image = await ParseURL.main(url)

                    except:
                        # Revert
                        icon = f"{icon}|{url}"
                    
                    else:
                        # Append to results
                        result.append(image)

                # Check if icon is a URL
                try:
                    icon = await ParseURL.main(icon)

                except:
                    # Revert
                    profile = f"{profile}|{icon}"
                    ext = []

                else:
                    # Insert into results
                    result.insert(0, icon)

            # Validate name
            l = len(profile)

            if l < 1 or l > 256:
                raise IE(f"Profile name must be between 1 and 256 characters, not {l}")

            total += l

            # Set to KW
            kw["profile"] = [profile, *result]
        
        # Image
        if len(keys["image"]) > 0:
            image = keys["image"][0]

            # Check if URL is valid (and pass any exceptions along)
            image = await ParseURL.main(image)

            # Append
            kw["image"] = image

        # Thumbnail
        if len(keys["thumbnail"]) > 0:
            image = keys["thumbnail"][0]

            # Check if URL is valid (and pass any exceptions along)
            image = await ParseURL.main(image)

            # Append
            kw["thumbnail"] = image

        if total > 6000:
            raise IE(f"Total embed length can't exceed 6000 characters - this embed is {total} characters long")

        # Done!
        if return_embed:
            return discordutils.create_embed(
                **kw
            )

        return kw

    async def format(
            inp: Union[dict, discord.Embed, str],
            shorten: bool
        ):

        values = {}

        if type(inp) == dict:
            # Just pass it along
            for key, value in inp.items():
                if key in ["title", "description", "field", "footer", "profile", "color", "image", "thumbnail"]:
                    values[key] = value

        elif type(inp) == discord.Embed:
            # Get dict
            inp = inp.to_dict()

            # Format out
            for key in ["title", "description", "color"]:
                if key in inp:
                    values[key] = inp[key]

            # Adjust image
            for key in ["image", "thumbnail"]:
                if key in inp:
                    values[key] = inp[key]["url"]

            # Footer & author
            if "footer" in inp:
                comp = []

                if "text" in inp["footer"]:
                    comp.append(inp["footer"]["text"])

                if "icon_url" in inp["footer"]:
                    comp.append(inp["footer"]["icon_url"])

                values["footer"] = comp

            if "author" in inp:
                comp = []

                if "name" in inp["author"]:
                    comp.append(inp["author"]["name"])

                if "icon_url" in inp["author"]:
                    comp.append(inp["author"]["icon_url"])

                if "url" in inp["author"]:
                    comp.append(inp["author"]["url"])

                values["author"] = comp

        else:
            # Parse it first
            values = await ParseEmbed.main(
                inp,
                return_embed = False
            )

        # Return formatted string
        comp = []

        for key, value in values.items():
            if key == "color":
                if type(value) == int:
                    value = colors.Colors.get_color_string(value)

                comp.append(f"color: {value}")

            elif key == "profile":
                comp.append("profile:")
                for i, v in enumerate(value):
                    k = ["name", "url", "icon_url"][i]
                    if shorten:
                        comp.append(f"  {k}: {v[:50]}{'...' if len(v) > 50 else ''}")

                    else:
                        comp.append(f"  {k}: {v}")

            elif key == "footer":
                comp.append("footer:")
                for i, v in enumerate(value):
                    k = ["text", "icon_url"][i]
                    if shorten:
                        comp.append(f"  {k}: {v[:50]}{'...' if len(v) > 50 else ''}")

                    else:
                        comp.append(f"  {k}: {v}")
            else:
                if shorten:
                    comp.append(f"{key}: {value[:100]}{'...' if len(value) > 100 else ''}")

                else:
                    comp.append(f"{key} = {value}")

        return "\n".join(comp)

whitespace_regex = re.compile(r'(\s|\u180B|\u200B|\u200C|\u200D|\u2060|\uFEFF)+') # Removes whitepsace
class ParseURL:
    async def main(
            inp: str
        ):

        inp = inp.strip()

        # Make sure there aren't spaces
        if whitespace_regex.sub("", inp) != inp:
            raise IE(f"URL cannot have whitespace in it - is it properly encoded?")

        # Check for protocol
        if "://" not in inp:
            raise IE(f"Missing protocol (http:// or https://)")

        # Get protocol
        protocol, rest = inp.split("://", 1)

        if protocol not in ["http", "https"]:
            raise IE(f"Invalid protocol (must be http or https)")

        # Check domain
        domain = rest.split("/")[0]

        if "." not in domain:
            raise IE(f"Invalid domain")

        # Good
        return inp

    async def format(
            inp
        ):

        return str(inp)

class ParseUser:
    async def main(
            inp: str
        ):

        inp = inp.strip()
        
        # Remove <, @, !, >
        for char in "<@!>":
            inp = inp.replace(char, "")

        # Try to turn into int
        try:
            inp = int(inp)

        except:
            raise IE(f"Invalid ID")

        # Try to get user
        user = humecord.bot.client.get_user(inp)

        if user is None:
            raise IE("User not found")

        # Good
        return user

    async def format(
            inp
        ):

        return str(inp)

    async def guild(
            inp,
            args
        ):

        member = humecord.bot.client.get_guild(args[0]).get_member(inp.id)

        if member is None:
            raise IE("User is not in guild")

channel_permission_presets = {
    "text": [
        "read_messages",
        "send_messages",
        "embed_links",
        "external_emojis",
        "attach_files",
        "add_reactions",
        "read_message_history"
    ],
    "text_mod": [
        "read_messages",
        "send_messages",
        "embed_links",
        "external_emojis",
        "attach_files",
        "add_reactions",
        "read_message_history",
        "manage_messages",
    ],
    "voice": [
        "view_channel",
        "connect",
        "speak",
        "use_voice_activation"
    ],
    "voice_mod": [
        "view_channel",
        "connect",
        "speak",
        "use_voice_activation",
        "move_members",
        "deafen_members",
        "mute_members"
    ]
}

class ParseChannel:
    async def main(
            inp: str
        ):

        inp = inp.strip()
        
        # Remove <, @, !, >
        for char in "<#!>":
            inp = inp.replace(char, "")

        # Try to turn into int
        try:
            inp = int(inp)

        except:
            raise IE(f"Invalid ID")

        # Try to get channel
        channel = humecord.bot.client.get_channel(inp)

        if channel is None:
            raise IE("Channel not found")

        # Good
        return channel

    async def format(
            inp
        ):

        return str(inp)

    async def rights(
            inp,
            args
        ):

        member = inp.guild.me

        if member is None:
            raise IE("Bot is not in guild")

        preset = args[0].lower()

        if preset not in channel_permission_presets:
            raise IE(f"Preset {preset} doesn't exist")

        perms = channel_permission_presets[preset]

        valid = discordutils.has_rights(
            inp,
            member,
            perms
        )

        if not valid:
            raise IE("Missing permissions")

    async def channel_type(
            inp,
            args
        ):

        req_type = args[0].lower()

        types = {
            "text": discord.TextChannel,
            "voice": discord.VoiceChannel,
            "stage": discord.StageChannel,
            "widget": discord.WidgetChannel,
            "group": discord.GroupChannel,
            "dm": discord.DMChannel,
        }

        ctype = types.get(req_type)

        if ctype is None:
            raise IE(f"Type {req_type} doesn't exist")

        if type(inp) != ctype:
            raise IE("Channel is of wrong type")




# Argument rules
# Imported by the argument parser on init.
rules = {
    "str": {
        "main": ParseStr.main,
        "functions": {
            "len": {
                "function": ParseStr.len,
                "args": [[int], [int]],
                "str": "between %0 and %1 characters"
            },
            "includes": {
                "function": ParseStr.includes,
                "arg_types": [str],
                "str": "includes one of %all"
            },
            "alnum": {
                "function": ParseStr.alnum,
                "str": "alphanumeric"
            },
            "in": {
                "function": ParseStr.in_,
                "arg_types": [str],
                "str": "one of %all"
            },
            "regex": {
                "function": ParseStr.regex,
                "arg_types": [str],
                "str": "matches regex %all"
            }
        },
        "str": "a string",
        "data": {},
        "format": {
            "data": {},
            "function": ParseStr.format
        }
    },
    "bool": {
        "main": ParseBool.main,
        "functions": {},
        "data": {},
        "str": "a boolean",
        "format": {
            "data": {},
            "function": ParseBool.format
        }
    },
    "int": {
        "main": ParseInt.main,
        "str": "an integer",
        "functions": {
            "between": {
                "function": ParseInt.between,
                "args": [[int], [int]],
                "str": "between %0 and %1"
            },
            "less": {
                "function": ParseInt.less,
                "args": [[int]],
                "str": "below %0"
            },
            "greater": {
                "function": ParseInt.greater,
                "args": [[int]],
                "str": "above %0"
            }
        },
        "data": {},
        "format": {
            "data": {},
            "function": ParseInt.format
        }
    },
    "float": {
        "main": ParseFloat.main,
        "str": "a number",
        "functions": {
            "between": {
                "function": ParseInt.between,
                "args": [[int], [int]],
                "str": "between %0 and %1"
            },
            "less": {
                "function": ParseInt.less,
                "args": [[int]],
                "str": "below %0"
            },
            "greater": {
                "function": ParseInt.greater,
                "args": [[int]],
                "str": "above %0"
            }
        },
        "data": {},
        "format": {
            "data": {},
            "function": ParseFloat.format
        }
    },
    "embed": {
        "main": ParseEmbed.main,
        "functions": {},
        "data": {},
        "str": "a discord embed",
        "format": {
            "data": {
                "shorten": [bool]
            },
            "function": ParseEmbed.format
        }
    },
    "url": {
        "main": ParseURL.main,
        "str": "a url",
        "functions": {},
        "data": {},
        "format": {
            "data": {},
            "function": ParseURL.format
        }
    },
    "user": {
        "main": ParseUser.main,
        "str": "a discord user",
        "functions": {
            "guild": {
                "function": ParseUser.guild,
                "args": [[int]],
                "str": "in guild %0"
            }
        },
        "data": {},
        "format": {
            "data": {},
            "function": ParseUser.format
        }
    },
    "channel": {
        "main": ParseChannel.main,
        "str": "a discord channel",
        "functions": {
            "type": {
                "function": ParseChannel.channel_type,
                "args": [[str]],
                "str": "of type %0"
            },
            "rights": {
                "function": ParseChannel.rights,
                "args": [[str]],
                "str": "with %0 permissions"
            }
        },
        "data": {},
        "format": {
            "data": {},
            "function": ParseChannel.format
        }
    }
}