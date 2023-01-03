"""
humecord/classes/commandhandler/CommandHandler

Handles interaction-based (slash command) commands.
Replacement for the previous MessageCommandHandler (deprecated).
"""
import json # FIXME: temp

import discord
from typing import Any, Optional, Union
import time

import humecord

from humecord.classes import (
    discordclasses
)

from humecord.utils import (
    discordutils,
    exceptions,
    errorhandler
)


class CommandHandler:
    def __init__(
            self
        ) -> None:
        """
        Initializes a command handler object.
        """

        global bot
        from humecord import bot

        try:
            self.slashtree = discord.app_commands.CommandTree(bot.client)

        except discord.errors.ClientException:
            self.slashtree = bot.client._connection._command_tree

        self.tree = {}
        self.imports = {}
        self._prep_finished = False

        self.stat_cache = {
            "__total__": 0,
            "__denied__": 0
        }

    def reset(
            self
        ) -> None:
        """
        Resets all prepped vars.
        """
        self.tree = {}
        self.imports = {}
        self.dtree = {}
        self._prep_finished = False

    async def prep_loader(
            self
        ) -> None:
        """
        Prepares a command tree for the Humecord Loader to do its magic on.
        """

        # Update our command list
        await self.imp_generate_default_commands()

    async def imp_generate_default_commands( 
            self
        ) -> None:
        """
        Grabs and compiles a default command import tree.
        """
        defaults = {
            "about": {
                "imp": "from humecord.commands import about",
                "module": "about",
                "class": "AboutCommand"
            },
            "botban": {
                "imp": "from humecord.commands import botban",
                "module": "botban",
                "class": "BotBanCommand"
            },
            "dev": {
                "imp": "from humecord.commands import dev",
                "module": "dev",
                "class": "DevCommand"
            },
            "devinfo": {
                "imp": "from humecord.commands import devinfo",
                "module": "devinfo",
                "class": "DevInfoCommand"
            },
            "dm": {
                "imp": "from humecord.commands import dm",
                "module": "dm",
                "class": "DMCommand"
            },
            "exec": {
                "imp": "from humecord.commands import execcmd",
                "module": "execcmd",
                "class": "ExecCommand"
            },
            "profile": {
                "imp": "from humecord.commands import profile",
                "module": "profile",
                "class": "ProfileCommand"
            },
            "settings": {
                "imp": "from humecord.commands import settings",
                "module": "settings",
                "class": "SettingsCommand"
            },
            "sync": {
                "imp": "from humecord.commands import sync",
                "module": "sync",
                "class": "SyncCommand"
            }
        }
        
        commands = {}

        for command, overrides in bot.config.default_commands.items():
            if command not in defaults:
                continue

            category = overrides.get("__category__")

            if category is None:
                category = "dev"

            if category not in commands:
                commands[category] = []

            commands[category].append(
                {
                    **defaults[command],
                    "attrs": overrides
                }
            )

        for category, cmds in commands.items():
            await self.imp_add_command_category(
                category,
                cmds
            )

    async def imp_add_command_category(
            self,
            category: str,
            commands: dict
        ) -> None:
        """
        Registers a category w/ commands to the internal imports store.
        """

        if category not in self.imports:
            self.imports[category] = []

        self.imports[category] += commands

    async def get_import_tree(
            self
        ) -> dict:
        """
        Retuns the current import tree.
        """

        return self.imports

    async def add_command(
            self,
            category: str,
            command: discord.app_commands.Command
        ) -> None:
        """
        Adds a command class to the tree.
        """

        if category not in self.tree:
            self.tree[category] = []

        self.tree[category].append(command)

    async def sync(
            self
        ):
        """
        Syncs the command tree to Discord.
        """

        self.slashtree.clear_commands(guild = None)
        counter = 0
        self.dtree = {}

        # Generate a group for each category
        for category, commands in self.tree.items():
            cmds = []

            for command in commands:
                # Generate a command from the hcommand class
                cmd = command._init_cmd(category)

                cmds.append(cmd)

                # Push to slash tree
                self.slashtree.add_command(
                    cmd
                )

                # Store the discord class in the hcommand
                command.dcommand = cmd

            self.dtree[category] = {
                "name": category,
                #"group": group,
                "commands": cmds
            }
            counter += 1

        # Once commands are all added, sync it (temporary: will be a command later)
        #self.slashtree.copy_global_to(guild = humecord.bot.client.get_guild(782851458671968276))
        #ret = await self.slashtree.sync(guild = humecord.bot.client.get_guild(782851458671968276))
        #print(ret)
        humecord.logger.log_step("botinit", "start", f"Registered {counter} commands")
        self._prep_finished = True

    async def sync_to(
            self,
            guild: discord.Guild,
            copy: bool = False
        ) -> int:
        """
        Syncs the local command tree to a single guild.
        
        Params:
            guild (discord.Guild): Target guild to sync to
            copy (bool = False): If True, the global command tree will be copied to this guild
            
        Returns:
            count (int): Commands synced
        """
        if not self._prep_finished:
            raise exceptions.DevError("Command tree is not prepared yet.")

        if copy:
            self.slashtree.copy_global_to(guild = guild)
            
        return len(await self.slashtree.sync(guild = guild))

    async def clear_tree(
            self,
            guild: discord.Guild
        ) -> None:
        """
        Clears a guild's local command tree.
        
        Params:
            guild (discord.Guild): Target guild to clear
        """
        if not self._prep_finished:
            raise exceptions.DevError("Command tree is not prepared yet.")

        self.slashtree.clear_commands(guild = guild)
        cmds = await self.slashtree.sync(guild = guild)

        if len(cmds) != 0:
            raise exceptions.DevError(f"Tree was not cleared successfully.")

    async def sync_global(
            self
        ) -> int:
        """
        Syncs the local command tree globally. Changes take a while to propogate.
            
        Returns:
            count (int): Commands synced
        """
        if not self._prep_finished:
            raise exceptions.DevError("Command tree is not prepared yet.")
        
        return len(await self.slashtree.sync())

    async def call_command(
            self,
            interaction: discord.Interaction,
            func,
            args: discordclasses.Args
        ) -> None:
        """
        Called on command interaction reciept.

        Params:
            interaction (discord.Interaction)
            func: Async callback to run (with params resp, ctx)
            args (discordclasses.Args): Args object to represent user data
        """
        # -> Find out what command this was
        command = interaction.command

        # Get the hcommand
        hcommand = command.extras.get("hcommand")

        if hcommand is None:
            raise exceptions.InvalidCommand("Command has no hcommand defined. Report this bug!")

        # -> Compile a RespChannel to the interaction
        resp = discordclasses.InteractionResponseChannel(interaction)

        # -> Create context
        kw = {
            "type": humecord.ContextTypes.SLASH,
            "resp": resp,
            "interaction": interaction,
            "channel": interaction.channel,
            "hcommand": hcommand,
            "command": command,
            "args": args,
            "user": interaction.user
        }
        
        # Check for a GDB
        if interaction.guild:
            gdb = await bot.api.get(
                humecord.bot.config.self_api,
                "guild",
                { "id": interaction.guild.id, "autocreate": True }
            )

            kw["gdb"] = gdb
            kw["guild"] = interaction.guild

            # Set preferred GDB values
            kw["preferred_gdb"] = {x: gdb.get(x) for x in bot.config.preferred_gdb}

        # Get UDB
        try:
            udb = await bot.api.get(
                bot.config.user_api,
                "user",
                { "id": interaction.user.id, "autocreate": True }
            )

        except Exception as e:
            humecord.logger.log("command", "warn", "Couldn't retrieve user's UDB. Is the section enabled in the API, and defined as 'users' in endpoints.yml?")
            self.stat_cache["__denied__"] += 1
            return
        
        kw["udb"] = udb

        preferred_api = getattr(hcommand, "preferred_api", None)

        if preferred_api is not None:
            # Get that preferred API's gdb, and swap them around
            p_gdb = await bot.api.get(
                preferred_api,
                "guild",
                { "id": interaction.guild.id, "autocreate": True }
            )

            kw["alt_gdb"] = kw["gdb"]
            kw["gdb"] = p_gdb

        # Check for botban
        if udb.get("botban") is not None:
            if udb["botban"]["duration"] is not None:
                if udb["botban"]["endsat"] > time.time():
                    humecord.logger.log("command", "cmd", f"User {interaction.user} ({interaction.user.id}) is botbanned, skipping command dispatch.")
                    self.stat_cache["__denied__"] += 1
                    return
                
        # Check permissions
        if "perms" in dir(hcommand):
            if not await bot.permissions.check(interaction.user, hcommand.perms, udb, dev_override = True):
                self.stat_cache["__denied__"] += 1
                await resp.send(
                    embed = discordutils.error(
                        interaction.user,
                        "You don't have permission to run this command!",
                        f"In order to run this command, you need the permission `{hcommand.perms}`. Check with an admin if you believe this is in error." 
                    )
                )
                return

        # Now, create a Context class from all that data
        ctx = discordclasses.Context(**kw)

        # Finally, run the command
        # TODO: Add shortcuts and such to this logic
        await errorhandler.slash_wrap(func(resp, ctx), resp, ctx)

    async def get_command_from_path(
            self,
            category: Optional[str],
            command: str
        ):

        if category is None:
            category = "root"

        commands = self.tree.get(category)

        if commands is None:
            raise exceptions.NotFound(f"Category {category} doesn't exist.")

        cmd = commands.get(command)

        if cmd is None:
            raise exceptions.NotFound(f"Command {command} doesn't exist in {category}.")

        return cmd


