import websockets
import asyncio
import json
import traceback

import humecord

from humecord.utils import (
    debug,
    discordutils,
    exceptions
)

class WSInterface:
    def __init__(
            self
        ):

        self.url = humecord.bot.config.ws_url

        self.auth = humecord.bot.config.ws_auth

        self.errors = 0
        self.stop = False

        self.connected = False

        global logger
        from humecord import logger

    async def close(
            self
        ):

        # Stop running
        self.stop = True

        # Kill the main task
        if hasattr(self, "send_task"):
            for task in [self.recv_task, self.send_task]:
                try:
                    task.cancel()

                except:
                    pass

            # Close the websocket
            try:
                await self.socket.close(code = 1000)

            except:
                pass

        # Kill the reboot loop
        if hasattr(self, "main_loop_task"):
            try:
                self.main_loop_task.cancel()

            except:
                pass

        self.main_loop_task = None

    def run(
            self
        ):

        humecord.bot.client.loop.create_task(self.async_run())

    async def async_run(
            self
        ):
        if hasattr(self, "main_loop_task"):
            if self.main_loop_task is not None:
                if not self.main_loop_task.done():
                    return

        self.main_loop_task = humecord.bot.client.loop.create_task(self.start_loop())

        while not self.main_loop_task.done():
            await asyncio.sleep(0.01)

        try:
            exc = self.main_loop_task.exception()

            if exc is not None:
                raise exc

        except (asyncio.CancelledError, asyncio.exceptions.InvalidStateError):
            pass

    async def start_loop(
            self
        ):
        log = False

        while self.errors < 3 and not self.stop:
            err = None
            try:
                await self.start()
                self.connected = True

                if log:
                    logger.log("ws", "info", "Websocket connection regained.")
                    await humecord.bot.syslogger.send(
                        "ws",
                        embed = discordutils.create_embed(
                            f"{humecord.bot.config.lang['emoji']['success']}  Websocket reconnected.",
                            color = "success"
                        )
                    )
                    log = False

            except (websockets.ConnectionClosedError, OSError) as e:
                if type(e) == OSError and "[Errno 111]" not in str(e):
                    err = e
                    
                else:
                    if not log:
                        logger.log("ws", "warn", "Websocket is disconnected. Will retry indefinitely.")
                        try:
                            await humecord.bot.syslogger.send(
                                "ws",
                                embed = discordutils.create_embed(
                                    f"{humecord.bot.config.lang['emoji']['warning']}  Websocket disconnected.",
                                    color = "warning"
                                )
                            )
                        
                        except:
                            logger.log_step("ws", "warn", "Failed to log to debug channel. Internet connection lost?", "yellow")

                        log = True

                    await asyncio.sleep(1)
                    continue

            except exceptions.CloseLoop as e:
                raise e

            except Exception as e:
                err = e

            if err is not None:
                try:
                    raise err

                except:
                    debug.print_traceback(f"A websocket connection exception occurred.")

                    self.errors += 1

                    # Log
                    try:
                        await humecord.bot.syslogger.send(
                            "ws",
                            embed = discordutils.create_embed(
                                f"{humecord.bot.config.lang['emoji']['error']}  Websocket encountered an error.",
                                description = f"Error count is now at {self.errors}. If 3 are reached, the websocket will shut down.\n```py\n{traceback.format_exc()[:3900]}```",
                                color = "error"
                            )
                        )

                    except:
                        logger.log("ws", "warn", "Failed to log websocket error alert to debug channel.")

                await asyncio.sleep(5)

            self.connected = False

        if self.errors >= 3:
            logger.log("ws", "error", "Websocket is shutting down - error threshold has been reached.")
            try:
                await humecord.bot.debug_channel.send(
                    embed = discordutils.create_embed(
                        f"{humecord.bot.config.lang['emoji']['error']}  Websocket is shutting down.",
                        description = "3 errors have occurred, so the websocket is shutting down. Reboot the bot to bring it back.",
                        color = "error"
                    )
                )

            except:
                logger.log("ws", "warn", "Failed to log websocket error alert to debug channel.")

    async def start(
            self
        ):
        self.socket = await websockets.connect(
            self.url
        )

        self.recv_task = humecord.bot.client.loop.create_task(self.recv_())
        self.send_task = humecord.bot.client.loop.create_task(self.send_())

        done, pending = await asyncio.wait(
            [self.recv_task, self.send_task],
            return_when = asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()

        for task in [self.recv_task, self.send_task]:
            try:
                exc = task.exception()

            except (asyncio.CancelledError, asyncio.exceptions.InvalidStateError):
                pass # We did this. Don't worry about it.  

            else:
                if exc is not None:
                    # Reraise
                    raise exc

    async def recv_(
            self
        ):

        async for message in self.socket:
            # Try to parse
            try:
                msg = json.loads(message)

            except Exception as e:
                logger.log("ws", "warn", f"Websocket returned unparseable message: '{str(e)}'")
                continue

            # Parse out action
            if not msg["success"]:
                # Just log it for now.
                logger.log("ws", "warn", f"Websocket returned error: '{msg.get('error')}'")
                continue

            # Get data
            if "data" not in msg:
                continue # Nothing to pass along.

            data = msg["data"]

            dtype = data["type"]

            if dtype == "action":
                # Run action call
                await humecord.bot.events.call(
                    "hc_on_ws_action",
                    [data["action"], data.get("data")]
                )

            elif dtype == "response":
                await humecord.bot.events.call(
                    "hc_on_ws_response",
                    [data.get("action"), data.get("data")]
                )

            else:
                logger.log("ws", "warn", f"Receieved message of unknown type '{dtype}' from websocket. Skipping.")

    async def send(
            self,
            action: str,
            data: dict
        ):

        await self.socket.send(
            json.dumps(
                {
                    "action": action,
                    "data": data
                }
            )
        )

    async def send_(
            self
        ):

        # Send authentication info
        await self.send(
            "auth",
            self.auth
        )
        logger.log_step("ws", "start", "Authenticated with the websocket.")

        # Just loop forever
        while True:
            await asyncio.sleep(100)