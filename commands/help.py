from humecord.utils import (
        discordutils,
        exceptions,
        components
    )

import math

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
                await self.update_page(
                    None,
                    "new",
                    name,
                    None,
                    message,
                    resp,
                    args,
                    gdb,
                    alternate_gdb,
                    preferred_gdb
                )

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
                comp = self.generate_command_details(
                    command,
                    category,
                    prefix
                )

                await resp.send(
                    embed = discordutils.create_embed(
                        f"{prefix}{command.name}",
                        description = command.description,
                        fields = comp,
                        color = "invisible"
                    )
                )

    def generate_command_details(
            self,
            command,
            category,
            prefix,
            one_line_safe = False
        ):

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
            if one_line_safe:
                comp.append(
                    {
                        "name": "→ Shortcuts",
                        "value": "\n" + "\n".join([f" • `{prefix}{x}` → `{prefix}{y}`" for x, y in command.shortcuts.items()])
                    }
                )

            else:
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
                    "value": "\n" + "\n".join([f" • `{prefix}{command.name}{f' {x}' if not x.startswith('__') else ''}`{': ' + y.get('description') if 'description' in y else ''}" for x, y in command.subcommands.items()])
                }
            )

        return comp

    async def update_page(
            self,
            direction,
            gen,
            category,
            old_page,
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):
        if gen == "new":
            if len(args) == 3:
                try:
                    page = int(args[2])

                except:
                    await resp.send(
                        embed = discordutils.error(
                            message.author,
                            "Invalid page!",
                            "If you specify a page, make sure it's a number."
                        )
                    )
                    return

            else:
                page = 1

        else:
            page = old_page - 1 if direction == "back" else old_page + 1

        name = str(category)
        category = bot.config.command_categories[category]
        
        prefix = preferred_gdb["prefix"]

        # Compile a list of commands they can use
        comp = []

        for command in bot.commands.commands[name]:
            if await bot.permissions.check(
                message.author,
                command.permission
            ):
                comp.append(command)

        if len(comp) == 0:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Can't list category!",
                    f"You don't have access to any commands in the category {category['name']}."
                )
            )
            return

        per = bot.config.commands_per_page

        page_count = math.ceil(len(comp) / per)

        if page > page_count or page < 1:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Page out of bounds!",
                    f"Specify a page between 1 and {page_count}."
                )
            )
            return

        fields = []

        for command in comp[per * (page - 1):per * page]:
            details = "\n".join([f"**{x['name'].split(' ', 1)[1]}**: {x['value']}" for x in self.generate_command_details(command, category, prefix, True) if "Category" not in x["name"]])

            fields.append(
                {
                    "name": f"→ {category['emoji']}  {prefix}{command.name}",
                    "value": f"{command.description}\n\n{details}"
                }
            )

        if page == 1:
            backward_button = ["secondary", self.pass_]

        else:
            backward_button = ["primary", lambda *args: self.update_page("back", "edit", str(name), int(page), *args)]
        
        if page == page_count:
            forward_button = ["secondary", self.pass_]

        else:
            forward_button = ["primary", lambda *args: self.update_page("forward", "edit", str(name), int(page), *args)]

        embed = discordutils.create_embed(
            f"{category['emoji']}  {category['name']} (page {page}/{page_count})",
            f"{category['description']}\n\nYou can access {len(comp)} command{'' if len(comp) == 1 else 's'} in this category.",
            fields = fields,
            color = "invisible"
        )

        view = components.create_action_row(
            [
                components.create_button(
                    message,
                    label = "🡸",
                    id = "back",
                    style = backward_button[0],
                    callback = backward_button[1]
                ),
                components.create_button(
                    message,
                    label = "🡺",
                    id = "forward",
                    style = forward_button[0],
                    callback = forward_button[1]
                )
            ]
        )

        if gen == "new":
            await resp.send(
                embed = embed,
                view = view
            )

        else:
            await resp.edit(
                embed = embed,
                view = view
            )

    async def pass_(self, *args):
        return