class HumecordCommand(object):
    """
    Inheritable command class. Currently used for slash commands only, but old message-based commands will be phased out in favor of a
    message extension to these.

    class MyCommand(humecord.Command):
        def __init__(self) -> None:
            self.name = "..."           # str, 1-32 chars
            self.description = "..."    # str, 1-100 chars
            self.command_tree = {...}   # see docstring for __init__ or GitHub docs
            self.args = {...}           # ^
            super().__init__()
    """

    def __init__(
            self
        ) -> None:
        """
        Initializes a Humecord command.

        Use this to define some command arguments:

        Each command is also expected to have a command tree defined, which gives all possible slash command usages.
        For example, the command
            /sample user [@user: required]
                /sample user [@user] (option1)
                /sample user [@user] (option2)
            /sample othersubcommand
        would become

        self.command_tree = {
            "user %user% %option%": self.user,
            "othersubcommand": self.othersubcommand
        }

        self.args = {
            "user": {
                "description": "A discord user to run an action on.",
                "type": "user",
                "required": True
            },
            "option": {
                "description": "The option you want.",
                "required": False
                "choices": [
                    "option1",
                    "option2"
                ]
            }
        }

        NOTE: Due to a Discord limitation, you cannot have a root (/name, no subcommand) command if it has subcommands.
        For example:
        /sample             <- doesn't work
        /sample option1 ...
        /sample option2 ...
        /sample %user%      <- also doesn't work: this is an arg to the root command
        """

        self._params = []
        self._root_dcmd = None
        self._root_dcmd_type = None

        # Verify stuff exists
        self._req_args = ["name", "command_tree"]
        self._opt_args = {
            "args": {},
            "subcommand_details": {},
            "description": None
        }
        obj_dir = dir(self)
        for argname in self._req_args:
            if argname not in obj_dir:
                raise exceptions.DevError(f"Missing required key {argname}")

        for argname, default in self._opt_args.items():
            if argname not in obj_dir:
                setattr(self, argname, default)

    def _set_general_attrs(
            self,
            cmd: Union[discord.app_commands.Command, discord.app_commands.Group],
            subcommand: str
        ) -> dict[str, Any]:
        """
        Sets some default attrs to a Command or Group.
        
        Deals with some permissions and guilds in particular.
        """
        # Set guild IDs if this is a dev command
        do_restrict = False
        if getattr(self, "dev", False):
            do_restrict = True

        elif hasattr(self, "perms"):
            if self.perms.lower() == "bot.dev":
                do_restrict = True

        if do_restrict:
            # Restrict to only permitted guilds
            cmd._guild_ids = bot.config.dev_guilds

        if getattr(self, "guild_only", False):
            cmd.guild_only = True

        self.default_permissions = self._get_permissions(subcommand)

    def _init_cmd(
            self,
            category: str
        ) -> Union[discord.app_commands.Command, discord.app_commands.Group]:
        """
        Initializes a Discord application command from the command's data.

        Params:
            category (str): Humecord internal category name

        Returns:
            root_cmd (discord.app_commands.Command, discord.app_commands.Group): Command to add to command tree
        """
        # Store name
        self.category = category
        self.full_name = f"{category}.{self.name}"

        subcommands = {}

        # This does a few things to format the command tree into something a little easier to use:
        # 1. Iterate over each item in the tree. Check if it's a subcommand item.
        for path, func in self.command_tree.items():
            ctree = [x.strip() for x in path.split(" ") if len(x.strip()) > 0]
            if len(ctree) == 0:
                # Forces at least one iteration for commands with no args or subcommands.
                ctree = [None]

            active_subcommand = "__root__"

            # Format into args or subcommands
            for i, arg in enumerate(ctree):
                # Find out if this is a subcommand or an arg
                if arg is None:
                    arg_name = None

                elif arg.startswith("%") and arg.endswith("%"):
                    # Argument
                    # Find the name of said arg
                    arg_name = arg[1:-1].strip()

                else:
                    arg_name = None
                    # Subcommand
                    if active_subcommand == "__root__":
                        active_subcommand = arg

                    else:
                        # Attempted redefine of subcommand
                        raise exceptions.DevError(f"Attempted nest of subcommand beyond argument 1 (currently unsupported)")

                # We are guaranteed to have an active subcommand by now -- either __root__ or an arg.
                # Verify it's been registered
                if active_subcommand not in subcommands:
                    # Generate an entry for this subcommand

                    # Find our details if they exist
                    details = {
                        "name": active_subcommand,
                        "description": None
                    }
                    if "subcommand_details" in dir(self):
                        if active_subcommand in self.subcommand_details:
                            details = {
                                **details,
                                **self.subcommand_details[active_subcommand]
                            }

                    subcommands[active_subcommand] = {
                        "name": active_subcommand,
                        "func": func,
                        "args": [],
                        "details": details
                    }

                # Now append our argument to that subcommand -- after first checking that it's not being overloaded
                if arg_name is not None:
                    if arg_name not in subcommands[active_subcommand]["args"]:
                        # Check the current item at this index
                        if len(subcommands[active_subcommand]["args"]) <= i:
                            # Append it. This is the first one.
                            subcommands[active_subcommand]["args"].append(arg_name)

                        else:
                            # There's something there already -- throw an error.
                            raise exceptions.DevError(f"Attempted overload of command tree at arg={i + 1} with more than one argument")

        # Save our new command tree for callbacks
        self._subcommand_tree = subcommands

        # Verify that there is nothing in root if we have other subcommands
        if len(subcommands) > 1:
            # Check the __root__ item
            if "__root__" in subcommands:
                raise exceptions.DevError(f"Root command is set while subcommands are registered (impossible due to Discord limitation)")

        # If this is not a root-level command, we need to assign all the subcommands to a group.
        root_cmd = None
        root_cmd_type = None
        if len(subcommands) > 1: # Redundant if statement for clarity
            root_cmd_type = humecord.CmdTypes.GROUP
            root_cmd = discord.app_commands.Group(
                name = self.name,
                description = self.description,
                extras = {
                    "hcommand": self,
                    "type": humecord.CmdTypes.GROUP
                }
            )

        else:
            root_cmd_type = humecord.CmdTypes.COMMAND
            root_cmd = discord.app_commands.Command(
                name = self.name,
                description = self.description,
                callback = self._fake_callback,
                extras = {
                    "hcommand": self,
                    "type": humecord.CmdTypes.COMMAND
                }
            )

            root_cmd._callback = self._command_callback.__func__
            root_cmd.binding = self

        self._set_general_attrs(root_cmd, "__root__")

        # Now we have all the command parameters we need -- let's figure out what we need to tell dpy about them
        
        for subcommand_name, details in subcommands.items():
            # This is the tough part.
            # We have a few options here:
            # 1. Use exec() statements to force decorators to be run, and make a dummy function that forwards to call_command()
            # 2. Use some hacky stuff to manually call decorators on a Group without actually writing a function
            # 3. Try to override Discord's parameter generation

            # Attempting 2 first, since I want to avoid exec() if at all possible

            # Let's first make a command

            # Two more options for creating the parameters:
            #  -  Exec function with our args
            #  -> Hijack the internal _parameters attr in our app_commands.Commands() object with our own params

            # To implement this, I'm taking from the annotation_to_parameter() function in dpy/app_commands/transformers.py
            # https://github.com/Rapptz/discord.py/blob/7cf3cd51a5d463ae5633ec2dd43d3e397b081876/discord/app_commands/transformers.py#L824
            params = {}

            for arg in details["args"]:
                # We can get additional details about this arg from self.args
                arg_details = self.args.get(arg)

                if arg_details is None:
                    raise exceptions.DevError(f"Argument {arg} is not defined in self.args")

                # Find the discord arg type
                dtype = None
                default = None
                ext_kw = {}

                # The type can be automatically set to 'string' (for our own validation later) if argtype is 'choices'
                if "choices" in arg_details:
                    dtype = discord.AppCommandOptionType.string

                    d_choices = []

                    for choice in arg_details["choices"]:
                        d_choices.append(
                            discord.app_commands.Choice(
                                name = choice,
                                value = choice
                            )
                        )

                    # Define our extra kwargs for that
                    ext_kw["choices"] = d_choices

                else:
                    # Attempt to transform string into discord arg
                    dtype = arg_str_transform.get(arg_details["type"])

                    if dtype is None:
                        raise exceptions.DevError(f"Argument type {arg_details['type']} does not exist. Must be one of: {','.join(list(arg_str_transform))}")

                    # Get a default arg
                    default = arg_details.get("default")

                param = discord.app_commands.transformers.CommandParameter(
                    type = dtype,
                    default = default,
                    required = arg_details["required"] if "required" in arg_details else True, # only True or False, avoids None assignments
                    name = arg,
                    description = arg_details.get("description"),
                    **ext_kw
                )

                params[arg] = param

            # Assign the params to the subcommand -- this means either creating a subcommand or just setting cmd._params
            if root_cmd_type == humecord.CmdTypes.GROUP:
                # Make a subcommand
                cmd = discord.app_commands.Command(
                    name = subcommand_name,
                    description = details["details"].get("description"),
                    callback = self._fake_callback,
                    extras = {
                        "hcommand": self,
                        "type": humecord.CmdTypes.SUBCOMMAND,
                        "subcommand": subcommand_name # So the callback knows where to look for func
                    }
                )
                self._set_general_attrs(cmd, subcommand_name)

                # Overwrite callback with real one
                cmd._callback = self._command_callback.__func__
                cmd.binding = self

                # Override params
                cmd._params = params

                # Add to group
                root_cmd.add_command(cmd)

            else:
                # Just assign the params to the cmd
                root_cmd._params = params

        # All done -- send the command back
        self._root_dcmd = root_cmd
        self._root_dcmd_type = root_cmd_type
        return root_cmd

    def _get_permissions(
            self,
            subcommand: str
        ) -> Optional[list]:
        default_perms = None
        if subcommand == "__root__":
            # Check for root 'self.default_perms' opt
            default_perms = getattr(self, "default_perms", None)

        else:
            # Check in self.subcommand_details
            details = getattr(self, "subcommand_details", None)

            if details is not None:
                # Check for subcommand
                if subcommand in self.subcommand_details:
                    default_perms = self.subcommand_details[subcommand].get("default_perms")

        if default_perms is None:
            return None

        # Otherwise, format them
        str_perms = []
        if type(default_perms) == str:
            # Humecord-style permission string
            rules = default_perms.split("+")

            for rule in rules:
                rule = rule.lower().strip()
                if not rule.startswith("guild."):
                    raise exceptions.DevError(f"Only guild.mod, guild.admin, or guild.any permitted for command permissions.")

                sub = rule.split(".", 1)[1].strip()

                if sub == "admin":
                    str_perms += ["administrator"]

                elif sub == "mod":
                    str_perms += bot.permissions.mod_perms

                elif sub == "any":
                    str_perms += ["read_messages"]

                else:
                    raise exceptions.DevError(f"Only guild.mod, guild.admin, or guild.any permitted for command permissions.")

        elif type(default_perms) == list:
            str_perms = default_perms

        else:
            raise exceptions.DevError(f"Command.default_perms must be a string (humecord permission node) or list (discord permission nodes).")

        # Turn the strings into discord.Permission enums
        discord_perms = []
        for perm in str_perms:
            disc_perm = getattr(discord.Permissions, perm, None)

            if disc_perm is None:
                raise exceptions.DevError(f"Permission {perm} does not exist. See discord.Permissions API docs for a list of all permissions.")

            discord_perms.append(disc_perm)

        return discord_perms

    async def _verify_permission(
            self,
            interaction: discord.Interaction,
            udb: dict[str, Any]
        ) -> None:
        # Find the Humecord permission node
        perm_node = getattr(self, "perms", None)

        if perm_node is None:
            return

        return await bot.permissions.check(
            interaction.user,
            perm_node,
            udb,
            dev_override = True
        )

    async def _fake_callback(
            self,
            interaction: discord.Interaction
        ) -> None:
        """
        Used temporarily during command generation to trick dpy into allowing kwargs with no types.
        
        Later changed once our params are overwritten.
        """
        humecord.logger.log("command", "error", "Fake callback was used for command dispatch. Report this!")

    async def _command_callback(
            self,
            interaction: discord.Interaction,
            **kwargs
        ) -> None:
        """
        Internal method which processes a dpy callback and forwards it to the necessary command.
        """
        
        # Wrap with an error handler, since it's not logged otherwise (reason unknown)
        await errorhandler.wrap(self._command_callback_wrapped(interaction, **kwargs))

    async def _command_callback_wrapped(
            self,
            interaction: discord.Interaction,
            **kwargs
        ) -> None:
        # Check the interaction command for the source
        dcmd = interaction.command

        # Find the target callback
        callback = None

        if "type" not in dcmd.extras:
            raise exceptions.ValidationError(f"Command was returned from dpy with no Humecord 'extras' values")

        if dcmd.extras["type"] == humecord.CmdTypes.COMMAND:
            # Command is at subcommand __root__
            callback = self._subcommand_tree["__root__"]["func"]

        elif dcmd.extras["type"] == humecord.CmdTypes.SUBCOMMAND:
            # Command is defined in extras
            sub_name = dcmd.extras.get("subcommand")

            if sub_name is None:
                raise exceptions.ValidationError(f"Subcommand returned from dpy has no subcommand location defined")

            callback = self._subcommand_tree[sub_name]["func"]

        else:
            raise exceptions.ValidationError("Attempted callback for command with invalid type")
        
        if callback is None:
            raise exceptions.ValidationError("No callback could be found")

        # Generate an Args class
        kwargs = {x: y for x, y in kwargs.items() if y is not None}

        args = discordclasses.Args(**kwargs)

        # Call the command handler's run_command method with this data
        await humecord.bot.commands.call_command(interaction, callback, args)

    async def run(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        await resp.embed(
            "Default slash command placeholder",
            "Change your slash command tree off of `self.run` or override the `async def run()` function to get rid of this!",
            fields = [
                {
                    "name": ".resp",
                    "value": f"```{[x for x in dir(resp) if not x.startswith('__')]}```"
                },
                {
                    "name": ".ctx",
                    "value": f"```{[x for x in dir(ctx) if not x.startswith('__')]}```"
                },
                {
                    "name": ".ctx.args",
                    "value": f"```{[x for x in dir(ctx.args) if not x.startswith('__')]}```"
                }
            ]
        )

arg_str_transform = {
    "str": discord.AppCommandOptionType.string,
    "int": discord.AppCommandOptionType.integer,
    "bool": discord.AppCommandOptionType.boolean,
    "user": discord.AppCommandOptionType.user,
    "channel": discord.AppCommandOptionType.channel,
    "role": discord.AppCommandOptionType.role,
    "mentionable": discord.AppCommandOptionType.mentionable,
    "number": discord.AppCommandOptionType.number,
    "attachment": discord.AppCommandOptionType.attachment
}