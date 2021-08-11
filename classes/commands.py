"""
Humecord/classes/commands

The Humecord command handler.
"""

import humecord

from humecord.utils import (
    ratelimits,
    discordutils,
    dateutils,
    exceptions
)

import textwrap
import random
import discord
import sys
import time

class Commands:
    def __init__(
            self,
            commands
        ):

        self.commands = commands

        global bot
        from humecord import bot

        self.stat_cache = {
            "__total__": 0,
            "__denied__": 0
        }

    def get_imports(
            self
        ):

        comp = {

        }

        defaults = {
            "about": {
                "imp": "from humecord.commands import about",
                "module": "about",
                "class": "AboutCommand"
            },
            "help": {
                "imp": "from humecord.commands import help",
                "module": "help",
                "class": "HelpCommand"
            },
            "overrides": {
                "imp": "from humecord.commands import overrides",
                "module": "overrides",
                "class": "OverridesCommand"
            },
            "dev": {
                "imp": "from humecord.commands import dev",
                "module": "dev",
                "class": "DevCommand"
            },
            "settings": {
                "imp": "from humecord.commands import settings",
                "module": "settings",
                "class": "SettingsCommand"
            },
            "messages": {
                "imp": "from humecord.commands import messages",
                "module": "messages",
                "class": "MessagesCommand"
            },
            "dm": {
                "imp": "from humecord.commands import dm",
                "module": "dm",
                "class": "DMCommand"
            },
            "exec": {
                "imp": "from humecord.commands import exec_cmd",
                "module": "exec_cmd",
                "class": "ExecCommand"
            },
            "loops": {
                "imp": "from humecord.commands import loops",
                "module": "loops",
                "class": "LoopsCommand"
            },
            "profile": {
                "imp": "from humecord.commands import profile",
                "module": "profile",
                "class": "ProfileCommand"
            },
            "botban": {
                "imp": "from humecord.commands import botban",
                "module": "botban",
                "class": "BotBanCommand"
            },
            "useredit": {
                "imp": "from humecord.commands import useredit",
                "module": "useredit",
                "class": "UserEditCommand"
            },
            "syslogger": {
                "imp": "from humecord.commands import syslogger",
                "module": "syslogger",
                "class": "SysLoggerCommand"
            },
            "logs": {
                "imp": "from humecord.commands import logs",
                "module": "logs",
                "class": "LogsCommand"
            }
        }

        for command, overrides in humecord.bot.config.default_commands.items():
            if command not in defaults:
                raise humecord.utils.exceptions.NotFound(f"Default command {command} does not exist.")

            if overrides["__category__"] not in comp:
                comp[overrides["__category__"]] = []

            # Create command
            comp[overrides["__category__"]].append(
                {
                    **defaults[command],
                    "attrs": overrides
                }
            )


        return comp

            

    def register_internal(
            self
        ):

        raise DeprecationWarning("This feature is deprecated in favor of the Humecord loader.")

        self.defaults = {
            "dev": humecord.commands.dev.DevCommand,
            "about": humecord.commands.about.AboutCommand,
            "help": humecord.commands.help.HelpCommand,
            "overrides": humecord.commands.overrides.OverridesCommand
        }

        # Load all defaults
        for command, command_overrides in humecord.bot.config.default_commands.items():
            if command not in self.defaults:
                raise humecord.utils.exceptions.NotFound(f"Default command {command} does not exist.")

            if command_overrides["__category__"] not in self.commands:
                self.commands[command_overrides["__category__"]] = []

            # Get command object
            cmd = self.defaults[command]()

            # Set attributes
            override_count = 0
            for key, value in command_overrides.items():
                if not key.startswith("__"):
                    setattr(cmd, key, value)
                    override_count += 1

            # Register
            self.commands[command_overrides["__category__"]].append(cmd)
            if override_count > 0:
                humecord.utils.logger.log_step(f"Registered default command {command} with {override_count} override{'' if override_count == 1 else 's'}", "cyan")

    async def run(
            self, 
            message: discord.Message
        ):
        args_lower = message.content.lower().split(" ")

        matched_commands = []
        for category, commands in self.commands.items():
            for command in commands:
                opts = dir(command)

                possible = [
                    {
                        "match": command.name.split(" "),
                        "type": "direct"
                    }
                ]

                if "aliases" in opts:
                    for alias in command.aliases:
                        possible.append(
                            {
                                "match": alias.split(" "),
                                "type": "alias"
                            }
                        )

                if "shortcuts" in opts:
                    for shortcut, value in command.shortcuts.items():
                        possible.append(
                            {
                                "match": shortcut.split(" "),
                                "type": "shortcut",
                                "replace_with": value
                            }
                        )

                matched = [header for header in possible if args_lower[0].endswith(header["match"][0])]

                for header in matched:
                    if len(header["match"]) != 1 and len(args_lower) >= len(header):
                        i = 1
                        for arg in header["match"][1:]:
                            if args_lower[i] != arg:
                                break

                            matched_commands.append(
                                {
                                    "category": category,
                                    "command": command,
                                    "header": header
                                }
                            )
                            
                            i += 1

                    elif len(header["match"]) == 1:
                        matched_commands.append(
                            {
                                "category": category,
                                "command": command,
                                "header": header
                            }
                        )

        if len(matched_commands) == 0:
            return

        # Get the user
        user = await bot.api.get(
            "users",
            "user",
            {
                "id": message.author.id,
                "autocreate": True
            }
        )

        # Check if banned
        if user["botban"] is not None:
            if user["botban"]["duration"] is not None:
                if user["botban"]["endsat"] > time.time():
                    humecord.logger.log("command", "cmd", f"User {message.author} ({message.author.id}) is botbanned, skipping command dispatch")
                    self.stat_cache["__denied__"] += 1
                    return False

        # Get the guild database
        # -> API method
        if humecord.bot.config.use_api:
            gdb = await humecord.bot.api.get(humecord.bot.config.self_api, "guild", {"id": message.guild.id, "autocreate": True})

        else:
            gdb = await humecord.bot.db.get("guild", {"id": message.guild.id})

        full_match = None
        for match in matched_commands:
            category, command, header = match.values()

            # Check guild prefix & universal prefixes
            for prefix in [gdb["prefix"]] + humecord.bot.config.universal_prefixes:
                if args_lower[0] == f"{prefix}{header['match'][0]}":
                    full_match = match

            # Check universal prefixes
            if full_match is None:
                for prefix in humecord.bot.config.conditional_prefixes:
                    if args_lower[0].startswith(prefix["start"]):
                        # Get everything after
                        arg1 = args_lower[0][len(prefix["start"]):]

                        # Check if end is specified
                        if prefix["end"] not in arg1:
                            continue

                        bots = arg1.split(prefix["end"])[0].split(",")

                        for bot_name in ["all", *humecord.bot.names]:
                            if bot_name in bots:
                                full_match = match
                                break

                        if full_match is not None:
                            break

        if full_match is None:
            return

        command_id = str(hex(message.id)).replace("0x", "")

        humecord.logger.log("command", "cmd", f"Dispatching command ID {command_id}", bold = True)

        category, command, header = full_match.values()

        # Generate pdb
        pdb = {}
        for key in humecord.bot.config.preferred_gdb:
            pdb[key] = gdb[key]

        # Create response channel
        if type(message.channel) == discord.Thread:
            resp = humecord.classes.discordclasses.ThreadResponseChannel(message)

        elif type(message.channel) == discord.TextChannel:
            resp = humecord.classes.discordclasses.MessageResponseChannel(
                message
            )

        else:
            return

        # Check perms
        if not await humecord.bot.permissions.check(message.author, command.permission, user):
            await resp.send(
                embed = humecord.utils.discordutils.error(
                    message.author,
                    "You don't have permission to run this command!",
                    f"In order to run this command, you need the permission `{command.permission}`. Check with an admin if you believe this is in error." 
                )
            )
            self.stat_cache["__denied__"] += 1
            return

        args = message.content.split(" ")

        rl_subcommand_name = "__main__"

        # Expand the args
        if header["type"] == "alias":
            alias_args = header["match"]

            default_args = command.name.split(" ")
            count = len(alias_args)
            while len(alias_args) < len(default_args):
                alias_args.append(default_args[count])
                count += 1

            args = alias_args + args[len(header["match"]):]

        elif header["type"] == "shortcut":
            final = []
            rep_args = header["replace_with"].split(" ")
            current_index = len(rep_args)
            final_num = 0

            for i, arg in enumerate(rep_args):
                if "%%" in arg:
                    num = int(arg.replace("%%", "").replace("-", ""))

                    if "-" in arg:
                        final += args[num:]
                        final_num = len(args) - 1

                    elif len(args) - 1 >= num:
                        final.append(args[num])
                        final_num = num

                else:
                    final.append(arg)

            if final_num + 1 < len(args):
                final += args[final_num + 1:]

            args = final
            #header["replace_with"].split(" ") + args[len(header["match"]):]

        # Match subcommands
        subcommand_details = ""
        if "subcommands" in dir(command):
            if len(args) == 1:
                if "__default__" in command.subcommands:
                    function = command.subcommands["__default__"]["function"](message, resp, args, user, gdb, None, pdb)
                    subcommand_details = ".__default__"
                    rl_subcommand_name = "__default__"

                else:
                    function = self.syntax_error(message, resp, args, gdb, command.name)
                    subcommand_details = ".__syntax_internal__"
                    rl_subcommand_name = None

            else:
                action = args[1].lower()

                if action in command.subcommands:
                    function = command.subcommands[action]["function"](message, resp, args, user, gdb, None, pdb)
                    subcommand_details = f".{action}"
                    rl_subcommand_name = action

                else:   
                    if "__syntax__" in command.subcommands:
                        function = command.subcommands["__syntax__"]["function"](message, resp, args, user, gdb, None, pdb)
                        subcommand_details = ".__syntax__"
                        rl_subcommand_name = "__syntax__"

                    else:
                        function = self.syntax_error(message, resp, args, gdb, command.name)
                        subcommand_details = ".__syntax_internal__"
                        rl_subcommand_name = None

        else:
            function = command.run(message, resp, args, user, gdb, None, pdb)

        # Check if they're rate limited
        if rl_subcommand_name is not None and humecord.bot.config.use_api:
            limited, limit, left, user, write = await ratelimits.check_command_ratelimit(
                category,
                command,
                user,
                rl_subcommand_name
            )

            if write:
                # Write udb
                await bot.api.put(
                    "users",
                    "user",
                    {
                        "id": message.author.id,
                        "db": {
                            "ratelimits": user["ratelimits"]
                        }
                    }
                )

            if limited:
                # Check if error limited
                if message.author.id in bot.mem_storage["error_ratelimit"]:
                    if bot.mem_storage["error_ratelimit"][message.author.id] > time.time() - 1:
                        # Don't say anything - they're spamming
                        self.stat_cache["__denied__"] += 1
                        return

                bot.mem_storage["error_ratelimit"][message.author.id] = float(time.time())

                left = round(left)

                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Can't run command!",
                        f"This command has a ratelimit of {dateutils.get_duration(limit)}, which means you have to wait {dateutils.get_duration(left)} before running again."
                    )
                )
                self.stat_cache["__denied__"] += 1
                return

        linebreak = "\n"
        humecord.logger.log_long(
            "commandinfo",
            "cmd",
            [
                f"Command:        {category}.{command.name}{subcommand_details}",
                f"Guild:          {message.guild.id} ({message.guild.name})",
                f"Channel:        {message.channel.id} ({message.channel.name})",
                f"User:           {message.author.id} ({message.author.name}#{message.author.discriminator})",
                f"Content:        {message.clean_content[:110].replace(linebreak, '')}",
                f"Match type:     {header['type']}"
            ],
            extra_line = False
        )

        if category not in self.stat_cache:
            self.stat_cache[category] = {}

        if command.name not in self.stat_cache[category]:
            self.stat_cache[category][command.name] = 0

        self.stat_cache[category][command.name] += 1

        self.stat_cache["__total__"] += 1

        humecord.logger.log_step("commandinfo", "cmd", "Creating command task...")
        humecord.bot.client.loop.create_task(
            humecord.utils.errorhandler.discord_wrap(
                function,
                message,
                command = [category, command, header]
            )
        )
        humecord.terminal.log(" ", True)

    async def syntax_error(
            self,
            message: discord.Message, 
            resp, 
            args: list, 
            gdb: dict,
            command: str
        ):

        # Forward
        await self.send_info_message(
            message,
            resp,
            args,
            gdb,
            command,
            title = f"{humecord.bot.config.lang['emoji']['error']}  {humecord.bot.config.lang['command_info']['title']['syntax_error']}",
            color = "error"
        )

    async def send_info_message(
            self,
            message: discord.Message,
            resp,
            args: list,
            gdb: dict,
            command: str,
            title = None,
            color = "invisible"
        ):

        if title is None:
            title = humecord.bot.config.lang["command_info"]["title"]["info_message"]

        # Find the command
        active = None
        for category, commands in self.commands.items():
            for command_ in commands:
                if command_.name == command:
                    if active is not None:
                        raise humecord.utils.exceptions.LookupError(f"Command {command} has multiple instances")

                    active = command_

        if active is None:
            raise humecord.utils.exceptions.LookupError(f"Command {command} doesn't exist")

        command = active

        prefix = gdb.get("prefix")

        # Compile the embed
        cd = dir(command)

        # Create syntax
        if "syntax" in cd:
            syntax = f"{prefix}{command.name} {command.syntax}".strip()

        else:
            # Try to compile syntax
            syntax = f"{prefix}{command.name}"

            if "subcommands" in cd:
                syntax += " [subcommand]"

        placeholders = {
            "command": command.name,
            "prefix": prefix,
            "p": prefix,
            "syntax": syntax,
            "description": command.description
        }

        # Create fields
        fields = []
        if "info" in cd:
            fields = [{"name": humecord.utils.miscutils.expand_placeholders(x, placeholders), "value": humecord.utils.miscutils.expand_placeholders(y, placeholders)} for x, y in command.info.items()]

        else:
            # Try to compile it ourselves
            if "subcommands" in cd:
                if len(command.subcommands) > 0:
                    fields.append(
                        {
                            "name": "Valid subcommands",
                            "value": "\n".join([f"`{prefix}{command.name}{f' {x}' if not x.startswith('__') else ''}{' ' + y.get('syntax') if 'syntax' in y else ''}`{': ' + y.get('description') if 'description' in y else ''}" for x, y in command.subcommands.items()])
                        }
                    )

        description = humecord.utils.miscutils.expand_placeholders(
            humecord.bot.config.lang["command_info"]["description"],
            placeholders
        )

        title = humecord.utils.miscutils.expand_placeholders(
            title,
            placeholders
        )

        await resp.send(
            embed = humecord.utils.discordutils.create_embed(
                title = title,
                description = description,
                fields = fields,
                color = color
            )
        )

    def get_command(
            self,
            category,
            name
        ):

        if category not in self.commands:
            raise humecord.utils.exceptions.DevError(f"Category {category} doesn't exist")

        for command in self.commands[category]:
            if command.name == name:
                return command

        raise humecord.utils.exceptions.DevError(f"Command {name} doesn't exist in category {category}")

class CommandArgParser:
    def __init__(
            self
        ):
        pass

    async def compile_all(
            self
        ):
        """
        Compiles all commands' arg parser values into
        easier to read dicts to save time later.
        """

        for category, commands in bot.commands.items():
            for command in commands:
                if hasattr(command, "args"):
                    command.args = await self.compile_one(command.args)

    async def compile_one(
            self,
            command
        ):

        comp = {
            "args": {}
        }

        comp["required"] = command["required"] if "required" in command else False
        comp["fill"] = command["fill"] if "fill" in command else False

        # Begin parsing args
        for name, arg in command["args"].items():
            arg_comp = {}
            # Parse the rule
            arg_comp["rule"] = await bot.args.compile_recursive(
                arg["rule"]
            )

            arg_comp["required"] = arg["required"] if "required" in arg else False

            if "if" in arg_comp:
                arg_comp["condition"] = await self.compile_condition(arg_comp["if"])

            comp["args"][name] = arg_comp

        return comp

    async def compile_condition(
            self,
            condition
        ):

        if not ":" in condition:
            raise exceptions.InvalidRule("Expected ':'")

        rtype, args = condition.split(":", 1)

        args = args.split("&")