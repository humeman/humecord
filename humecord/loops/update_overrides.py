import humecord

class UpdateOverridesLoop:
    def __init__(
            self
        ):

        self.type = "delay"

        self.delay = 30

        self.name = "update_overrides"

    async def run(
            self
        ):
        await humecord.bot.overrides.put_guilds(
            [x.id for x in humecord.bot.client.guilds]
        )