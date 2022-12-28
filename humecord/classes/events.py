from ..utils import debug
from ..utils import errorhandler
from ..utils import exceptions

from .. import events

import humecord

class Events:
    def __init__(
            self,
            bot
        ):

        global logger
        from humecord import logger

        self.events = []

        self.registered = []

        self.valid_events = [
            "hc_on_stop",
            "hc_on_ready",
            "hc_on_reload",
            "hc_on_command",
            "hc_on_ws_action",
            "hc_on_ws_response",
            "hc_on_perma_interaction",
            "on_connect",
            "on_shard_connect",
            "on_disconnect",
            "on_shard_disconnect",
            "on_ready",
            "on_shard_ready",
            "on_resumed",
            "on_shard_resumed",
            "on_socket_raw_receive",
            "on_socket_raw_send",
            "on_typing",
            "on_message",
            "on_message_delete",
            "on_bulk_message_delete",
            "on_raw_message_delete",
            "on_raw_bulk_message_delete",
            "on_message_edit",
            "on_raw_message_edit",
            "on_reaction_add",
            "on_raw_reaction_add",
            "on_reaction_remove",
            "on_raw_reaction_remove",
            "on_reaction_clear",
            "on_raw_reaction_clear",
            "on_reaction_clear_emoji",
            "on_raw_reaction_clear_emoji",
            "on_interaction",
            "on_private_channel_update",
            "on_private_channel_pins_update",
            "on_guild_channel_create",
            "on_guild_channel_delete",
            "on_guild_channel_update",
            "on_guild_channel_pins_update",
            "on_thread_join",
            "on_thread_remove",
            "on_thread_delete",
            "on_thread_member_join",
            "on_thread_member_remove",
            "on_thread_update",
            "on_guild_integrations_update",
            "on_integration_create",
            "on_integration_update",
            "on_raw_integration_delete",
            "on_webhooks_update",
            "on_member_join",
            "on_member_remove",
            "on_member_update",
            "on_presence_update",
            "on_user_update",
            "on_guild_join",
            "on_guild_remove",
            "on_guild_update",
            "on_guild_role_create",
            "on_guild_role_delete",
            "on_guild_role_update",
            "on_guild_emojis_update",
            "on_guild_available",
            "on_guild_unavailable",
            "on_voice_state_update",
            "on_stage_instance_create",
            "on_stage_instance_delete",
            "on_stage_instance_update",
            "on_member_ban",
            "on_member_unban",
            "on_invite_create",
            "on_invite_delete",
            "on_group_join",
            "on_group_remove"
        ]

        # Force register
        """self.force = [
            events.on_ready.OnReadyEvent,
            events.on_message.OnMessageEvent
        ]"""

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

    def get_imports(
            self
        ):

        return [
            {
                "imp": "from humecord.events import on_message",
                "module": "on_message",
                "class": "OnMessageEvent"
            },
            {
                "imp": "from humecord.events import on_ready",
                "module": "on_ready",
                "class": "OnReadyEvent"
            },
            {
                "imp": "from humecord.events import ws",
                "module": "ws",
                "class": "HCOnWSAction"
            }
        ]

    async def prep(
            self
        ):

        await self.load()
        await self.register()

    async def load(
            self
        ):

        # Format event database into a less intensive dict.
        self.edb = {}

        for event in self.events + humecord.extra_events:
            if event.event not in self.valid_events:
                raise exceptions.InitError(
                    f"Event {event.name} tried to register event {event.event}, but it doesn't exist"
                )

            # Check if event exists
            if event.event not in self.edb:
                self.edb[event.event] = []

            # Find out where to insert
            for name, function in event.functions.items():
                index = 0
                prio = function["priority"]
                for i, func in enumerate(self.edb[event.event]):
                    if func["priority"] <= prio:
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
            #logger.log("events", "warn", f"Event {event} called, but isn't registered in the event database")
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

            if not event.startswith("hc_"):
                exec("\n".join([x[16:] for x in f"""
                @bot.client.event
                async def {event}(*args):
                    await bot.events.call("{event}", args)
                """.split("\n")]))

                self.registered.append(event)

        logger.log_step("botinit", "start", f"Registered {len(self.edb)} events")











