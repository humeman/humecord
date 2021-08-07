import humecord

from humecord.utils import (
    dateutils,
    discordutils,
    hcutils,
    miscutils,
    components
)

import time

class SysLoggerCommand:
    def __init__(self):
        self.name = "syslogger"

        self.description = "Manages the system logger for Discord."

        self.aliases = ["syslog", "syslogs"]

        self.permission = "bot.dev"

        self.subcommands = {
            "__default__": {
                "function": self.list,
                "description": "Lists all system logs."
            },
            "set": {
                "function": self.toggle,
                "description": "Sets overrides.",
                "syntax": "[log types] (new state) (duration)"
            },
            "clear": {
                "function": self.clear,
                "description": "Clears overrides.",
                "syntax": "[log types]"
            },
            "pause": {
                "function": self.pause,
                "description": "Pauses logs.",
                "syntax": "[log types] (duration)"
            },
            "unpause": {
                "function": self.unpause,
                "description": "Unpauses logs.",
                "syntax": "[log types] (duration)"
            }
        }
        
        self.shortcuts = {
            # pauselogs [logs] [time]
            "pauselogs": "syslogger set %%1 off",
            "unpauselogs": "syslogger set %%1 on",
            "togglelogs": "syslogger set %%1",
            "silence": "syslogger set start,stop,api,ws off 1h",
            "unsilence": "syslogger clear start,stop,api,ws"
        }

        global bot
        from humecord import bot

    async def list(
            self, 
            message,
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb,
            preferred_gdb
        ):

        comp = []

        for name in bot.syslogger.log_types:
            enabled, status = bot.syslogger.get_status(name)

            comp.append(f"{bot.config.lang['emoji']['toggle_on' if enabled else 'toggle_off']} - **{name}** ({status})")

        await resp.send(
            embed = discordutils.create_embed(
                f"System logs",
                description = "\n\n".join(comp)
            )
        )

    async def toggle(
            self, 
            message,
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb,
            preferred_gdb
        ):

        # Get logs
        if len(args) < 4:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify log types to disable, a new state, and optionally a new time."
                )
            )
            return

        state = None
        raw_logs = args[2].split(",")
        logs = []
        actions = {}

        for log in raw_logs:
            log = log.lower()

            if log not in bot.syslogger.log_types:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid log type!",
                        f"Log type `{log}` doesn't exist."
                    )
                )
                return

            logs.append(log)
            actions[log] = []

        # Check for a state
        new_state = args[3].lower()

        if new_state in ["on", "true", "yes"]:
            state = True

        elif new_state in ["off", "false", "no"]:
            state = False

        else:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid state!",
                    f"State `{new_state}` is invalid. Specify a boolean (yes/no, true/false, etc)."
                )
            )
            return

        duration = None
        if len(args) > 4:
            try:
                duration = dateutils.parse_duration(args[4])

            except:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid time!",
                        f"Time `{args[4]}` could not be parsed. A valid duration looks like (for example): `1h30m`"
                    )
                )
                return

        if duration is not None:
            # We're setting a temporary pause
            for log in logs:
                bot.files.files["__humecord__.json"]["temp_system_logs"][log] = {
                    "override": state,
                    "expire_at": time.time() + duration
                }

                actions[log].append(f"Added temporary log override to `{'on' if state else 'off'}` for {dateutils.get_duration(duration)}")

        else:
            # Remove any temporary pause
            for log in logs:
                if log in bot.files.files["__humecord__.json"]["temp_system_logs"]:
                    del bot.files.files["__humecord__.json"]["temp_system_logs"][log]

                    actions[log].append(f"Removed old temporary log override")

                # Add state
                bot.files.files["__humecord__.json"]["system_logs"][log] = state
                actions[log].append(f"Added permanent log override to `{'on' if state else 'off'}`")

        bot.files.write("__humecord__.json")

        actions = {x: y for x, y in actions.items() if len(y) > 0}


        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']}  Set log overrides!",
                fields = [
                    {
                        "name": f"%-a% {x}",
                        "value": "\n".join(y)
                    } for x, y in actions.items()
                ],
                color = "success"
            )
        )

    async def clear(
            self, 
            message,
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb,
            preferred_gdb
        ):

        # Get logs
        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify log types to clear."
                )
            )
            return

        raw_logs = args[2].split(",")
        logs = []
        actions = {}

        for log in raw_logs:
            log = log.lower()

            if log not in bot.syslogger.log_types:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid log type!",
                        f"Log type `{log}` doesn't exist."
                    )
                )
                return

            logs.append(log)
            actions[log] = []

        for log in logs:
            if log in bot.files.files["__humecord__.json"]["temp_system_logs"]:
                del bot.files.files["__humecord__.json"]["temp_system_logs"][log]

                actions[log].append(f"Removed temporary log override")

            if log in bot.files.files["__humecord__.json"]["system_logs"]:
                del bot.files.files["__humecord__.json"]["system_logs"][log]
                
                actions[log].append(f"Removed permanent log override")

        bot.files.write("__humecord__.json")

        actions = {x: y for x, y in actions.items() if len(y) > 0}

        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']}  Cleared log overrides!",
                fields = [
                    {
                        "name": f"%-a% {x}",
                        "value": "\n".join(y)
                    } for x, y in actions.items()
                ],
                color = "success"
            )
        )

    async def pause(
            self, 
            message,
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb,
            preferred_gdb
        ):

        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify log types to pause."
                )
            )
            return

        args = ["syslogs", "set", args[2], "off"] + args[3:]

        await self.toggle(
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb
        )

    async def unpause(
            self, 
            message,
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb,
            preferred_gdb
        ):

        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify log types to unpause."
                )
            )
            return

        args = ["syslogs", "set", args[2], "on"] + args[3:]

        await self.toggle(
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb
        )