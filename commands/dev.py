import humecord
import discord

class DevCommand:
    def __init__(self):
        self.name = "dev"

        self.description = "All HumeCord development controls."

        self.aliases = ["development"]

        self.permission = "bot.dev"

        self.subcommands = {
            "error": self.error
        }

    async def error(self, message, resp, args, gdb, alternat_gdb = None, preferred_gdb = None):
        #raise humecord.utils.exceptions.TestException("dev.error call")
        #raise KeyError("helo this is And err'or")

        9 + "10" == 21