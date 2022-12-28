import humecord

import time

class PostStatsLoop:
    def __init__(
            self
        ):

        self.type = "delay"

        self.delay = 60

        self.name = "post_stats"

        global bot
        from humecord import bot

    async def run(
            self
        ):

        if not hasattr(bot, "_last_stats"):
            bot._last_stats = time.time()

        # Purge old
        uptime = time.time() - bot._last_stats
        commands = dict(bot.commands.stat_cache)

        bot._last_stats = time.time()
        bot.commands.stat_cache = {
            "__total__": 0,
            "__denied__": 0
        }

        # Send off
        await bot.api.put(
            "stats",
            "update",
            {
                "bot": bot.config.self_api,
                "uptime": uptime,
                "commands": commands
            }
        )
        