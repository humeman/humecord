"""
/logs: humecord base commands

Discord log viewer.
"""

from typing import Optional

import humecord

from humecord.classes import (
    discordclasses
)

from humecord.utils import (
    discordutils
)

class DevCommand(humecord.Command):
    def __init__(
            self
        ) -> None:
        self.name = "dev"
        self.description = "Extra bot controls."
        self.command_tree = {
            "reload %force%": self.reload,
            "close": self.close,
        }
        self.args = {
            "force": {
                "type": "bool",
                "required": False,
                "description": "Forces a reload without gracefully shutting down components first."
            }
        }
        self.subcommand_details = {
            "reload": {
                "description": "Reloads the bot's config, commands, loops, and events."
            },
            "close": {
                "description": "Shuts down the bot."
            }
        }
        self.messages = {}
        self.dev = True
        self.perms = "bot.dev"
        self.default_perms = "guild.admin"

        global bot
        from humecord import bot