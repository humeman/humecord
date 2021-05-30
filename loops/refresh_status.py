import time
import datetime

import humecord
from humecord import bot

class RefreshStatusLoop:
    def __init__(
            self
        ):

        self.type = "period"

        self.time = "minute"

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
        visibility = eval(bot.config["visibilities"][humecord.bot.files.files["__bot__.json"]["visibility"]], globals())

        # Update it
        await eval()