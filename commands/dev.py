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

        self.shortcuts = {
            "loops": "dev loops",
            "loop": "dev loops"
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
        #   reset [loop] -> Resets a loop (errors, time, all)

        if len(args) >= 3:
            action = args[2].lower()

            if action in ["list"]:
                await LoopsSubcommand.list_(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            elif action in ["run"]:
                await LoopsSubcommand.run_(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            elif action in ["pause"]:
                await LoopsSubcommand.pause(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            elif action in ["unpause"]:
                await LoopsSubcommand.unpause(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            elif action in ["reset"]:
                await LoopsSubcommand.reset(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

        await resp.send(
            embed = discordutils.error(
                message.author,
                "Invalid syntax!",
                f"Specify an action.\nValid actions: `list`, `run`, `pause`, `unpause`, `reset`"
            )
        )

    async def list_(message, resp, args, gdb, alternate_gdb, preferred_gdb):
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

    async def run_(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        if len(args) < 4:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a loop to force run."
                )
            )
            return

        loop = LoopsSubcommand.get_loop(
            args[3].lower()
        )

        if loop is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid loop!",
                    f"Loop '{args[3].lower()}' does not exist."
                )
            )
            return

        humecord.bot.client.loop.create_task(
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

    async def pause(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        if len(args) < 4:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a loop to force run."
                )
            )
            return

        loop = LoopsSubcommand.get_loop(
            args[3].lower()
        )

        if loop is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid loop!",
                    f"Loop '{args[3].lower()}' does not exist."
                )
            )
            return

        if len(args) == 4:
            # Pause indefinitely
            loop.pause = True
            details = "Indefinitely"

        else:
            try:
                duration = dateutils.parse_duration(args[4])

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

    async def unpause(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        if len(args) < 4:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a loop to force run."
                )
            )
            return

        loop = LoopsSubcommand.get_loop(
            args[3].lower()
        )

        if loop is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid loop!",
                    f"Loop '{args[3].lower()}' does not exist."
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

    async def reset(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        if len(args) < 4:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a loop to force run."
                )
            )
            return

        loop = LoopsSubcommand.get_loop(
            args[3].lower()
        )

        if loop is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid loop!",
                    f"Loop '{args[3].lower()}' does not exist."
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
            actions.append(f"• Reset last run time (last run on {humecord.bot.files.files['__loops__.json'][loop.name]['last_run']})")
            humecord.bot.files.files["__loops__.json"][loop.name]["last_run"] = "Never"
            humecord.bot.files.write("__loops__.json")

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


    def get_loop(loop_name):
        for loop in humecord.bot.loops.loops:
            if loop.name == loop_name:
                return loop