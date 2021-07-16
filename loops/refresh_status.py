import time
import datetime
import discord

import humecord

class RefreshStatusLoop:
    def __init__(
            self
        ):

        self.type = "delay"

        self.delay = 600

        self.name = "refresh_status"

    async def run(
            self
        ):

        # Retrieve status
        status = humecord.bot.files.files["__bot__.json"]["status"]

        kw = {}

        if status is not None:
            status = str(status)

            # Compile placeholders
            if "%" in status:
                for name, script in humecord.bot.config.placeholders.items():
                    try:
                        status = status.replace(f"%{name}%", str(eval(script, globals())))

                    except:
                        humecord.utils.debug.print_traceback(f"Status placeholder {name}'s eval failed.")

            # Get activity
            activity = humecord.bot.files.files["__bot__.json"]["activity"]

            kw["activity"] = humecord.utils.discordutils.generate_activity(details = status, **activity)

        # Find visibility
        visibility = eval(humecord.bot.config.visibilities[humecord.bot.files.files["__bot__.json"]["visibility"]], globals())

        # Update it
        await humecord.bot.client.change_presence(status = visibility, **kw)