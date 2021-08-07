from humecord.utils import (
    debug,
    exceptions,
    dateutils
)

import time

class SystemLogger:
    def __init__(
            self
        ): 

        self.log_types = {
            "start": True,
            "stop": True,
            "api": True,
            "ws": True,
            "error": True
        }

        self.override = {}

        global bot
        from humecord import bot

    async def send(
            self,
            message_type: str,
            *args,
            **kwargs
        ):

        if message_type not in self.log_types:
            raise exceptions.DevError(f"System log type {message_type} doesn't exist")

        run = self.log_types[message_type]

        # Lowest priority: File storage
        if hasattr(bot, "files"):
            if message_type in bot.files.files["__humecord__.json"]["system_logs"]:
                run = bot.files.files["__humecord__.json"]["system_logs"][message_type]

        # Medium priority: Overrides
        if message_type in self.override:
            run = self.override[message_type]

        # Highest priority: Temporary overrides
        if hasattr(bot, "files"):
            if message_type in bot.files.files["__humecord__.json"]["temp_system_logs"]:
                details = bot.files.files["__humecord__.json"]["temp_system_logs"][message_type]
                # Verify that it's still active
                if time.time() < details["expire_at"]:
                    run = details["override"]

        if run:
            await bot.debug_channel.send(
                *args,
                **kwargs
            )

    async def purge_expired(
            self
        ):

        t = time.time()
        rem = []

        for name, details in bot.files.files["__humecord__.json"]["temp_system_logs"].items():
            if t > details["expire_at"]:
                rem.append(name)

        for name in rem:
            del bot.files.files["__humecord__.json"]["temp_system_logs"][name]

        if len(rem) > 0:
            bot.files.write("__humecord__.json")

    def get_status(
            self,
            message_type
        ):

        if message_type not in self.log_types:
            raise exceptions.DevError(f"System log type {message_type} doesn't exist")

        run = self.log_types[message_type]
        status = "default"

        if message_type in bot.files.files["__humecord__.json"]["system_logs"]:
            run = bot.files.files["__humecord__.json"]["system_logs"][message_type]
            status = "permanent override"
        
        if message_type in self.override:
            run = self.override[message_type]
            status = "session override"

        if message_type in bot.files.files["__humecord__.json"]["temp_system_logs"]:
            details = bot.files.files["__humecord__.json"]["temp_system_logs"][message_type]
            # Verify that it's still active
            if time.time() < details["expire_at"]:
                run = details["override"]
                status = f"temporary override for {dateutils.get_duration(details['expire_at'] - time.time())}"

        return run, status