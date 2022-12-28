import discord
import humecord
from humecord.utils import (
    discordutils,
    miscutils,
    components,
    dateutils,
    miscutils,
    hcutils
)

import traceback
import asyncio
import time
import random

class LoopsCommand:
    def __init__(
            self
        ):

        self.name = "loops"

        self.description = "Manages Humecord loops."

        self.aliases = ["loop"]

        self.permission = "bot.dev"
        
        self.permission_hide = True

        self.subcommands = {
            "list": {
                "function": self.list,
                "description": "Lists all running loops and their statuses."
            },
            "run": {
                "function": self.run,
                "description": "Forces a loop to run.",
                "syntax": "[loop]"
            },
            "pause": {
                "function": self.pause,
                "description": "Pauses a loop for a specified amount of time.",
                "syntax": "[loop] [time]"
            },
            "unpause": {
                "function": self.unpause,
                "description": "Unpauses a loop.",
                "syntax": "[loop]"
            },
            "reset": {
                "function": self.reset,
                "description": "Resets a loop's run data, and forces it to run.",
                "syntax": "[loop]"
            }
        }

        global bot
        from humecord import bot

    async def list(
            self,
            message, 
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb, 
            preferred_gdb
        ):
        # Compile list
        comp = []

        for loop in bot.loops.loops:
            details = [
                f"• Runs: `{hcutils.get_loop_runtime(loop)}`",
                f"• Last run: `{hcutils.get_loop_last_run(loop)}`"
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

    async def run(
            self,
            message, 
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb, 
            preferred_gdb
        ):
        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a loop to force run."
                )
            )
            return

        loop = self.get_loop(
            args[2].lower()
        )

        if loop is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid loop!",
                    f"Loop '{args[2].lower()}' does not exist."
                )
            )
            return

        bot.client.loop.create_task(
            humecord.utils.errorhandler.wrap(
                loop.run(),
                context = {
                    "Loop details": [
                        f"Loop: `{loop.name}`",
                        f"Manual call by: <@{message.author.id}>"
                    ]
                }
            )
        )

        await resp.send(
            embed = discordutils.create_embed(
                f"Ran loop {loop.name}",
                description = "Make sure to check the debug channel for errors - they will not be forwarded here.",
                color = "green"
            )
        )

    async def pause(
            self,
            message, 
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb, 
            preferred_gdb
        ):
        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a loop to force run."
                )
            )
            return

        loop = self.get_loop(
            args[2].lower()
        )

        if loop is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid loop!",
                    f"Loop '{args[2].lower()}' does not exist."
                )
            )
            return

        if len(args) == 3:
            # Pause indefinitely
            loop.pause = True
            details = "Indefinitely"

        else:
            try:
                duration = dateutils.parse_duration(args[3])

            except Exception as e:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid duration!",
                        f"{str(e)}"
                    )
                )
                return

            # Add to pause_until
            loop.pause_until = int(time.time()) + int(duration)
            details = f"For {dateutils.get_duration(duration)}"

        await resp.send(
            embed = discordutils.create_embed(
                f"Paused loop {loop.name}.",
                description = f"Paused: `{details}`\n\nUnpause it with `{preferred_gdb['prefix']}dev loops unpause {loop.name}`.",
                color = "green"
            )
        )

    async def unpause(
            self,
            message, 
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb, 
            preferred_gdb
        ):

        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a loop to force run."
                )
            )
            return

        loop = self.get_loop(
            args[2].lower()
        )

        if loop is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid loop!",
                    f"Loop '{args[2].lower()}' does not exist."
                )
            )
            return

        actions = []

        if loop.pause:
            loop.pause = False
            actions.append("• Removed indefinite pause")

        if loop.pause_until:
            actions.append(f"• Removed timer pause (was due to expire in {dateutils.get_duration(loop.pause_until - int(time.time()))})")
            loop.pause_until = None

        if loop.errors >= 3:
            actions.append(f"• Reset error counter (was at {loop.errors})")

        await resp.send(
            embed = discordutils.create_embed(
                f"Unpaused loop {loop.name}.",
                fields = [
                    {
                        "name": f"→ **Actions:**",
                        "value": "\n".join(actions)
                    }
                ],
                color = "green"
            )
        )

    async def reset(
            self,
            message, 
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb, 
            preferred_gdb
        ):
        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a loop to force run."
                )
            )
            return

        loop = self.get_loop(
            args[2].lower()
        )

        if loop is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid loop!",
                    f"Loop '{args[2].lower()}' does not exist."
                )
            )
            return

        actions = []

        if loop.pause:
            loop.pause = False
            actions.append("• Removed indefinite pause")

        if loop.pause_until:
            actions.append(f"• Removed timer pause (was due to expire in {dateutils.get_duration(loop.pause_until - int(time.time()))})")
            loop.pause_until = None

        if loop.errors > 0:
            actions.append(f"• Reset error counter (was at {loop.errors})")

        if loop.type == "delay":
            actions.append(f"• Reset run delay (last run {dateutils.get_duration(int(time.time()) - loop.last_run)} ago)")
            loop.last_run = -1
        
        elif loop.type == "period":
            actions.append(f"• Reset last run time (last run on {bot.files.files['__loops__.json'][loop.name]['last_run']})")
            bot.files.files["__loops__.json"][loop.name]["last_run"] = "Never"
            bot.files.write("__loops__.json")

        await resp.send(
            embed = discordutils.create_embed(
                f"Reset loop {loop.name}.",
                fields = [
                    {
                        "name": f"→ **Actions:**",
                        "value": "\n".join(actions)
                    }
                ],
                color = "green"
            )
        )

    def get_loop(
            self,
            loop_name
        ):
        for loop in bot.loops.loops:
            if loop.name == loop_name:
                return loop