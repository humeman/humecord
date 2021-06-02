from humecord.utils import (
        discordutils,
        exceptions
    )


class HelpCommand:
    def __init__(
            self
        ):

        self.name = "help"
        self.description = "Sends a list of commands that you can use."

        self.aliases = ["commands"]

        self.permission = "bot.any"

        global bot
        from humecord import bot

    async def run(
            self,
            message,
            resp,
            args,
            gdb,
            alternate_gdb = None,
            preferred_gdb = None
        ):

        if len(args) == 1:
            # Compile categories
            comp = {}

            for category, commands in bot.commands.commands.items():
                comp_commands = []

                for command in commands:
                    if await bot.permissions.check(
                        message.author,
                        command.permission
                    ):
                        comp_commands.append(command)

                if len(comp_commands) > 0:
                    comp[category] = comp_commands

            if len(comp) == 0:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Couldn't list any commands!",
                        "You don't have access to any commands."
                    )
                )
                return

            # Find each corresponding category
            fields = []
            for category, commands in comp.items():
                if category not in bot.config.command_categories:
                    raise exceptions.DevError(f"Category {category} doesn't exist in bot.config.command_categories")
        
                c = bot.config.command_categories[category]

                fields.append(
                    {
                        "name": f"{c['emoji']}  {c['name']}",
                        "value": f"{c['description']}\n{len(commands)} command{'' if len(commands) == 1 else 's'}"
                    }
                )

            # Send the message
            await resp.send(
                embed = discordutils.create_embed(
                    f"{message.author.name}'s commands",
                    f"This is a list of all commands that {message.author.mention} can run in {message.guild.name}.\nTo view the commands in each category, run `{preferred_gdb['prefix']}help [category]`.",
                    author = message.author,
                    fields = fields,
                    color = "invisible"
                )
            )

        else:
            # Find the category/command
            category = args[1].lower()
            active = None

            for cat, info in bot.config.command_categories.items():
                if category == cat or category in info["aliases"]:
                    name = cat
                    active = info
            
            if active is not None:
                pass

            else:
                active = None

                # See if it's a command
                for cat, commands in bot.commands.commands.items():
                    for command in commands:
                        valid = [command.name]
                        cd = dir(command)

                        if "aliases" in cd:
                            valid += command.aliases

                        if "shortcuts" in cd:
                            valid += list(command.shortcuts)

                        if category in valid:
                            active = command

                            if cat not in bot.config.command_categories:
                                raise exceptions.DevError(f"Category {cat} doesn't exist in bot.config.command_categories")
        
                            active_cat = bot.config.command_categories[cat]

                if active is None:
                    await resp.send(
                        embed = discordutils.error(
                            message.author,
                            "Can't find command!",
                            f"`{category}` was not found as either a category or command."
                        )
                    )
                    return

                # Send command details
                category = active_cat

                prefix = preferred_gdb["prefix"]
                command = active
                cd = dir(command)
                comp = []

                comp.append(
                    {
                        "name": "→ Category",
                        "value": f"{category['emoji']}  {category['name']}\n{category['description']}"
                    }
                )

                # Create syntax
                if "syntax" in cd:
                    syntax = f"{prefix}{command.name} {command.syntax}".strip()

                else:
                    # Try to compile syntax
                    syntax = f"{prefix}{command.name}"

                    if "subcommands" in cd:
                        syntax += " [subcommand]"

                comp.append(
                    {
                        "name": "→ Syntax",
                        "value": f"`{syntax}`"
                    }
                )

                if "aliases" in cd:
                    comp.append(
                        {
                            "name": "→ Aliases",
                            "value": ", ".join([f"`{prefix}{x}`" for x in command.aliases])
                        }
                    )

                if "shortcuts" in cd:
                    comp.append(
                        {
                            "name": "→ Shortcuts",
                            "value": "\n".join([f"`{prefix}{x}` → `{prefix}{y}`" for x, y in command.shortcuts.items()])
                        }
                    )

                if "subcommands" in cd:
                    comp.append(
                        {
                            "name": "→ Subcommands",
                            "value": "\n".join([f"`{prefix}{command.name}{f' {x}' if not x.startswith('__') else ''}`{': ' + y.get('description') if 'description' in y else ''}" for x, y in command.subcommands.items()])
                        }
                    )

                await resp.send(
                    embed = discordutils.create_embed(
                        f"{prefix}{command.name}",
                        description = command.description,
                        fields = comp,
                        color = "invisible"
                    )
                )

