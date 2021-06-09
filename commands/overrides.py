import discord
from humecord.utils import (
        discordutils,
        exceptions
    )


class OverridesCommand:
    def __init__(
            self
        ):

        self.name = "overrides"
        self.description = "Allows you to manage overrides over the rest of my bots."

        self.aliases = ["override"]

        self.permission = "guild.admin"

        self.subcommands = {
            "__default__": {
                "function": self.list,
                "description": "List all overrides."
            },
            "__syntax__": {
                "function": self.edit,
                "description": "Edit overrides."
            }
        }

        global bot
        from humecord import bot

    async def list(
            self,
            message,
            resp,
            args,
            gdb,
            alternate_gdb = None,
            preferred_gdb = None
        ):

        overrides = await bot.overrides.get_priorities(
            message.guild.id
        )

        comp = []
        listified = {}

        for bot_name, priority in overrides.items():
            if priority not in listified:
                listified[priority] = []

            listified[priority].append(bot_name)

        # Sort
        listified = {k: v for k, v in sorted(listified.items(), key = lambda item: item[0])}

        description = "\n".join(f"{priority}: {', '.join(bots)}" for priority, bots in listified.items())

        await resp.send(
            embed = discordutils.create_embed(
                title = f"{message.guild.name}'s overrides",
                description = f"A lower priority (ex: 1) will override bots of higher priorities (ex: 10).\nTo update these values, run `{preferred_gdb['prefix']}overrides <NEW VALUE/'all'>`.\n```yml\n{description}\n```",
                color = "invisible"
            )
        )

    async def edit(
            self,
            message,
            resp,
            args,
            gdb,
            alternate_gdb = None,
            preferred_gdb = None
        ):

        change = args[1].lower()

        if change in ["all"]:
            overrides = await bot.overrides.get_priorities(
                message.guild.id
            )

            offset = []
            for bot_name, priority in overrides.items():
                if priority < 3:
                    await bot.overrides.set_priority(
                        message.guild.id,
                        3,
                        bot_name
                    )
                    offset.append(bot_name)

            await bot.overrides.set_priority(
                message.guild.id,
                1
            )

            if len(offset) > 0:
                extra = f"\nOverrode priorities of: `{', '.join(offset)}` → 3"

            else:
                extra = ""

            await resp.send(
                embed = discordutils.create_embed(
                    title = "Updated overrides!",
                    description = f"I will now override all other bots.\n**Note:** Override changes can take up to 30 seconds to fully propagate.\n\nSet priority of: `{bot.config.self_api}` → 1{extra}",
                    color = "green"
                )
            )

        elif change in ["test"]:
            if len(args) < 3:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Can't test!",
                        "To test overrides, pass a list of bots."
                    )
                )
                return

            bots = args[2].lower().split(",")

            try:
                overrides = await bot.overrides.check(
                    message.guild.id, 
                    bots, 
                    return_name = True
                )

            except exceptions.APIError:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Failed to get overrides!",
                        "One or more bot names may be invalid."
                    )
                )

            if overrides == bot.config.self_api:
                desc = "does"
                extra = ""

            else:
                desc = "does not"
                extra = f"\n\nBot `{overrides}` takes priority instead."

            await resp.send(
                embed = discordutils.create_embed(
                    title = "Tested overrides.",
                    description = f"Bot {bot.config.self_api} {desc} override bots `{', '.join(bots)}`.{extra}",
                    color = "invisible"
                )
            )

        else:
            bot_name = None
            updating_self = False
            try:
                priority = int(change)

                if priority < 0 or priority > 999:
                    raise Exception()

            except:
                # Check if they specified a bot instead
                try:
                    if len(args) == 3:
                        bot_name = args[1]
                        priority = int(args[2])

                        updating_self = False

                        if priority < 0 or priority > 999:
                            raise Exception()

                        if bot_name not in bot.config.globals.override_bots:
                            raise Exception()

                except:
                    await resp.send(
                        embed = discordutils.error(
                            message.author,
                            "Can't set overrides!",
                            f"Specify new overrides in one of two ways:\n`{preferred_gdb['prefix']}overrides [NEW VALUE]` - Set overrides for this bot\n`{preferred_gdb['prefix']}overrides [BOT] [NEW VALUE]` - Set overrides for another bot\n\nKeep in mind that the priority must be a number between 1 and 999."
                        )
                    )
                    return

            if bot_name is None:
                bot_name = bot.config.self_api

            await bot.overrides.set_priority(
                message.guild.id,
                priority,
                bot_name
            )

            apost = "'" # Disgostang
            await resp.send(
                embed = discordutils.create_embed(
                    title = f"Updated overrides!",
                    description = f"{'My' if updating_self else f'{bot_name}{apost}s'} priority is now `{priority}`.\n**Note:** Override changes can take up to 30 seconds to fully propagate.",
                    color = "green"
                )
            )