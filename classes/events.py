from ..utils import logger
from ..utils import debug
from ..utils import errorhandler

from .. import events

class Events:
    def __init__(
            self,
            bot
        ):

        # Force register
        self.force = {
            "on_ready": [
                events.on_ready.populate_debug_channel,
                events.on_ready.tell_api,
                events.on_ready.ready
            ],
            "on_message": [
                events.on_message.check_ping,
                events.on_message.run_command,
                events.on_message.check_debug_console
            ],
            "on_interaction": [
                events.on_interaction.check_interaction
            ]
        }

        @bot.client.event
        async def on_ready():
            global bot
            from .. import bot

            await bot.populate_imports()

    async def prep(
            self
        ):
        await self.load()
        await self.register()

        await self.call("on_ready", [None])

    async def load(
            self
        ):
        
        self.events = bot.imports.events

        for event, functions in self.force.items():
            if event not in self.events:
                self.events[event] = []

            self.events[event] += functions

    async def call(
            self,
            event: str,
            args: list
        ):

        if event not in self.events:
            logger.log("warn", f"Event {event} called, but isn't registered in the event handler")
            return

        for function in self.events[event]:
            result = await errorhandler.wrap(
                function(*args),
                context = {
                    "Event details": [
                        f"Event name: {event}"
                    ]
                }
            )

            if result is not None:
                if result == False:
                    break

    async def register(
            self
        ):
        # Registers all the events we need.

        for event in self.events: # Only the name
            exec("\n".join([x[12:] for x in f"""
            @bot.client.event
            async def {event}(*args):
                await bot.events.call("{event}", args)
            """.split("\n")]))

        logger.log_step(f"Registered {len(self.events)} events", "cyan")











