import humecord
import sys

from humecord.utils import logger

async def populate_debug_channel(__):
    humecord.bot.debug_channel = humecord.bot.client.get_channel(humecord.bot.config.debug_channel)

    if not humecord.bot.debug_channel:
        logger.log("error", "Debug channel does not exist.")
        sys.exit(-1)

    # Populate debug console's channel
    await humecord.bot.debug_console.prep()

async def ready(__):
    logger.log_step(f"Logged in as {humecord.bot.client.user} ({humecord.bot.client.user.id})", "cyan")

    description = []

    description += [
        f"Running: {humecord.bot.config.name}",
        f"Version: {humecord.bot.config.version}"
    ]

    if humecord.bot.config.use_api:
        description.append(f"\nAPI:\n  URL: {humecord.bot.config.api_url}\n  Self API: {humecord.bot.config.self_api}")

    description += [
        " ",
        f"Commands: {len(humecord.bot.commands.commands)}",
    ] + [
        f"  {name}: {len(value)} commands"
        for name, value in humecord.bot.commands.commands.items()
    ]

    description += [
        "",
        f"Events: {len(humecord.bot.events.events)}",
    ] + [
        f"  {name}: {len(value)} functions"
        for name, value in humecord.bot.events.events.items()
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
            color = "success",
            footer = f"Running HumeCord v{humecord.version}"
        )
    )