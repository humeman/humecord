# migrating to 0.4

Humecord 0.4 is a major update which brings a number of new features and refreshes, which unfortunately come with some major breaking changes. Before using 0.4 in your bots, please follow the steps contained in this guide to get them prepared for use.

## table of contents

1. [updating humecord](#updating-humecord)
2. [new config options](#new-config-options)
3. [command migration](#command-migration)
4. [component changes](#component-changes)

## updating humecord

Follow the normal installation guide contained on the [home page](/README.md). In short:
1. Clone the repo: `git clone https://github.com/humeman/humecord` and `cd humecord`
2. Remove old symbolic links: `rm -r ~/.local/lib/python3.[python version here -- press tab]/site-packages/humecord` (sample on Linux -- varies from platform to platform. check your PYTHONHOME variable)
3. Create a new symbolic link: `ln -s [full_path_to_humecord_repo]/humecord [full_path_to_python_home]/site-packages/humecord`
4. Install requirements: `pip3 install -r requirements.txt`

## new config options

As always, you can just start your bot to get a nice copy-pastable output of all new config options.

If you use the Users API, the following value has to be added:
```yml
# API category for retrieving users.
user_api: users
```

The following option has to be added: Due to Discord limitations, we can't check permissions before displaying a command to the user -- only after execution. To keep other guilds clean, dev commands are now restricted to a predefined list of guilds. This is not applicable to message commands.
```yml
# Restricts any commands with 'self.dev = True' to these guild IDs for slash command registration.
dev_guilds: 
  - 782851458671968276
```

## command migration

This is the change which will require the most restructuring to implement:
- New basic command format
- Response channels
- Context class
- Args class
- Permissions

### a. New format
All command classes now follow a new format:

__Sample: Single-function command (no subcommands)__
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
            "/%test%": self.run
        }

        # Arguments, if any exist
        self.args = {
            "test": {
                "type": "number",
                "required": True,
                "description": "A number." # required
            }
        }

        # Info for message-based commands -- not applicable for slash commands
        self.messages = {
            "aliases": ["testingcommand"],
            "shortcuts": {
                "testthecommand": "test 123" # from -> to (!testthecommand will become !test 123)
            }
        }

        # Required: initialize parent command
        super().__init__()

    async def run(
            self,
            resp,
            ctx
        ) -> None:
        await resp.send(
            f"Your number is: {ctx.args.test}"
        )
```

__Sample: Subcommands__
```py
import humecord

class SubcommandCommand(humecord.Command):
    def __init__(self) -> None:
        # Command name
        self.name = "subcommand"

        # Description (100 chars or less)
        self.description = "A testing command to demonstrate using subcommands."

        # Command tree
        self.command_tree = {
            "/mysubcommand": self.mysubcommand,
            "/anothersubcommand/%testargument%": self.anothersubcommand
        }

        # Arguments, if any exist
        self.args = {
            "testargument": {
                "type": "user",
                "required": True,
                "description": "A Discord user." # required
            }
        }

        # Info for message-based commands -- not applicable for slash commands
        self.messages = {
            "aliases": ["testsubcommands"],
            "shortcuts": {
                "mysubcommand": "test mysubcommand", # from -> to (!mysubcommand will become !test mysubcommand),
                "anothersubcommand": "test anothersubcommand"
            }
        }

        # Required: initialize parent command
        super().__init__()

    async def mysubcommand(
            self,
            resp,
            ctx
        ) -> None:
        await resp.send(
            "You picked the first subcommand!"
        )

    async def anothersubcommand(
            self,
            resp,
            ctx
        ) -> None:
        await resp.send(
            f"Hey, {ctx.args.user.mention}!"
        )
```

__Creating a command tree__

Each command is expected to have a command tree defined, which gives all possible subcommands and their corresponding callbacks.
For example, the command
```
/sample user [@user: required]
    /sample user [@user] (option1)
    /sample user [@user] (option2)
/sample othersubcommand
```
would become

```py
self.command_tree = {
    "/user/%user%/%option%": self.user,
    "/othersubcommand": self.othersubcommand
}

self.args = {
    "user": {
        "description": "A discord user to run an action on.",
        "type": "user",
        "required": True
    },
    "option": {
        "description": "The option you want.",
        "type": "option",
        "required": False
        "options": [
            "option1",
            "option2"
        ]
    }
}
```

A command tree with no subcommands could be formatted as such:
```py
# /commandname

self.command_tree = {
    "/": self.run
}
```

or, with args:
```py
# /commandname [arg1] (arg2)

self.command_tree = {
    "/%arg1%/%arg2%": self.run
}

self.args = {
    "arg1": {
        "type": "number",
        "required": True,
        "description": "A number"
    },
    "arg2": {
        "type": "user",
        "required": False,
        "description": "A discord user"
    }
}
```
*NOTE*: Due to a Discord limitation, you cannot have a root (/name, no subcommand) command if it has subcommands.
    For example:
    /sample             <- doesn't work
    /sample option1 ...
    /sample option2 ...
    /sample %user%      <- also doesn't work - this is an arg to the root command

### b. Response channel

Each command now takes only two arguments instead of the previous 9 or something: `resp` and `ctx`.

The `resp` argument now contains methods to send messages back to the user, which are all consistent regardless of whether the command was executed using slash commands, message commands, or other interactions.

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

### c. Context

The other argument, `ctx`, contains all the old arguments which were passed to commands: message, interaction, udb, gdb, args, and so on.
This allows for much more flexibility in the usage of commands.

__All context params__
* `type` (humecord.ContextTypes): `humecord.ContextTypes.SLASH` or `.MESSAGE`
* `resp` (humecord.ResponseChannel): The interaction's response channel
* `interaction` (discord.Interaction): The interaction, if activated using one
* `channel` (discord.TextChannel): The text channel from which the interaction originated
* `hcommand` (humecord.Command): The humecord command executed
* `command` (discord.app_commands.Command): The discord app command object executed
* `args` (humecord.classesdiscordclasses.Args): An object containing all args
* `user` (discord.User, discord.Member): User who ran the command

### d. Args

All commands now are *required* to use name-key style arguments, as existed with the argument parser in the old command system.

They are available in `ctx.args`.

__Sample: Check and use arguments__
```py
async def run(self, resp, ctx) -> None:
    # Check if an argument exists (only necessary if the arg isn't required in command.args)
    if ctx.args.exists("myargument"):
        await resp.send(
            f"Your argument is: {ctx.args.myargument}"
        )

    else:
        await resp.send(
            "You didn't supply an argument! :("
        )
```

### e. Permissions

Permissions are now done a bit differently.

With slash commands, guild owners now have the ability to override the permissions of any slash command or subcommand. To set the default permissions of a command, use:
```py
# If you want to use a Humecord permission node (only guild.admin, guild.mod, or guild.any)
self.default_perms = "guild.admin"

# If you want to manually specify permissions
# https://discordpy.readthedocs.io/en/latest/api.html#discord.Permissions for names
self.default_perms = [
    "manage_roles",
    "kick_members"
]

# Can also be done on a subcommand basis
self.subcommand_details = {
    "mysubcommand": {
        "description": "...",
        "default_perms": "guild.mod"
    }
}
```

Note that this permission *can* be overridden by any guild owner, so development commands still need some extra work:
```py
# Hides the command on any guild not specified in config.dev_guilds
self.dev = True

# Verifies the user's Humecord permission node before running
# https://github.com/humeman/humecord/blob/main/docs/misc/permissions.md
self.perms = "bot.dev"
```

You can also still use the old Humecord permission nodes to ensure no one uses a command they shouldn't. This is highly recommended for commands that could have a high impact if used by the wrong person -- don't trust the guild owner to set it up right. Applies to the base command and all subcommands.
```py
# https://github.com/humeman/humecord/blob/main/docs/misc/permissions.md
self.perms = "bot.dev"
```

You can also restrict a command to only run inside of a guild with:
```py
self.guild_only = True
``` 

## component changes

`humecord.utils.components` has been removed in favor of a helper class: `bot.interactions`. Setup is virtually the same.

Some main differences:
- All functions are now async
- Components don't rely on a message anymore and use a randomized UUID in place of message ID
- Instead of passing additional args, all component data is now in `ctx`
- Args have been reformatted to be more intuitive

Docs are in the works. In the meantime, you can check the docstrings for `.create_button(), .create_view(), .create_select(), .create_textinput()` [here](/humecord/classes/interactions.py) (or by hovering over the function in VSCode).

__Sample: making a button__
```py
async def run(self, resp, ctx) -> None:
    components = [
        await bot.interactions.create_button(
            name = "mybutton1", # Cannot have duplicate names of any components in the same message
            callback = lamda *args: self.callback(*args, "Woohoo!"), # Lambdas are not required -- just for any extra data you may need to pass
            label = "Click me!",
            style = humecord.ButtonStyles.SUCCESS
        ),
        await bot.interactions.create_button(
            name = "mybutton1", # Cannot have duplicate names of any components in the same message
            callback = lamda *args: self.callback(*args, ":("),
            label = "Don't click me.",
            style = humecord.ButtonStyles.DANGER
        )
    ]

    view = await bot.interactions.create_view(
        components
    )

    await resp.send(
        "Here are some buttons!",
        view = view
    )

async def callback(self, resp, ctx, response_string) -> None:
    await resp.edit(
        response_string
    )
```