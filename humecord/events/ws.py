import humecord

from humecord.utils import (
    discordutils,
    colors
)

class HCOnWSAction:
    def __init__(
            self
        ):

        self.name = "hc_on_ws_action"
        self.description = "Receieves commands from the configured websocket."

        self.event = "hc_on_ws_action"

        self.functions = {
            "send_command": {
                "function": self.send_command,
                "priority": 5
            }
        }

        global bot
        from humecord import bot

        global logger
        from humecord import logger

    async def send_command(
            self,
            action: str,
            data: dict
        ):

        if action != "send_command":
            return

        # Get the command
        command = data["action"]

        silent = data["data"].get("silent")

        base = f"{humecord.terminal.color['remote']}{colors.termcolors['bold']}"
        end = f"{colors.termcolors['reset']}{humecord.terminal.color['remote']} "

        if command == "reload":
            humecord.terminal.log(f"{base}>{end}reload", True)

            # Check if force reload
            safe = False if data["data"].get("force") else True

            await humecord.bot.loader.load(safe_load = safe)

            detail = [
                "Reloaded!",
                f"Safe reload: `{'Yes' if safe else 'No'}`"
            ]

        elif command == "shutdown":
            humecord.terminal.log(f"{base}>{end}shutdown", True)
            await humecord.bot.shutdown("Websocket command")

        elif command == "kill":
            humecord.terminal.log(f"{base}>{end}kill", True)
            await humecord.bot.kill()
            return

        elif command == "command":
            # Get command
            cmd = data["data"]["command"]

            humecord.terminal.log(f"{base}${end}{cmd}", True)

            await bot.console.call(cmd)

        else:
            logger.log("ws", "warn", f"Received invalid command from websocket: '{command}'")