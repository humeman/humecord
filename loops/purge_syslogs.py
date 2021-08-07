class PurgeSyslogsLoop:
    def __init__(
            self
        ):

        self.type = "delay"

        self.delay = 5

        self.name = "purge_syslogs"

        global bot
        from humecord import bot

    async def run(
            self
        ):

        await bot.syslogger.purge_expired()
