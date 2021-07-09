

class SettingsCommand:
    def __init__(
            self
        ):

        self.name = "settings"

        self.description = "Manages the settings of the bot in this server."

        self.aliases = ["config", "configuration"]

        self.permission = "guild.admin"

        self.subcommands = {
            "__default__": {
                "function": self.list,
                "description": "Lists all your settings."
            },
            "__syntax__": {
                "function": self.edit,
                "description": "Manages your settings."
            }
        }

        global bot
        from humecord import bot