from enum import Enum

import discord

# classes/commandhandler
class CmdTypes(Enum):
    COMMAND     = 0
    GROUP       = 1
    SUBCOMMAND  = 2

# classes/discordclasses
class ContextTypes(Enum):
    COMPONENT   = 0
    SLASH       = 1
    MESSAGE     = 2

class RespTypes:
    NONE        = 0
    MESSAGE     = 1
    INTERACTION = 2
    THREAD      = 3

# classes/interactions
class ComponentTypes(Enum):
    BUTTON      = 0
    SELECT      = 1
    TEXTINPUT   = 2
    MODAL       = 3

class ComponentArgTypes(Enum):
    ANY     = 0
    SELECT  = 1
    MODAL   = 2
    PERMA   = 3

class ButtonStyles(Enum):
    PRIMARY         = discord.ButtonStyle.primary
    BLUE            = discord.ButtonStyle.primary
    SECONDARY       = discord.ButtonStyle.secondary
    GRAY            = discord.ButtonStyle.secondary
    GREY            = discord.ButtonStyle.secondary
    SUCCESS         = discord.ButtonStyle.success
    GREEN           = discord.ButtonStyle.green
    DANGER          = discord.ButtonStyle.danger
    RED             = discord.ButtonStyle.danger
    HYPERLINK       = discord.ButtonStyle.link
    LINK            = discord.ButtonStyle.link
    URL             = discord.ButtonStyle.link

# classes/msgadapter
class ActivatorTypes(Enum):
    REPLACE     = 1
    SHORTCUT    = 2

# classes/discordutils
class TimecodeFormats(Enum):
    SHORT_TIME      = ":t"
    LONG_TIME       = ":T"
    SHORT_DATE      = ":d"
    LONG_DATE       = ":D"
    DATE_TIME       = ":f"
    LONG_DATE_TIME  = ":F"
    RELATIVE        = ":R"

STR_TO_TIMECODE = {
    "short_time": TimecodeFormats.SHORT_TIME,
    "long_time": TimecodeFormats.LONG_TIME,
    "short_date": TimecodeFormats.SHORT_DATE,
    "long_date": TimecodeFormats.LONG_DATE,
    "date_time": TimecodeFormats.DATE_TIME,
    "long_date_time": TimecodeFormats.LONG_DATE_TIME,
    "relative": TimecodeFormats.RELATIVE
}

# general
VISIBILITIES = {
    "online": discord.Status.online,
    "offline": discord.Status.offline,
    "idle": discord.Status.idle,
    "dnd": discord.Status.dnd,
    "invisible": discord.Status.invisible
}

ACTIVITIES = {
    "playing": discord.ActivityType.playing,
    "streaming": discord.ActivityType.streaming,
    "listening": discord.ActivityType.listening,
    "watching": discord.ActivityType.watching,
    "competing": discord.ActivityType.competing
}

