import discord
import time

import humecord

from humecord.utils import (
    dateutils,
    discordutils,
    hcutils
)

class DevCommand:
    def __init__(self):
        self.name = "dev"

        self.description = "All HumeCord development controls."

        self.aliases = ["development"]

        self.permission = "bot.dev"

        self.subcommands = {
            "error": {
                "function": self.error,
                "description": "Forces an error."
            },
            "loops": {
                "function": LoopsSubcommand.run,
                "description": "Manages the bot's loops."
            }
        }

        global bot
        from humecord import bot
        

    async def error(self, message, resp, args, gdb, alternate_gdb = None, preferred_gdb = None):
        raise humecord.utils.exceptions.TestException("dev.error call")

class LoopsSubcommand:
    async def run(message, resp, args, gdb, alternate_gdb = None, preferred_gdb = None):
        # Map:
        # !dev loops
        #   list -> List loops & status
        #   run [loop] -> Force run loop
        #   pause [loop] (time/'forever') -> Pauses a loop for a set time

        if len(args) == 2:
            # Throw an error
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    f"Specify an action.\nValid actions: `list`, `run`, `pause`, `unpause`"
                )
            )

        elif len(args) == 3:
            action = args[2].lower()

            if action in ["list"]:
                await LoopsSubcommand.list_(message, resp, args, gdb, alternate_gdb, preferred_gdb)

    async def list_(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        # Compile list
        comp = []

        for loop in bot.loops.loops:
            details = [
                f"• Runs: `{hcutils.get_loop_runtime(loop)}`",
                f"• Last run: `{hcutils.get_loop_last_run(loop)} ago`"
            ]

            if loop.errors > 0:
                if loop.errors >= 3:
                    details.append(f"• Errors: `{loop.errors} (paused)`")

                else:
                    details.append(f"• Errors: `{loop.errors}`")

            if loop.pause_until:
                details.append(f"• Paused for: `{dateutils.get_duration(loop.pause_until - time.time())}`")

            comp.append(
                {
                    "name": f"→ {loop.name}",
                    "value": "\n".join(details)
                }
            )

        if len(comp) == 0:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Can't list loops!",
                    "No loops are active."
                )
            )

        else:
            await resp.send(
                embed = discordutils.create_embed(
                    f"Loops",
                    fields = comp,
                    color = "invisible"
                )
            )