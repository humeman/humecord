import humecord

from humecord.utils import (
    discordutils,
    dateutils,
    hcutils,
    dateutils
)

import discord
import time

class PostStatusLoop:
    def __init__(
            self
        ):

        self.type = "delay"

        self.delay = 15

        self.name = "post_status"

        global bot
        from humecord import bot

    async def run(
            self
        ):

        members = sum([len(x.members) for x in bot.client.guilds])

        info = [
            f"%-b% Uptime: `{dateutils.get_duration(time.time() - bot.timer)}`",
            f"%-b% Running since: `{dateutils.get_timestamp(bot.timer).strip()}`",
            f"%-b% Stats: `{len(bot.client.guilds)} guilds | {members} members`"
        ]

        fields = [
            {
                "name": "%-a% Info",
                "value": "\n".join(info)
            }
        ]

        loop_details = {}

        for loop in bot.loops.loops:
            details = []
            emoji = "status_green"

            if loop.last_run != -1:
                if loop.type == "delay":
                    if loop.last_run < time.time() - loop.delay - 5:
                        emoji = "status_yellow"
                        details.append(f"{dateutils.get_duration(time.time() - loop.last_run - loop.delay)} behind expected runtime")

            if loop.errors > 0:
                if loop.errors >= 3:
                    details.append(f"Errors: `{loop.errors} (paused)`")
                    emoji = "status_red"

                else:
                    details.append(f"Errors: `{loop.errors}`")
                    emoji = "status_yellow"

            if loop.pause_until:
                details.append(f"Paused for: `{dateutils.get_duration(loop.pause_until - time.time())}`")
                emoji = "status_yellow"

            lb = "\n"
            ln = loop.name.replace("_", " ").replace("-", " ")

            loop_details[f"{bot.config.lang['emoji'][emoji]}  {ln[0].upper()}{ln[1:]}"] = f"\nLast run `{hcutils.get_loop_last_run(loop)}` | Runs `{hcutils.get_loop_runtime(loop)}`{lb if len(details) > 0 else ''}{' | '.join(details)}\n"

        fields.append(
            {
                "name": "%-a% Loops",
                "value": "\n".join([f"%-b% **{x}:** {y}" for x, y in loop_details.items()])
            }
        )

        await bot.api.put(
            "status",
            "bot",
            {
                "bot": bot.config.self_api,
                "details": {
                    "fields": fields,
                    "info": f"Running {bot.config.cool_name} v{bot.config.version} (humecord {humecord.version})",
                    "cool_name": bot.config.cool_name,
                    "avatar": bot.client.user.avatar.url
                }
            }
        )