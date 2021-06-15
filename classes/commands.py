"""
HumeCord/classes/commands

The HumeCord command handler.
"""

import humecord

import textwrap
import random
import discord
import sys

class Commands:
    def __init__(
            self,
            commands
        ):

        self.commands = commands

    def register_internal(
            self
        ):

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

        if len(matched_commands) > 1:
            humecord.utils.logger.log("warn", f"Command has multiple matches: {', '.join([x['command'].name for x in matched_commands])} ")

        # Get the guild database
        # -> API method
        if humecord.bot.config.use_api:
            gdb = await humecord.bot.api.get(humecord.bot.config.self_api, "guild", {"id": message.guild.id, "autocreate": True})

        else:
            gdb = await humecord.bot.db.get("guild", {"id": message.guild.id})

        category, command, header = matched_commands[0].values()

        if args_lower[0] != f"{gdb['prefix']}{header['match'][0]}":
            return

        # Generate pdb
        pdb = {}
        for key in humecord.bot.config.preferred_gdb:
            pdb[key] = gdb[key]

        # Create response channel
        resp = humecord.classes.discordclasses.MessageResponseChannel(
            message
        )

        # Check perms
        if not await humecord.bot.permissions.check(message.author, command.permission):
            await resp.send(
                embed = humecord.utils.discordutils.error(
                    message.author,
                    "You don't have permission to run this command!",
                    f"Contact an admin if you believe this is in error." 
                )
            )
            return

        args = message.content.split(" ")

        # Expand the args
        if header["type"] == "alias":
            args = command.name.split(" ") + args[len(header["match"]):]

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
                    function = command.subcommands["__default__"]["function"](message, resp, args, gdb, None, pdb)
                    subcommand_details = ".__default__"

                else:
                    function = self.syntax_error(message, resp, args, gdb, command.name)
                    subcommand_details = ".__syntax_internal__"

            else:
                action = args[1].lower()

                if action in command.subcommands:
                    function = command.subcommands[action]["function"](message, resp, args, gdb, None, pdb)
                    subcommand_details = f".{action}"

                else:   
                    if "__syntax__" in command.subcommands:
                        function = command.subcommands["__syntax__"]["function"](message, resp, args, gdb, None, pdb)
                        subcommand_details = ".__syntax__"

                    else:
                        function = self.syntax_error(message, resp, args, gdb, command.name)
                        subcommand_details = ".__syntax_internal__"

        else:
            function = command.run(message, resp, args, gdb, None, pdb)

        command_id = str(hex(message.id)).replace("0x", "")

        humecord.utils.logger.log("cmd", f"Dispatching command ID {command_id}", bold = True)
        linebreak = "\n"
        humecord.utils.logger.log_long(
            f"""Command:        {category}.{command.name}{subcommand_details}
            Guild:          {message.guild.id} ({message.guild.name})
            Channel:        {message.channel.id} ({message.channel.name})
            User:           {message.author.id} ({message.author.name}#{message.author.discriminator})
            Content:        {message.clean_content[:110].replace(linebreak, "")}
            Match type:     {header['type']}""".replace("            ", ""),
            "blue",
            extra_line = False
        )

        humecord.utils.logger.log_step("Creating command task...", "blue")
        humecord.bot.client.loop.create_task(
            humecord.utils.errorhandler.discord_wrap(
                function,
                message,
                command = [category, command, header]
            )
        )
        print()

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
                fields.append(
                    {
                        "name": "Valid subcommands",
                        "value": "\n".join([f"`{prefix}{command.name}{f' {x}' if not x.startswith('__') else ''}`{': ' + y.get('description') if 'description' in y else ''}" for x, y in command.subcommands.items()])
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