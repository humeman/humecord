from enum import Enum

import discord

# classes/commandhandler
class CmdTypes(Enum):
    COMMAND = 0
    GROUP = 1
    SUBCOMMAND = 2

# classes/discordclasses
class ContextTypes(Enum):
    COMPONENT = 0
    SLASH = 1
    MESSAGE = 2

# classes/interactions
class ComponentTypes(Enum):
    BUTTON = 0
    SELECT = 1
    TEXTINPUT = 2
    MODAL = 3

class ComponentArgTypes(Enum):
    ANY = 0
    SELECT = 1
    MODAL = 2
    PERMA = 3

class ButtonStyles(Enum):
    PRIMARY = discord.ButtonStyle.primary
    BLUE = discord.ButtonStyle.primary
    SECONDARY = discord.ButtonStyle.secondary
    GRAY = discord.ButtonStyle.secondary
    GREY = discord.ButtonStyle.secondary
    SUCCESS = discord.ButtonStyle.success
    GREEN = discord.ButtonStyle.green
    DANGER = discord.ButtonStyle.danger
    RED = discord.ButtonStyle.danger
    HYPERLINK = discord.ButtonStyle.link
    LINK = discord.ButtonStyle.link
    URL = discord.ButtonStyle.link

# classes/msgadapter
class ActivatorTypes(Enum):
    REPLACE = 1
    SHORTCUT = 2