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
        status = str(humecord.bot.files.files["__bot__.json"]["status"])

        # Compile placeholders
        if "%" in status:
            for name, script in humecord.bot.config.placeholders.items():
                try:
                    status = status.replace(f"%{name}%", str(eval(script, globals())))

                except:
                    humecord.utils.debug.print_traceback(f"Status placeholder {name}'s eval failed.")

        # Find visibility
        visibility = eval(humecord.bot.config.visibilities[humecord.bot.files.files["__bot__.json"]["visibility"]], globals())

        # Get activity
        activity = humecord.bot.files.files["__bot__.json"]["activity"]

        # Update it
        await humecord.bot.client.change_presence(status = visibility, activity = humecord.utils.discordutils.generate_activity(details = status, **activity))