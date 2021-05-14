import humecord
import sys

from humecord.utils import logger

async def prep(__):
    global bot
    from humecord.bot import bot

async def populate_debug_channel(__):
    bot.debug_channel = bot.client.get_channel(bot.config.debug_channel)

    if not bot.debug_channel:
        logger.log("error", "Debug channel does not exist.")
        sys.exit(-1)

async def ready(__):
    description = []

    description += [
        f"Running: {bot.config.name}",
        f"Version: {bot.config.version}"
    ]

    if bot.config.use_api:
        description.append(f"\nAPI:\n  URL: {bot.config.api_url}\n  Self API: {bot.config.self_api}")

    """
    description += [
        " ",
        f"Commands: {len(bot.commands.commands)}",
    ] + [
        f"  {name}: {len(value)} commands"
        for name, value in bot.commands.commands.items()
    ]
    """

    description += [
        "",
        f"Events: {len(bot.events.events)}",
    ] + [
        f"  {name}: {len(value)} functions"
        for name, value in bot.events.events.items()
    ]

    """
    description += [
        " ",
        f"Loops: {len(bot.loops.loops)}",
    ] + [
        f"  {name}"
        for name in bot.loops.loops
    ]
    """

    linebreak = "\n"

    await bot.debug_channel.send(
        embed = humecord.utils.discordutils.create_embed(
            "Client ready!",
            description = f"```yaml\n{linebreak.join(description)}```",
            color = "green",
            footer = f"Running HumeCord v{humecord.version}"
        )
    )