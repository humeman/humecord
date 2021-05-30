"""
HumeCord/classes/commands

The HumeCord command handler.
"""

import humecord

import textwrap
import random
import discord

class Commands:
    def __init__(
            self,
            commands
        ):

        self.commands = commands

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
                        for arg in header[1:]:
                            i += 1
                            if args_lower[i] != header[i]:
                                break

                            matched_commands.append(
                                {
                                    "category": category,
                                    "command": command,
                                    "header": header
                                }
                            )

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
            gdb = await humecord.bot.api.get(humecord.bot.config.self_api, "guild", {"id": message.guild.id})

        else:
            gdb = await humecord.bot.db.get("guild", {"id": message.guild.id})

        category, command, header = matched_commands[0].values()

        if args_lower[0] != f"{gdb['prefix']}{header['match'][0]}":
            return

        # Create response channel
        resp = humecord.classes.discordclasses.MessageResponseChannel(
            message
        )

        args = message.content.split(" ")

        # Expand the args
        if header["type"] == "alias":
            args = command.name.split(" ") + args[len(header["match"]):]

        elif header["type"] == "shortcut":
            args = header["replace_with"].split(" ") + args[len(header["match"]):]

        # Match subcommands
        subcommand_details = ""
        if "subcommands" in dir(command):
            if len(args) == 1:
                if "__default__" in command.subcommands:
                    function = command.subcommands["__default__"](message, resp, args, gdb)
                    subcommand_details = ".__default__"

                else:
                    function = self.syntax_error(message, resp, args, gdb["prefix"], "test", "when")
                    subcommand_details = ".__syntax_internal__"

            else:
                action = args[1].lower()

                if action in command.subcommands:
                    function = command.subcommands[action](message, resp, args, gdb)
                    subcommand_details = f".{action}"

                else:   
                    if "__syntax__" in command.subcommands:
                        function = command.subcommands["__syntax__"](message, resp, args, gdb)
                        subcommand_details = ".__syntax__"

                    else:
                        function = self.syntax_error(message, resp, args, gdb["prefix"], "test", "when")
                        subcommand_details = ".__syntax_internal__"

        else:
            function = command.run(message, resp, args, gdb)

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