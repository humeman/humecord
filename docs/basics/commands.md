# commands system
## creating commands

Each command should be contained in its own class.
This class does not have to extend any HumeCord class - 
it will be parsed by the command handler instead.

For example:
```py
class SampleCommand:
    def __init__(self):
        self.name = "sample"
        self.description = "A sample command"
        (...)

    async def run(
            self,
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):
        # Command
```

## run function

The run function has a number of parameters that
are passed to it with each call.

* `message` - a discord.Message object

* `resp` - a humecord.classes.discordclasses.ResponseChannel instance
    * Learn more about ResponseChannels [here](../classes/responsechannels.md)

* `args` - a list of all arguments

* `gdb` - the guild's guild database

* `alternate_gdb` - an alternage guild database (for global bots)
    * Ex: Used in HumeBot to pass the HumeBot guild database - the `gdb` parameter is whatever the command requests instead

* `preferred_gdb` - a compiled version of the guild database with bot info
    * Ex: You should get the prefix from here - will default to whatever the current bot's database is

## keys

Below is a list of valid keys which can be used in your command class:

* `name` - The command's name

* `description` - A short description of the command, used in help commands and info commands

* `aliases` - Other names which can be used to run this command

* `shortcuts` - Aliases, but when run they're expanded to a long list of arguments
    * Ex: 
      ```py
      {
          "testcommand": "alonger command"
      }
      ```
      will expand `!testcommand` to `!alonger command`

* `args` - Arguments which are passed through the argument validator.

* `permission` - A default permission. Can be overriden by guild, which is checked in the command handler.
    * Learn more about permissions [here](../misc/permissions.md)

* `subcommands` - A list of subcommands to automatically expand to
    * Should be a dict, formatted as:
    ```py
    {
        "name": self.function
    }
    ```
    * Functions are called with the same base arguments as `self.run()`.
    * Use the following names for fallback cases:
        * `__default__` - Called if no subcommand is specified.
        * `__syntax__` - Called when an invalid subcommand is passed, or if no subcommand is specified and there's no __default__.
