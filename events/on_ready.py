import humecord
import sys
import discord
import glob
import os
import inspect

from humecord.utils import (
    logger,
    fs,
    discordutils
)


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
            },
            "post_changelog": {
                "function": self.post_changelog,
                "priority": 3
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
            embed = discordutils.create_embed(
                f"{humecord.bot.config.lang['emoji']['success']}  Client ready!",
                description = f"```yaml\n{linebreak.join(description)}```",
                color = "success"
            )
        )

    async def post_changelog(
            self,
            __
        ):

        # Check if it's enabled
        if humecord.bot.config.send_changelogs:
            # Check if our version differs
            if humecord.bot.files.files["__humecord__.json"]["version"] != humecord.version:
                # Check for a changelog
                files = glob.glob(f"{os.path.dirname(inspect.getfile(humecord))}/changelogs/*.yml")

                current = humecord.version.replace(".", "-").lower()

                # Check for our version
                for file in files:
                    # Get filename
                    try:
                        name = file.rsplit("/", 1)[-1].split(".", 1)[0].lower()

                    except:
                        continue

                    if current == name:
                        # Found it!
                        # Read the file
                        try:
                            details = fs.read_yaml(file)

                        except:
                            logger.log("warn", f"Tried to read changelog {name}, but the YAML parser threw an error.")

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
                            logger.log_step(f"Humecord was updated to version {humecord.version}!", "cyan", bold = True)
                            logger.log_step(f"Read the changelog in your debug channel.", "cyan")

                            # Store the new version
                            humecord.bot.files.files["__humecord__.json"]["version"] = humecord.version
                            humecord.bot.files.write("__humecord__.json")
                            return

                await humecord.bot.debug_channel.send(
                    embed = discordutils.create_embed(
                        f"Humecord was updated to version {humecord.version}!",
                        description = "There is no changelog for this update.",
                        color = "blue"
                    )
                )
                            
                logger.log_step(f"Humecord was updated to version {humecord.version}!", "cyan", bold = True)