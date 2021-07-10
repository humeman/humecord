import humecord
import sys
import discord

from humecord.utils import logger


class OnReadyEvent:
    def __init__(
            self
        ):
        self.name = "hh_on_ready"
        self.description = "Internal HumeCord hooks for Discord's on_ready event."

        self.event = "on_ready"

        self.functions = {
            "populate_debug_channel": {
                "function": self.populate_debug_channel,
                "priority": 1
            },
            "tell_api": {
                "function": self.tell_api,
                "priority": 1
            },
            "ready": {
                "function": self.ready,
                "priority": 2
            }
        }

    async def populate_debug_channel(
            self,
            __
        ):
        humecord.bot.debug_channel = humecord.bot.client.get_channel(humecord.bot.config.debug_channel)

        if not humecord.bot.debug_channel:
            logger.log("error", "Debug channel does not exist.")
            sys.exit(-1)

        # Populate debug console's channel
        await humecord.bot.debug_console.prep()

    async def tell_api(
            self,
            __
        ):
        if humecord.bot.config.use_api:
            await humecord.bot.api.put(
                humecord.bot.config.ready_route["category"],
                humecord.bot.config.ready_route["method"],
                {
                    "category": humecord.bot.config.self_api,
                    "defaults": humecord.bot.config.defaults
                }
            )

    async def ready(
            self,
            __
        ):
        logger.log_step(f"Logged in as {humecord.bot.client.user} ({humecord.bot.client.user.id})", "cyan")

        description = []

        description += [
            f"Running: {humecord.bot.config.name}",
            f"Version: {humecord.bot.config.version}",
            " ",
            "Libraries:",
            f"  Humecord: {humecord.version}",
            f"  Discord: {discord.__version__}"
        ]

        if humecord.bot.config.use_api:
            description.append(f"\nAPI:\n  URL: {humecord.bot.config.api_url}\n  Self API: {humecord.bot.config.self_api}")

        description += [
            " ",
            f"Commands: {sum([len(y) for x, y in humecord.bot.commands.commands.items()])}",
        ] + [
            f"  {name}: {len(value)} command{'' if len(value) == 1 else 's'}"
            for name, value in humecord.bot.commands.commands.items()
        ]

        description += [
            "",
            f"Events: {len(humecord.bot.events.events)}",
        ] + [
            f"  {name}: {len(value)} function{'' if len(value) == 1 else 's'}"
            for name, value in humecord.bot.events.edb.items()
        ]

        description += [
            " ",
            f"Loops: {len(humecord.bot.loops.loops)}",
        ] + [
            f"  {loop.name}"
            for loop in humecord.bot.loops.loops
        ]

        linebreak = "\n"

        await humecord.bot.debug_channel.send(
            embed = humecord.utils.discordutils.create_embed(
                f"{humecord.bot.config.lang['emoji']['success']}  Client ready!",
                description = f"```yaml\n{linebreak.join(description)}```",
                color = "success"
            )
        )