import humecord
import sys
import discord
import httpx
import yaml

from humecord.utils import (
    fs,
    discordutils,
    debug
)


class OnReadyEvent:
    def __init__(
            self
        ):
        self.name = "hc_on_ready"
        self.description = "Internal Humecord hooks for Discord's on_ready event."

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
            "fire_hc": {
                "function": self.fire_hc,
                "priority": 2
            },
            "ready": {
                "function": self.ready,
                "priority": 3
            },
            "start_ws": {
                "function": self.start_ws,
                "priority": 3
            },
            "post_changelog": {
                "function": self.post_changelog,
                "priority": 3
            }
        }

        global logger
        from humecord import logger

    async def populate_debug_channel(
            self,
            __ = None
        ):
        humecord.bot.debug_channel = humecord.bot.client.get_channel(humecord.bot.config.debug_channel)

        if not humecord.bot.debug_channel:
            logger.log("botinit", "error", "Debug channel does not exist.")
            sys.exit(-1)

        # Populate debug console's channel
        await humecord.bot.debug_console.prep()

    async def tell_api(
            self,
            __ = None
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
            __ = None
        ):
        logger.log_step("botinit", "start", f"Logged in as {humecord.bot.client.user} ({humecord.bot.client.user.id})")

        description = []

        if humecord.version.endswith("s"):
            description.append(
                f" > This bot is running a snapshot version of Humecord.\n > Version: {humecord.version} | Bugs ahead!\n\n"
            )

        elif humecord.version.endswith("a"):
            description.append(
                f" > This bot is running an early development version of Humecord.\n > Version: {humecord.version} | Bugs ahead!\n\n"
            )

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

        """
        description += [
            " ",
            f"Commands: {sum([len(y) for x, y in humecord.bot.commands.commands.items()])}",
        ] + [
            f"  {name}: {len(value)} command{'' if len(value) == 1 else 's'}"
            for name, value in humecord.bot.msgcommands.commands.items()
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
        ]"""

        linebreak = "\n"

        await humecord.bot.syslogger.send(
            "start",
            embed = discordutils.create_embed(
                f"{humecord.bot.config.lang['emoji']['success']}  Client ready!",
                description = f"```yaml\n{linebreak.join(description)}```",
                color = "success"
            )
        )

    async def fire_hc(
            self,
            __ = None
        ):

        await humecord.bot.events.call("hc_on_ready", [])

    async def start_ws(
            self,
            __ = None
        ):

        if hasattr(humecord.bot, "ws"):
            humecord.bot.ws.run()

    async def post_changelog(
            self,
            __ = None
        ):

        # Check if it's enabled
        if humecord.bot.config.send_changelogs:
            #if humecord.version[-1] in "as":
            #    return

            # Check if our version differs
            if humecord.bot.files.files["__humecord__.json"]["version"] != humecord.version:
                # Skip if snapshot
                if humecord.version[-1] in "abs":
                    return

                # Check for a changelog
                current = "".join([x for x in humecord.version if x in "0123456789."]).replace(".", "-").lower()

                try:
                    async with httpx.AsyncClient(http2 = True) as cl:
                        resp = await cl.get(
                            f"https://cdn.humeman.com/humecord/changelogs/{current}.yml"
                        )
                
                except:
                    debug.print_traceback(error_message = "An error occurred while retrieving this update's changelog!")
                    logger.log_step("botinit", "warn", f"Attempted URL: https://cdn.humeman.com/humecord/changelogs/{current}.yml")
                    logger.log_step("botinit", "start", f"Humecord was updated to version {humecord.version}!", bold = True)
                    await humecord.bot.debug_channel.send(
                        embed = discordutils.create_embed(
                            f"Humecord was updated to version {humecord.version}!",
                            description = "There is no changelog for this update.",
                            color = "blue"
                        )
                    )

                else:
                    # Found it!
                    # Read the file
                    try:
                        details = yaml.safe_load(resp.text)

                    except:
                        debug.print_traceback("Changelog read")
                        logger.log("botinit", "warn", f"Tried to read changelog {current}, but the YAML parser threw an error.")
                        return

                    else:
                        # Paginate the changelog.
                        #   Create a new embed after every 6,000 characters, or 25 fields.
                        comp = [[]]
                        i = 0

                        # Generate a running total - first embed will be longer
                        total = 30 + len(details["version"]) + len(details["description"])

                        for change in details["changes"]:
                            # Add to the total (+10, for our added characters)
                            cur_total = len(change["name"]) + len(change["value"]) + 10

                            # Check if we're too long
                            if len(comp[i]) >= 25 or total + cur_total >= 6000:
                                # Reset it
                                i += 1
                                total = 0
                                comp.append([])

                            total += cur_total

                            comp[i].append(
                                {
                                    "name": f"%-a% {change['name']}",
                                    "value": change["value"]
                                }
                            )


                        # Create an embed
                        for i, fields in enumerate(comp):
                            if i == 0:
                                embed = discordutils.create_embed(
                                    f"Humecord was updated to version {details['version']}!",
                                    description = details["description"],
                                    fields = fields,
                                    color = "blue"
                                )

                            else:
                                embed = discordutils.create_embed(
                                    fields = fields,
                                    color = "blue"
                                )

                            # Send the embed
                            await humecord.bot.debug_channel.send(
                                embed = embed
                            )

                        # Log it
                        logger.log_step("botinit", "start", f"Humecord was updated to version {humecord.version}!", bold = True)
                        logger.log_step("botinit", "start", f"Read the changelog in your debug channel.")

                        # Store the new version
                        humecord.bot.files.files["__humecord__.json"]["version"] = humecord.version
                        humecord.bot.files.write("__humecord__.json")