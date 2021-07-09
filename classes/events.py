from ..utils import logger
from ..utils import debug
from ..utils import errorhandler
from ..utils import exceptions

from .. import events

class Events:
    def __init__(
            self,
            bot
        ):

        self.events = []

        self.registered = []

        # Force register
        self.force = [
            events.on_ready.OnReadyEvent,
            events.on_message.OnMessageEvent
        ]

        """
            "on_ready": [
                events.on_ready.populate_debug_channel,
                events.on_ready.tell_api,
                events.on_ready.ready
            ],
            "on_message": [
                events.on_message.check_dm,
                events.on_message.check_reply,
                events.on_message.check_ping,
                events.on_message.run_command,
                events.on_message.check_debug_console
            ],
            "on_interaction": [
                events.on_interaction.check_interaction
            ]
        }
        """

        @bot.client.event
        async def on_ready():
            global bot
            from .. import bot

            await bot.populate_imports()

    async def prep(
            self
        ):

        self.events = [
            *self.events,
            *self.force
        ]

        await self.load()
        await self.register()

    async def load(
            self
        ):

        # Format event database into a less intensive dict.
        self.edb = {}

        for event in self.events:
            if event.event not in self.valid_events:
                raise exceptions.InitError(
                    f"Event {event.name} tried to register event {event.event}, but it doesn't exist"
                )

            # Check if event exists
            if event.event not in self.edb:
                self.edb[event.event] = []

            # Find out where to insert
            for name, function in event.functions:
                index = 0
                prio = function["priority"]
                for i, event in enumerate(self.edb[event.event]):
                    if event.priority <= prio:
                        index = i + 1

                # Insert
                self.edb[event.event].insert(
                    index,
                    {
                        "name": name,
                        **function
                    }
                )

        """
        for event, functions in self.force.items():
            if event not in self.events:
                self.events[event] = []

            if event == "on_ready": # Take priority
                self.events[event] = [
                    *functions,
                    *self.events[event]
                ]

            else:
                self.events[event] += functions
        """

    async def call(
            self,
            event: str,
            args: list
        ):

        if event not in self.edb:
            logger.log("warn", f"Event {event} called, but isn't registered in the event database")
            return

        for function in self.edb[event]:
            result = await errorhandler.wrap(
                function["function"](*args),
                context = {
                    "Event details": [
                        f"Event name: {event}",
                        f"Function: {function['name']}",
                        f"Function description: {function.get('description')}",
                        f"Priority: {function['priority']}"
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

        for event in self.edb: # Only the name
            if event in self.registered:
                continue # Don't register twice

            if not event.startswith("hh_"):
                exec("\n".join([x[16:] for x in f"""
                @bot.client.event
                async def {event}(*args):
                    await bot.events.call("{event}", args)
                """.split("\n")]))

                self.registered.append(event)

        logger.log_step(f"Registered {len(self.edb)} events", "cyan")











