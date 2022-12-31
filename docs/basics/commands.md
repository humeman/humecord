### [humecord](../..)/[docs](../README.md)/[basics](./README.md)/commands

---
# humecord basics
## creating commands

There are three main steps to adding a command to Humecord:
1. [Creating a command class](#creating-a-command-class)
2. [Adding callbacks](#adding-callbacks)
3. [Registering with the loader](#registering-with-the-loader)

### creating a command class

*Changed in:* Humecord 0.4

Command classes inherit the `humecord.Command` class and contain all the details and callbacks for your command.
Each one should be held in a separate file in the `commands` folder of your project.

For example, say I have commands `test` and `sample`:
```
my_bot/
 |_ commands
 |  |_ test.py
 |  |_ sample.py
 |_ main.py
 |_ imports.py
 ....
 ```

Here's sample on how to generate a command:
```py
import humecord

class TestCommand(humecord.Command):
    def __init__(self) -> None:
        # Command name
        self.name = "test"

        # Description (100 chars or less)
        self.description = "A testing command to demonstrate the new command format."

        # Command tree
        self.command_tree = {
            "": self.some_callback
        }

        # Arguments, if any exist
        self.args = {}

        # Info for message-based commands -- not applicable for slash commands
        # If not specified, the command will be slash only
        self.messages = {
            "aliases": ["testingcommand"],
            "shortcuts": {}
        }

        # Required: initialize parent command
        super().__init__()
```

Your `__init__` function is where you define all the information about your command.
Here are the possible attributes you can set:
* `.name (str)`: Your command's name. Due to Discord limitations, this must be between 1 and 32 characters long.
* `.description (str)`: The description displayed in command info messages and the slash command menu. 1-100 chars.
* `.command_tree (dict[str, Callable])`: The command's command tree.
    * The key is the command's subcommand (if applicable) and all args, and the value is an async callback.
    * Each command tree entry is a new subcommand, and contains all the possible args for that command. For example:
    * *No subcommands*: `self.command_tree = {"": self.some_callback}` -> `/command`
    * *No subcommands, args*: `self.command_tree = {"%arg%": some_callback}` -> `/command [arg]`
    * *Subcommands*: `self.subcommand_tree = {"subcommand1": self.subcommand1, "subcommand2 %somearg%": self.subcommand2}` -> `/command subcommand1`, `/command subcommand2 [somearg]`
    * **Note:** See 'arguments' section below for how to define `%arg%` and `%somearg%`.
* `.args (dict[str, dict[str, Any]])`: All the command's args.
    * The general structure for this is:
      ```py
      self.args = {
        "[arg name]": {
            "type": "[arg type]",
            "description": "[arg description, 1-100 chars]",
            "required": bool,   # optional: defaults to False
            "choices": [        # optional: if you want to autofill some choices
                "choice1",      # must match argument type and be a string, integer, or number
                "choice2"
            ]
        }
      }
      ```
    * Continuing the example above, if we wanted `somearg` to be a required integer and `arg` to be an optional string:
      ```py
      self.args = {
        "somearg": {
            "type": "int",
            "description": "Some argument",
            "required": True
        },
        "arg": {
            "type": "str",
            "description": "Another argument",
            "required": False
        }
      }
      ```
    * Args are accessed via `ctx.args` in a command callback. Learn more [here](#command-arguments)
* `.messages (dict[str, Any])`: Contains information for running this command via messages.
    * If this is not supplied, the command will be slash only.
    * Possible keys/values:
        * `aliases (list[str])`: Name aliases for the command.
        * `shortcuts (dict[str, str])`: Shortcuts to subcommands:
            * ```py
              "shortcuts": {
                # from   :   to
                "newname": "commandname somesubcommand"
              }
              ```
* `.perms (str)`: A Humecord permission string required to execute the command.
    * For a list of possible permission strings, see [this doc page](../misc/permissions.md).
    * If not supplied, anyone can run the command.
* `.default_perms (list[str] or str)`: Default permissions set to run the command as a slash command.
    * This is overridable by a guild admin. It's strongly encouraged to set a `.perms` requirement for important commands.
    * Can be a Humecord `guild.` permission string (one of `guild.admin`, `guild.mod`, `guild.any`), or a list of [Discord permissions](https://discordpy.readthedocs.io/en/stable/api.html#permissions) required.
* `.guildonly (bool)`: If True, the command can only be run in a Discord guild (not in DMs). Defaults to False.
* `.dev (bool)`: If True, the command will only be registered as a slash command in your dev guilds (defined in `config.yml/dev_guilds`). Does not affect message commands, so you should still set a `self.perms` permission if True.

### adding callbacks
The callback for each subcommand is the value to the corresponding path in the command tree. For example:
```py
self.command_tree = {
    "subcommand1": self.subcommand1, # Goes to self.subcommand1(ctx, resp)
    "subcommand2": self.subcommand2  # Goes to self.subcommand2(ctx, resp)
}
```

Callbacks are defined with two parameters: resp (`humecord.classes.discordclasses.ResponseChannel`) and ctx (`humecord.classes.discordclasses.Context`).

**response channels**

The `resp` argument contains methods to send messages back to the user, which are all consistent regardless of whether the command was executed using slash commands, message commands, or other interactions.

__Sample: Using a response channel__
```py
async def run(self, resp, ctx) -> None:
    # Send a brand new message to the user
    await resp.send(
        "This is a message",
        embed = humecord.utils.discordutils.create_embed("This is an embed"),
        ephemeral = True    # Ignored if not interaction-based. Makes the message display to only the sender.
    )

    # Edit the original message
    await resp.edit(
        "This is a different message",
        embed = humecord.utils.discordutils.create_embed("This is a new embed")
    )
    # Important note about resp.edit():
    # If a message hasn't already been sent, it will send a new one.
    # This is useful for component-based interactions in that you don't have to keep track of whether or not a message has been sent yet.
```
They can have the following methods and attributes:
* `.message` or `.interaction`, depending on if the interaction is from a message or slash command/component
* `async .send(*args, **kwargs)`: Sends a message using normal Discord.py syntax
    * You can specify `ephemeral = True` here if you want the reply to be visible to only the user who executed the command. Only works in slash commands, and is ignored for message commands.
* `async .edit(*args, **kwargs)`: Edits the previously sent message. If one has not yet been sent, it will send a new one.
    * `ephemeral` kwarg works here too
* `async .embed(*args, **kwargs)`: Generates an embed using your kwargs (same args as `discordutils.create_embed`) and sends it.
* `async .error(*args, **kwargs)`: Generates an error embed using your kwargs (same args as `discordutils.error`) and sends it.

**context**
The other argument, `ctx`, contains all the old arguments which were passed to commands: message, interaction, udb, gdb, args, and so on.
This allows for much more flexibility in the usage of commands.

Possible attributes:
* `type` (humecord.ContextTypes): `humecord.ContextTypes.SLASH` or `.MESSAGE`
* `resp` (humecord.ResponseChannel): The interaction's response channel
* `interaction` (discord.Interaction): The interaction, if activated using one
* `channel` (discord.TextChannel): The text channel from which the interaction originated
* `hcommand` (humecord.Command): The humecord command executed
* `command` (discord.app_commands.Command): The discord app command object executed
* `args` (humecord.classesdiscordclasses.Args): An object containing all args
* `user` (discord.User, discord.Member): User who ran the command
* `gdb` (dict): Guild's GDB, if ran in a guild
* `guild` (discord.Guild): Guild command was executed in, if applicable
* `udb` (dict): User's bot UDB

### adding callbacks
Callbacks are async functions which are given two arguments at runtime: `resp` and `ctx` (in that order).

For example, if the command tree function is `self.run`, define the function as:
```py
async def run(
        self,
        resp: humecord.ResponseChannel,
        ctx: humecord.Context
    ) -> None:
    # your code here
```

You can also utilize the built in `lambda` function to pass extra arguments to a function.

In the following example, we have the same callback `self.run`, with an extra argument called `subcommand_number`.

If the user calls subcommand 1, `1` is passed, and so on.

```py
# __init__()
    self.command_tree = {
        "subcommand1": lambda *args: self.run(*args, 1),
        "subcommand2": lambda *args: self.run(*args, 2),
        "subcommand3": lambda *args: self.run(*args, 3)
    }

async def run(
        self,
        resp: humecord.ResponseChannel,
        ctx: humecord.Context,
        subcommand_number: int
    ) -> None:
    await resp.send(f"You ran subcommand #{subcommand_number}.")
```

### registering with the loader
To register a command, loop, or event to Humecord, you simply add an entry to your `imports.py` file.

You can learn more about the general structure of an imports file [here](./loader.md).

If your command is named `mycommand.py`, the class is named `MyCommand`, the file is located in a folder named `commands`, and you wish to add the command to the `general` category, your import would look like so:
```py
# __init__
    self.loader = {
        "commands": {
            "general": [
                {
                    "imp": "from commands import mycommand",
                    "module": "mycommand",
                    "class": "MyCommand"
                }
            ]
        }
    }
```