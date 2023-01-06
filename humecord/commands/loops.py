"""
/loops: humecord base commands

Manages loop execution.
"""

import asyncio
import glob
import time
from typing import Optional
import aiofiles

import humecord

from humecord.classes import (
    discordclasses
)

from humecord.utils import (
    discordutils,
    hcutils,
    dateutils
)

class LoopsCommand(humecord.Command):
    def __init__(
            self
        ) -> None:
        self.name = "loops"
        self.description = "Manages loop execution."
        self.command_tree = {
            "%loop%": self.run,
        }
        self.args = {
            "loop": {
                "required": False,
                "type": "str",
                "description": "Loop to manage."
            }
        }
        self.subcommand_details = {}
        self.messages = {}
        self.dev = True
        self.perms = "bot.dev"
        self.default_perms = "guild.admin"

        global bot
        from humecord import bot
    
    async def run(
            self,
            resp: humecord.ResponseChannel,
            ctx: humecord.Context
        ) -> None:

        if ctx.args.exists("loop"):
            # Run the loop's callback, if it exists
            loop_name = ctx.args.loop.lower()

            loop = None
            for loop_ in bot.loops.loops:
                if loop_name == loop_.name.lower():
                    loop = loop_


            if loop is None:
                await resp.error(
                    ctx.user,
                    "Invalid loop!",
                    f"Valid loops include: {', '.join([f'`{x.name}`' for x in bot.loops.loops])}"
                )

            await self.view(
                resp,
                ctx,
                loop
            )

        else:
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

                if loop.pause:
                    details.append(f"• Paused indefinitely")

                comp.append(
                    {
                        "name": f"→ {loop.name}",
                        "value": "\n".join(details)
                    }
                )

            if len(comp) == 0:
                await resp.send(
                    embed = discordutils.error(
                        ctx.user,
                        "Can't list loops!",
                        "No loops are active."
                    )
                )

            else:
                await resp.send(
                    embed = discordutils.create_embed(
                        "Loops",
                        fields = comp,
                        color = "invisible"
                    )
                )

    async def view(
            self,
            resp: humecord.ResponseChannel,
            ctx: humecord.Context,
            loop
        ) -> None:

        details = []
        buttons = []

        if hasattr(loop, "description"):
            details.append(f"*{loop.description}*")

        details += [
            f"• Runs: `{hcutils.get_loop_runtime(loop)}`",
            f"• Last run: `{hcutils.get_loop_last_run(loop)}`"
        ]

        if loop.errors > 0:
            if loop.errors >= 3:
                details.append(f"• Errors: `{loop.errors} (paused)`")

            else:
                details.append(f"• Errors: `{loop.errors}`")

        use_pause = True
        if loop.pause_until:
            if loop.pause_until > time.time():
                use_pause = False
                details.append(f"• Paused for: `{dateutils.get_duration(loop.pause_until - time.time())}`")

        if loop.pause:
            use_pause = False
            details.append(f"• Paused indefinitely")


        if use_pause:
            pause_button = await bot.interactions.create_button(
                "pause",
                callback = lambda *args: self.pause(*args, loop),
                sender = ctx.user,
                label = "Pause",
                emoji = bot.config.lang['emoji']['pause'],
                style = humecord.ButtonStyles.GRAY
            )

        else:
            pause_button = await bot.interactions.create_button(
                "pause",
                callback = lambda *args: self.unpause(*args, loop),
                sender = ctx.user,
                label = "Unpause",
                emoji = bot.config.lang['emoji']['play'],
                style = humecord.ButtonStyles.GRAY
            )


        embed = discordutils.create_embed(
            f"{bot.config.lang['emoji']['info']}  Loop '{loop.name}'",
            "\n".join(details)
        )

        # Create a view of various actions
        view = await bot.interactions.create_view(
            [
                await bot.interactions.create_button(
                    "refresh",
                    callback = lambda *args: self.view(*args, loop),
                    sender = ctx.user,
                    label = "Refresh",
                    emoji = bot.config.lang['emoji']['undo'],
                    style = humecord.ButtonStyles.GREEN
                ),
                await bot.interactions.create_button(
                    "run",
                    callback = lambda *args: self.run_loop(*args, loop),
                    sender = ctx.user,
                    label = "Run",
                    emoji = bot.config.lang['emoji']['forward'],
                    style = humecord.ButtonStyles.GRAY
                ),
                pause_button,
                await bot.interactions.create_button(
                    "reset",
                    callback = lambda *args: self.reset(*args, loop),
                    sender = ctx.user,
                    label = "Reset",
                    emoji = bot.config.lang['emoji']['backward'],
                    style = humecord.ButtonStyles.GRAY
                )
            ]
        )

        await resp.edit(
            embed = embed,
            view = view
        )

    async def run_loop(
            self,
            resp: humecord.ResponseChannel,
            ctx: humecord.Context,
            loop
        ) -> None:
        
        bot.client.loop.create_task(
            humecord.utils.errorhandler.wrap(
                loop.run(),
                context = {
                    "Loop details": [
                        f"Loop: `{loop.name}`",
                        f"Manual call by: <@{ctx.user.id}>"
                    ]
                }
            )
        )

        await asyncio.sleep(0.2)

        await self.view(
            resp,
            ctx,
            loop
        )
    
    async def unpause(
            self,
            resp: humecord.ResponseChannel,
            ctx: humecord.Context,
            loop
        ) -> None:
        actions = []

        loop.pause = False
        loop.pause_until = None
        loop.errors = 0

        await self.view(
            resp,
            ctx,
            loop
        )

    async def pause(
            self,
            resp: humecord.ResponseChannel,
            ctx: humecord.Context,
            loop
        ) -> None:

        # Show the user a modal asking for a duration
        modal = await bot.interactions.create_modal(
            "pause_time",
            callback = lambda *args: self.pause_recv(*args, loop),
            sender = ctx.user,
            title = f"Pause '{loop.name}'",
            components = [
                await bot.interactions.create_textinput(
                    "time",
                    label = "Pause duration",
                    placeholder = "Blank for indefinite",
                    required = False,
                    min_length = 0
                )
            ]
        )

        await resp.send_modal(modal)

    async def pause_recv(
            self,
            resp: humecord.ResponseChannel,
            ctx: humecord.Context,
            loop
        ) -> None:
        duration_str = ctx.modal_args.get("time")

        if duration_str is None:
            # Pause indefinitely
            loop.pause = True

        elif len(duration_str) == 0:
            loop.pause = True

        else:
            try:
                duration = dateutils.parse_duration(duration_str)

            except Exception as e:
                await resp.edit(
                    embed = discordutils.error(
                        ctx.user,
                        "Invalid pause duration!",
                        f"Error: {str(e)}"
                    )
                )
                return

            # Add to pause_until
            loop.pause_until = int(time.time()) + int(duration)

        await self.view(
            resp,
            ctx,
            loop
        )

    async def reset(
            self,
            resp: humecord.ResponseChannel,
            ctx: humecord.Context,
            loop
        ) -> None:
        actions = []

        loop.pause = False
        loop.pause_until = None
        loop.errors = 0

        await self.view(
            resp,
            ctx,
            loop
        )