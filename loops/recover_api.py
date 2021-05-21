import humecord

class RecoverAPILoop:
    def __init__(
            self
        ):

        self.type = "delay"

        self.name = "recover_api"

        self.delay = 0.5

    async def run(
            self
        ):
        if humecord.bot.api_online:
            humecord.utils.logger.log("warn", "Recover API loop was called, but API is online.")
            return

        try:
            await humecord.bot.api.get(
                humecord.bot.config.online_route["category"],
                humecord.bot.config.online_route["method"],
                {}
            )

            humecord.bot.api_online = True

            try:
                humecord.utils.logger.log("info", f"Bot API is back online. Unpausing requests.")

                try:
                    await humecord.bot.debug_channel.send(
                        embed = humecord.utils.discordutils.create_embed(
                            description = f"{humecord.bot.config.lang['emoji']['success']} **Regained connection to the bot API.**\n\nConnection regained for: `{humecord.bot.config.api_url}`\nUnpausing all events and loops.",
                            color = "success"
                        )
                    )

                except:
                    humecord.utils.logger.log_step("Failed to log to debug channel.", "red")

                try:
                    await humecord.bot.events.call("on_ready", [None])

                except:
                    humecord.utils.logger.log_step("Failed to re-run on ready event.", "red")

            except:
                humecord.utils.logger.log("error", f"Failed during API unpause.")
                humecord.utils.debug.print_traceback()

        except:
            pass
