"""
humecord/classes/msgcommands/MessageCommandAdapter

Provides an adapter from message-based commands to the new slash command interface.
Replaces the old command handler entirely.
"""

from typing import Optional, Union, Any, Tuple, List
from enum import Enum
import discord
import humecord
import time
import asyncio

from . import discordclasses

from humecord.utils import (
    exceptions,
    discordutils
)

class MessageCommandAdapter:
    def __init__(
            self,
            parent
        ) -> None:
        """
        Initializes a message command adapter object.

        Params:
            parent (humecord.classes.commandhandler.CommandHandler): Parent command handler to retrieve commands from
        """
        global bot
        from humecord import bot

        self.tree = {}
        self.parent = parent

    async def generate_tree(    
            self
        ) -> None:
        """
        Pulls data from the command tree.
        Must be called before any commands will be run.
        Additionally, this retrieves the command tree from bot.commands,
            so initialization has to occur after bot.commands is done.
        """
        if not self.parent._prep_finished:
            raise exceptions.DevError(f"Command handler is not synced yet.")
        
        self.tree = {}

        for category, commands in self.parent.tree.items():
            # Assign a category to the tree
            _category = {
                "name": category,
                "commands": []
            }

            for command in commands:
                if not "messages" in dir(command):
                    humecord.logger.log("botinit", "warn", f"Command {category}.{command.name} has no message attr defined -- message-based command invocation will not work.")
                    continue

                msginfo = command.messages

                # Prepare a list of 'activator' phrases -- name, aliases, shortcuts 
                activators = {
                    command.name: {
                        "content": command.name,
                        "type": humecord.ActivatorTypes.REPLACE
                    }
                }

                if "aliases" in msginfo:
                    for alias in msginfo["aliases"]:
                        activators[alias] = {
                            "content": alias,
                            "type": humecord.ActivatorTypes.REPLACE
                        }

                if "shortcuts" in msginfo:
                    for sc_from, sc_to in msginfo["shortcuts"].items():
                        activators[sc_from] = {
                            "content": sc_from,
                            "type": humecord.ActivatorTypes.SHORTCUT,
                            "to": sc_to
                        }

                _category["commands"].append(
                    {
                        "hcommand": command,
                        "category": category,
                        "activators": activators
                    }
                )

            self.tree[category] = _category

    def check_run(
            self,
            first_arg: str
        ) -> Tuple[Optional[dict[str, Any]], Optional[dict[str, dict[str, Any]]]]:
        """
        Checks if a message could be present in the message.

        Still has to be checked against the guild/user's prefix.

        Params:
            first_arg (str): First argument

        Returns:
            match_command (Optional[dict[str, Any]]): Matched command details, if a match is found
            match_activator (Optional[dict[str, dict[str, Any]]]): Matched activator details
        """
        first_arg = first_arg.lower()

        for category, category_det in self.tree.items():
            for command_det in category_det["commands"]:
                for activator, activator_det in command_det["activators"].items():
                    if first_arg.endswith(activator):
                        return command_det, activator_det

        return None, None

    async def run(
            self,
            message: discord.Message
        ) -> None:
        """
        Checks for and runs a message.

        Params:
            message: discord.Message
        """

        # Verify this is a user message
        if message.type != discord.MessageType.default:
            return

        # Check if there is content available
        if message.content is None:
            return

        # And, verify that there's enough content to get the first arg
        if message.content.count(" ") == 0:
            first_arg = message.content

        else:
            first_arg = message.content.split(" ", 1)[0]

        # Check if the message has an activator match
        matched_command, matched_activator = self.check_run(first_arg)

        if matched_command is None:
            return
        
        hcommand = matched_command["hcommand"]

        kw = {}
        prefix = None
        # Now, we have to get a command prefix. Check if this is:
        # A guild message
        if message.channel.type in [discord.ChannelType.text, discord.ChannelType.private_thread, discord.ChannelType.public_thread, discord.ChannelType.forum]:
            # Get gdb (+ preferred gdb) and udb, prefix is from gdb
            gdb = await bot.api.get(
                humecord.bot.config.self_api,
                "guild",
                { "id": message.guild.id, "autocreate": True }
            )

            # Set preferred GDB values
            kw["preferred_gdb"] = {x: gdb.get(x) for x in bot.config.preferred_gdb}

            kw["gdb"] = gdb
            prefix = gdb.get("prefix") or "!"

            preferred_api = getattr(hcommand, "preferred_api", None)

            if preferred_api is not None:
                # Get that preferred API's gdb, and swap them around
                p_gdb = await bot.api.get(
                    preferred_api,
                    "guild",
                    { "id": message.guild.id, "autocreate": True }
                )

                kw["alt_gdb"] = kw["gdb"]
                kw["gdb"] = p_gdb

            udb = await bot.api.get(
                bot.config.user_api,
                "user",
                { "id": message.guild.id, "autocreate": True }
            )

        elif message.channel.type in [discord.ChannelType.private or discord.ChannelType.group]:
            udb = await bot.api.get(
                bot.config.user_api,
                "user",
                { "id": message.author.id, "autocreate": True }
            )

            prefix = udb.get("prefix") or "!"

        # Now, check that the command matches the prefix + activator to determine if we actually run
        if prefix is None:
            humecord.logger.log("command", "warn", f"No prefix defined for target location {message.channel.id} ({message.channel.type}). Skipping execution.")
            self.parent.stat_cache["__denied__"] += 1
            return

        if first_arg != f"{prefix}{matched_activator['content']}":
            return

        # We matched the command. Prepare for execution.
        # 1: Check if user is botbanned.
        if udb.get("botban") is not None:
            if udb["botban"]["duration"] is not None:
                if udb["botban"]["endsat"] > time.time():
                    humecord.logger.log("command", "cmd", f"User {message.author} ({message.author.id}) is botbanned, skipping command dispatch.")
                    self.parent.stat_cache["__denied__"] += 1
                    return

        # 2: Check that the user doesn't have ignore_me on.
        if udb.get("ignore"):
            humecord.logger.log("command", "cmd", f"User {message.author} ({message.author.id}) has ignore enabled, skipping command dispatch.")
            self.parent.stat_cache["__denied__"] += 1
            return
                
        # 2a: (forgot about this one) Check permissions, if they exist
        if "perms" in dir(hcommand):
            if not await bot.permissions.check(message.author, hcommand.perms, udb):
                await resp.send(
                    embed = humecord.utils.discordutils.error(
                        message.author,
                        "You don't have permission to run this command!",
                        f"In order to run this command, you need the permission `{hcommand.perms}`. Check with an admin if you believe this is in error." 
                    )
                )
                self.parent.stat_cache["__denied__"] += 1
                return

        # 3: Split the command into args
        text_args = message.content.split(" ")
        
        if len(hcommand._subcommand_tree) == 1:
            arg_len = 1

        else:
            arg_len = 2

        # 4: If activation method is a shorcut, expand args to that shortcut
        if matched_activator["type"] == humecord.ActivatorTypes.SHORTCUT:
            new_args = matched_activator["to"].split(" ")
            text_args = new_args + text_args[1:]
            arg_len = len(new_args)

        # 5: Match these args to a subcommand or regular command
        text_arg_len = len(text_args)
        subcommand_match = None
        err = True
        if text_arg_len == 1: # Root subcommand or error
            if len(hcommand._subcommand_tree) > 1:
                # Syntax error: Missing a subcommand
                await message.reply(
                    embed = self.get_err_embed(hcommand, error = False)
                )
                self.parent.stat_cache["__denied__"] += 1
                return

            # Run the root command
            subcommand_match = hcommand._subcommand_tree["__root__"]
        
        # We've already matched a command -- now check the subcommand (arg 2)
        elif text_arg_len >= 2:
            subcommand = text_args[1].lower()

            for name, details in hcommand._subcommand_tree.items():
                matches = [name.lower()]

                if "aliases" in details["details"]:
                    matches += [x.lower() for x in details["details"]["aliases"]]
                
                if subcommand in matches:
                    # Match found
                    subcommand_match = hcommand._subcommand_tree[name]
                    break

        else:
            err = False

        # If there's not a match, send an error
        if subcommand_match is None:
            await message.reply(
                embed = self.get_err_embed(hcommand, error = err)
            )
            self.parent.stat_cache["__denied__"] += 1
            return
        
        # 6: Parse any args
        arg_names = []

        for arg_name in subcommand_match["args"]:
            arg_details = hcommand.args.get(arg_name)

            if arg_details is None:
                self.parent.stat_cache["__denied__"] += 1
                raise exceptions.DevError(f"Argument {arg_name} has no entry in self.args.")

            if arg_details.get("slashonly"):
                continue

            arg_names.append(arg_name)

        next_i = arg_len
        total_arg_len = len(text_args)
        parsed_args = {}
        for i, arg_name in enumerate(arg_names):
            arg_details = hcommand.args[arg_name]

            hc_arg_type = discord_to_humecord_args[arg_details.get("type")]

            if hc_arg_type is None:
                # We don't have a way to transform this arg yet.
                # Send an error, asking the user to use slash commands -- if the arg is required.

                if arg_details.get("required"):
                    await message.reply(
                        embed = discordutils.create_embed(
                            f"{bot.config.lang['emoji']['error']}  Can't execute command!",
                            f"Humecord does not have a method to parse arguments of type `{arg_details['type']}` yet. In the meantime, you'll have to use slash commands.\nFeel free to bug my dev (or Hume) about this!",
                            color = "error"
                        )
                    )
                    self.parent.stat_cache["__denied__"] += 1
                    return
        
            # Parse the arg, if it exists
            elif next_i < total_arg_len:
                # Append any validators, if they exist
                if "validate" in arg_details:
                    hc_arg_type = f"{hc_arg_type}[{arg_details['validate']}]"

                # Parse either the arg (if there are more args coming) or the rest of the content (if it's the last one)
                if i == len(arg_names) - 1:
                    to_parse = " ".join(text_args[next_i:])

                else:
                    to_parse = text_args[next_i]

                # Arg exists -- parse it
                success, res = await bot.args.parse(
                    hc_arg_type,
                    to_parse,
                    {}
                )

                if success:
                    # Valid -- add to collection
                    parsed_args[arg_name] = res

                else:
                    # Invalid -- find out why, then tell the user
                    await message.reply(
                        embed = discordutils.create_embed(
                            f"{bot.config.lang['emoji']['error']}  Invalid arguments!",
                            f"```{self.get_syntax_err_string(text_args, next_i)}\nexpected argument {arg_name} of type {arg_details['type']}```",
                            color = "error"
                        )
                    )
                    self.parent.stat_cache["__denied__"] += 1
                    return


            # Arg doesn't exist. If it's not required, that's okay.
            elif arg_details.get("required"):
                await message.reply(
                    embed = discordutils.create_embed(
                        f"{bot.config.lang['emoji']['error']}  Missing arguments!",
                        f"```{self.get_syntax_err_string(text_args, next_i)}\nexpected argument {arg_name} of type {arg_details['type']}```",
                        color = "error"
                    )
                )
                self.parent.stat_cache["__denied__"] += 1
                return

            next_i += 1

        # 7: Generate RespChannel
        resp = discordclasses.MessageResponseChannel(message)

        # 8: Generate Args
        args = discordclasses.Args(**parsed_args)

        # 9: Generate Context
        kw = {
            **kw,
            "type": humecord.ContextTypes.MESSAGE,
            "resp": resp,
            "message": message,
            "channel": message.channel,
            "hcommand": hcommand,
            "args": args,
            "user": message.author
        }
        ctx = discordclasses.Context(**kw)

        # 10: Wrap command and run
        humecord.logger.log("commandinfo", "cmd", "Dispatching message-based command.")
        humecord.logger.log_long(
            "commandinfo",
            "cmd",
            [
                f"Command:        {hcommand.category}.{hcommand.name} ({subcommand_match['name']})",
                f"Channel:        {message.channel.id} ({message.channel.name})",
                f"User:           {message.author.id} ({message.author.name}#{message.author.discriminator})"
            ],
            extra_line = False
        )
        self.parent.stat_cache["__total__"] += 1

        humecord.bot.client.loop.create_task(
            humecord.utils.errorhandler.message_wrap(
                subcommand_match["func"](resp, ctx),
                message,
                hcommand
            )
        )


    def get_syntax_err_string(
            self,
            args: List[str],
            index: int
        ) -> str:
        """
        Returns a string in the following format:

        arg1 arg2 arg3 arg4
                  ^^^^
        given an args array and an index.
        If index is out of bounds, pointer will be at the end of the string.

        Params:
            args (List[str])
            index (int)
        """
        # Change index into a location
        if index >= len(args):
            # End of string
            location = len(args) + sum([len(x) for x in args])
            length = 1

        else:
            # Index of arg
            location = len(args) + sum([len(x) for x in args[:index]]) - 1
            length = len(args[index])

        return f"{' '.join(args)}\n{' ' * location}{'^' * length}"

    def get_err_embed(
            self,
            hcommand,
            error: bool = False
        ) -> None:

        details = [
            f"**{hcommand.name}**"
        ]
        desc = getattr(hcommand, "description", None)
        if desc is not None:
            details.append(hcommand.description)

        fields = []

        # Check for subcommands
        if len(hcommand._subcommand_tree) > 1:
            comp = []
            # Subcommands exist. List them
            for name, subcommand_details in hcommand._subcommand_tree.items():
                comp.append(f"• **{hcommand.name} {name}**: *{subcommand_details['details'].get('description') or 'No description set'}*")

            fields.append(
                {
                    "name": "→ Subcommands",
                    "value": "\n".join(comp)
                }
            )

        # Aliases
        aliases = hcommand.messages.get("aliases")
        if aliases is not None:
            if len(aliases) > 1:
                fields.append(
                    {
                        "name": "→ Aliases",
                        "value": ", ".join(aliases)
                    }
                )

        # And shortcuts
        shortcuts = hcommand.messages.get("shortcuts")
        if shortcuts is not None:
            if len(shortcuts) > 1:
                comp = []
                for _from, _to in shortcuts.items():
                    comp.append(f"• **{_from}** → {_to}")

                fields.append(
                    {
                        "name": "→ Shortcuts",
                        "value": "\n".join(comp)
                    }
                )

        # Generate details
        if error:
            title = f"{bot.config.lang['emoji']['error']}  Invalid syntax!"
            color = "error"

        else:
            title = f"{bot.config.lang['emoji']['info']}  Command info: /{hcommand.name}"
            color = "blue"

        return discordutils.create_embed(
            title,
            description = "\n".join(details),
            fields = fields,
            color = color
        )

discord_to_humecord_args = {
    "str": "str",
    "int": "int",
    "bool": "bool",
    "user": "user",
    "channel": "channel",
    "role": None,
    "mentionable": None,
    "number": "float",
    "attachment": None,
    "option": "str",
    None: None
}

