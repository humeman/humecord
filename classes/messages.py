import humecord
from typing import Optional

from humecord.utils import (
    discordutils,
    exceptions
)

class Messenger:
    def __init__(
            self,
            bot
        ):

        # Need to access before initialization
        self.bot = bot

        # Load in default messages
        self.messages = bot.config.messages

    def find(
            self,
            path: list
        ):

        current = self.messages

        for name in path:
            if name not in current:
                raise humecord.utils.exceptions.NotFound(f"Path {'.'.join(path)} not in messages ({name})")
            
            current = current[name]

        return current

    def parse_placeholders(
            self,
            message: str,
            placeholders: dict,
            conditions: dict,
            allow_config_placeholders: bool = False
        ):
        comp = []

        # Add in default placeholders
        for line in message.split("\n"):
            if ":::" in line and line.startswith("if"):
                condition, msg = line.split(":::", 1)

                if "[" in condition and "]" in condition:
                    detail = condition.split("[", 1)[1].rsplit("]", 1)[0]

                    if ":" in detail:
                        check_type, var = detail.split(":", 1)

                        if check_type == "exists":
                            if placeholders.get(var) is not None:
                                comp.append(msg)
                            
                            continue

                        else:
                            raise humecord.utils.exceptions.InvalidStatement(f"Can't use if condition with check type {check_type}")

                    else:
                        if conditions.get(detail) is not None:
                            comp.append(msg)

                        continue

        # Add in config placeholders
        if allow_config_placeholders:
            comp_ = []
            for word in "\n".join(comp).split(" "):
                if not word.startswith("%-"):
                    continue

                ext = ""
                if word.endswith("\n"):
                    ext = "\n"
                    word = word[:-1]

                if word.startswith("%-lang:::"):
                    search = humecord.bot.config.lang

                elif word.startswith("%-config:::"):
                    search = humecord.bot.config

                elif word.startswith("%-globals:::"):
                    search = humecord.bot.config.globals

                else:
                    comp_.append(f"{word}{ext}")
                    continue

                # Get location
                location = word.split(":::", 1)[1]

                if location.endswith("%"):
                    location = location[:-1]

                    # Get value
                    if type(search) == dict:
                        current = search

                        for path in location.split("."):
                            if path in current:
                                current = current["path"]

                            else:
                                comp_.append(f"{word}{ext}")
                                continue

                        if type(current) not in [str, int, float, bool, None]:
                            comp_.append(f"{word}{ext}")
                            continue

                        # Add
                        comp_.append(str(current))
                    
                else:
                    comp_.append(f"{word}{ext}")

            message = " ".join(comp_)

        else:
            message = "\n".join(comp)

        for placeholder, value in placeholders.items():
            message = message.replace(f"%{placeholder}%", str(value))

        return message

    def parse_embed(
            self,
            embed: dict,
            placeholders: dict,
            conditions: dict
        ):

        comp = {}

        for key, value in embed.items():
            if key in ["title", "description", "footer", "thumbnail", "image", "color"]:
                comp[key] = self.parse_placeholders(value, placeholders, conditions)

            elif key in ["profile"]:
                comp[key] = []

                for item in value:
                    comp[key].append(
                        self.parse_placeholders(
                            item,
                            placeholders,
                            conditions
                        )
                    )

            elif key in ["fields"]:
                comp[key] = []

                for item in value:
                    comp[key].append(
                        {
                            x: self.parse_placeholders(y, placeholders, conditions)
                            for x, y in item.items() if type(y) != str
                        }
                    )

            else:
                raise humecord.utils.exceptions.InvalidKey(f"Unknown key: {key}")

        return humecord.utils.discordutils.create_embed(**comp)

    async def get(
            self,
            gdb: dict,
            path: list,
            placeholders: dict,
            conditions: dict = {},
            force_type: Optional[str] = None,
            ext_placeholders: dict = {}
        ):

        # Follow path
        msg = self.find(path)

        # Check if guild has overridden
        try:
            override = humecord.utils.miscutils.follow(gdb["messages"], path)

        except:
            override = None
            use = msg

        else:
            use = {
                **msg,
                **override
            }

        m_type = msg["default"] if force_type is None else force_type

        if msg["allow_override"]:
            if "type_override" in msg:
                m_type = msg["type_override"]

        # Add extra placeholders
        placeholders = {
            **(await self.get_ext_placeholders(ext_placeholders)),
            **placeholders
        }

        kwargs = {}

        if m_type == "str":
            content = self.parse_placeholders(
                msg["content"],
                placeholders,
                conditions
            )

            kwargs["content"] = content

        elif m_type == "embed":
            embed = self.parse_embed(
                msg["embed"],
                placeholders,
                conditions
            )

            kwargs["embed"] = embed

        elif m_type == "both":
            kwargs["content"] = self.parse_placeholders(
                msg["content"],
                placeholders,
                conditions
            )
            kwargs["embed"] = self.parse_embed(
                msg["embed"],
                placeholders,
                conditions
            )

        else:
            raise exceptions.DevError(f"mtype '{m_type}' doesn't exist")

        return kwargs

    async def get_ext_placeholders(
            self,
            data: dict
        ):

        comp = {}

        if "message" in data:
            m = data["message"]
            comp.update(
                {
                    "message_id": str(m.id),
                    "guild": m.guild.name,
                    "guild_id": str(m.guild.id),
                    "guild_avatar": m.guild.icon.url,
                    "channel": m.channel.name,
                    "channel_mention": m.channel.mention,
                    "channel_id": str(m.channel.id),
                    "user": f"{m.author.name}#{m.author.discriminator}",
                    "user_id": str(m.author.id),
                    "user_avatar": str(m.author.avatar.url)
                }
            )
        
        if "user" in data:
            u = data["user"]
            comp.update(
                {
                    "user": f"{u.name}#{u.discriminator}",
                    "user_id": str(u.id),
                    "user_avatar": str(u.avatar.url)
                }
            )
        
        return comp
        