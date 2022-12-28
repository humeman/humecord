import humecord
import discord

from humecord.utils import (
    debug
)

class RecoverAPILoop:
    def __init__(
            self
        ):

        self.type = "delay"

        self.name = "recover_api"

        self.delay = 0.5

        self.status_set = False

    async def run(
            self
        ):
        if humecord.bot.api_online:
            humecord.logger.log("api", "warn", "Recover API loop was called, but API is online.")
            return

        if not self.status_set:
            try:
                await humecord.bot.client.change_presence(activity = discord.Game(name = humecord.bot.config.api_error_status["status"]), status = eval(humecord.bot.config.visibilities[humecord.bot.config.api_error_status['visibility']], globals()))

            except:
                debug.print_traceback()
                humecord.logger.log("api", "warn", "Failed to update status.")

            self.status_set = True

        try:
            await humecord.bot.api.get(
                humecord.bot.config.online_route["category"],
                humecord.bot.config.online_route["method"],
                {}
            )

            humecord.bot.api_online = True

            try:
                self.status_set = False
                humecord.logger.log("api", "info", f"Bot API is back online. Unpausing requests.")

                try:
                    await humecord.bot.syslogger.send(
                        "api",
                        embed = humecord.utils.discordutils.create_embed(
                            description = f"{humecord.bot.config.lang['emoji']['success']} **Regained connection to the bot API.**\n\nConnection regained for: `{humecord.bot.config.api_url}`\nUnpausing all events and loops.",
                            color = "success"
                        )
                    )

                except:
                    humecord.logger.log_step("api", "error", "Failed to log to debug channel.")

                humecord.bot.syslogger.override["start"] = False

                try:
                    await humecord.bot.events.call("on_ready", [None])
                    await humecord.loops.refresh_status.RefreshStatusLoop.run(None)

                except:
                    debug.print_traceback()
                    humecord.logger.log_step("api", "error", "Failed to re-run on ready event.")

                if "start" in humecord.bot.syslogger.override:
                    del humecord.bot.syslogger.override["start"]

            except:
                humecord.utils.logger.log("api", "error", f"Failed during API unpause.")
                humecord.utils.debug.print_traceback()

        except:
            pass
