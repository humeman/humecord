"""
Humecord/classes/bot.py

The main Bot object.
"""

import sys
import discord
import time
import pytz
import os
import inspect
import asyncio
import traceback
#import nest_asyncio

#nest_asyncio.apply()

from contextlib import suppress
from typing import Optional

import humecord

from .loader import Loader
from .config import Config
from .events import Events
from .commands import Commands
from .loops import Loops
from .debugconsole import DebugConsole
from .interactions import Interactions
from .permissions import Permissions
from .overrides import OverrideHandler
from .replies import Replies
from .argparser import ArgumentParser
from .messages import Messenger
from .console import Console


from ..interfaces.apiinterface import APIInterface
from ..interfaces.fileinterface import FileInterface
from ..interfaces.wsinterface import WSInterface

from humecord.utils import (
    logger,
    fs,
    debug,
    discordutils,
    miscutils,
    subprocess,
    exceptions,
    errorhandler,
    dateutils
)

class Bot:
    def __init__(
            self
        ):
        pass

    def init(
            self,
            imports_imp,
            imports_class
        ):
        self.imports_imp = imports_imp
        self.imports_class = imports_class

        self.loop = asyncio.get_event_loop()

        self.error_state = False
        self.disabled = False

        return

        raise DeprecationWarning("This function is deprecated. Pass all init parameters to Bot() instead.")

        self.loop.run_until_complete(
            errorhandler.async_wrap(
                self._init(*args, **kwargs)
            )
        )

    async def _init(
            self,
            imports_imp,
            imports_class
        ):

        self.console = Console()

        # Create a loader
        self.loader = Loader(
            imports_imp,
            imports_class
        )

        # Tell the loader to only do config things :)
        await self.loader.load_config()

        # Load up bot names
        self.names = [self.config.name, self.config.cool_name.lower()] + self.config.name_aliases

        # Log things
        placeholders = {
            "bot": self.config.cool_name,
            "version": self.config.version,
            "humecord": humecord.version
        }

        for command in self.config.start_calls:
            if command.startswith("eval:::"):
                eval(
                    miscutils.expand_placeholders(
                        command.split(":::", 1)[1],
                        placeholders
                    ),
                    globals()
                )
            
            elif command.startswith("exec:::"):
                exec(
                    miscutils.expand_placeholders(
                        command.split(":::", 1)[1],
                        placeholders
                    ),
                    globals()
                )


            else:
                await subprocess.run(
                    miscutils.expand_placeholders(
                        command,
                        placeholders
                    )
                )

        logger.log("start", "Initializing bot instance...", bold = True)
        logger.log_step("Loaded config", "cyan")

        # Read persistent storage

        # -- MEM STORAGE --
        self.mem_storage = {
            "reply": None,
            "error_ratelimit": {},
            **dict(self.config.mem_storage)
        }

        # -- STARTUP VARS --
        self.started = False
        self.timer = time.time()
        self.client = discord.Client(
            intents = discordutils.generate_intents(self.config.intents)
        )

        @self.client.event
        async def on_error(*args, **kwargs):
            await errorhandler.async_wrap(
                on_error_ext()
            )

        self.timezone = pytz.timezone(self.config.timezone)

        logger.log_step("Initialized storage", "cyan")

        # -- HANDLERS --

        if self.config.use_api:
            self.api = APIInterface()
            self.overrides = OverrideHandler(self)
        
        if self.config.use_ws:
            self.ws = WSInterface()
            
        self.commands = Commands({})
        self.loops = Loops()
        self.events = Events(self)
        self.replies = Replies()
        self.interactions = Interactions()
        self.files = FileInterface(self)
        # self.overrides = Overrides()
        # self.console = Console()
        self.debug_console = DebugConsole()
        self.permissions = Permissions(self)
        self.args = ArgumentParser({})
        self.messages = Messenger(self)

        logger.log_step("Initialized handlers", "cyan")

        humecord.init_finished = True
        humecord.terminal.finish_start()

        logger.log_step("Initialized successfully!", "cyan", bold = True)

    def load_config(
            self
        ):
        self.config = Config()

        try:
            self.config.config_raw = fs.read_yaml("config.yml")

        except:
            debug.print_traceback()
            logger.log("error", "Failed to read config file.")

            humecord.terminal.log(" ", True)

            choice = logger.ask("Would you like to automatically generate a new config file?", "Y/n", "cyan")

            if choice.lower().strip() in ["yes", "y", ""]:
                # Read config default
                with open(f"{os.path.dirname(inspect.getfile(humecord))}/config.default.yml", "r") as f:
                    config_sample = f.read().split("\n")

                # Write to base dir
                with open("config.yml", "w+") as f:
                    f.write("\n".join(config_sample))

                logger.log("info", f"Wrote default config file to 'config.yml'.", color = "cyan", bold = True)
                logger.log_step("Edit the file as needed, then start Humecord again to get going!", color = "cyan")

            else:
                logger.log("info", "Not creating config file.", color = "cyan")

            sys.exit(-1)

        for key, value in self.config.config_raw.items():
            setattr(self.config, key, value)

    async def populate_imports(
            self
        ):

        # Now we just tell the loader to do it
        await self.loader.load(
            starting = True,
            safe_stop = False
        ) # Not a safe stop - don't stop anything

        """
        self.imports = self.imports_class()
        
        self.loops.loops = self.imports.loops
        await self.loops.prep()

        self.commands.commands = self.imports.commands
        self.commands.register_internal()

        await self.events.prep()
        """


        humecord.terminal.log(" ", True)

    def start(
            self
        ):

        try:
            self.loop.run_until_complete(
                errorhandler.async_wrap(
                    self._start()
                )
            )

            self.loop.run_forever()

        except KeyboardInterrupt:
            # This is from an error state.
            try:
                if self.error_state:
                    self.loop.run_until_complete(self.perform_logout("Keyboard interrupt (from error state)", error_state = False, skip_shutdown = True))

                else:
                    humecord.terminal.reprint(log_logs = True)
                    try:
                        self.loop.run_until_complete(self.shutdown(f"Keyboard interrupt", safe = True))

                    except KeyboardInterrupt:
                        self.loop.run_until_complete(self.shutdown(f"Immediate shutdown", safe = False))


            except exceptions.CloseLoop:
                pass

        except exceptions.CloseLoop:
            pass
            
        self.cleanup()

    def cleanup(
            self
        ):

        # End async loop
        self.loop.stop()

        #for task in asyncio.all_tasks():
        #    task.cancel()
#
        #    asyncio.get_event_loop().run_until_complete(task)

        self.loop.close()

    async def _start(
            self
        ):
        await self._init(self.imports_imp, self.imports_class)

        if not self.disabled:
            logger.log_step("Starting client...", "cyan")

            await self.client.start(self.config.token)

    async def shutdown_(
            self,
            *args,
            **kwargs
        ):

        await asyncio.shield(
            self.shutdown_(
                *args, 
                **kwargs
            )
        )

    async def shutdown(
            self,
            reason: str,
            safe: bool = True,
            error_state: bool = False,
            skip_shutdown: bool = False
        ):
        if self.disabled:
            return

        self.disabled = True

        # Log out
        if safe or skip_shutdown:
            await self.perform_logout(reason, error_state, skip_shutdown = skip_shutdown)

        else:
            raise exceptions.CloseLoop()

            self.console.shutdown = True
            humecord.terminal.close()

            # Terminate the asyncio loop so we can exit
            self.loop.stop()

            for task in asyncio.Task.all_tasks():
                task.cancel()

            self.loop.close()

    async def perform_logout(
            self,
            reason: str,
            error_state: bool = False,
            skip_shutdown: bool = False
        ):

        if not skip_shutdown:
            humecord.terminal.log(" ", True)
            if not error_state:
                logger.log("close", "Shutting down...", bold = True)

            if hasattr(self, "debug_channel"):
                await self.debug_channel.send(
                    embed = discordutils.create_embed(
                        title = f"{self.config.lang['emoji']['success']}  Shutting down client.",
                        description = f"```yml\nCaused by: {reason}\n\nRuntime: {miscutils.get_duration(time.time() - self.timer)}\nSession started: {dateutils.get_timestamp(self.timer)}\nSession closed: {dateutils.get_timestamp(time.time())}\n\nBye bye!```",
                        color = "success"
                    )
                )
            
            if hasattr(self, "loops"):
                logger.log_step("Shutting down loops", "cyan")
                self.loops.close()

            if hasattr(self, "api"):
                logger.log_step("Logging out of API", "cyan")
                try:
                    await humecord.loops.post_stats.PostStatsLoop.run(None)

                except:
                    debug.print_traceback()

                try:
                    await self.api.put(
                        "status",
                        "bot",
                        {
                            "bot": self.config.self_api,
                            "shutdown": True,
                            "details": {}
                        }
                    )

                except:
                    debug.print_traceback()

                await self.api.direct.client.aclose()

            if hasattr(self, "ws"):
                logger.log_step("Closing websocket", 'cyan')
                await self.ws.close()
            
            if hasattr(self, "client"):
                if self.client.is_ready():
                    logger.log_step("Changing presence to offline", "cyan")
                    try:
                        await self.client.change_presence(status = discord.Status.offline)

                    except:
                        pass
                    
                    logger.log_step("Logging out", "cyan")
                    await self.client.close()

                logger.log_step("Bye bye!", "cyan", bold = True)

        if error_state:
            logger.log(f"error", "Humecord has entered into an error state. Check the logs above, then run Ctrl + C again to exit.", True)
            if hasattr(self, "console"):
                self.console.error_state = True

            self.error_state = True

        else:
            self.console.shutdown = True
            humecord.terminal.close()

            raise exceptions.CloseLoop()

async def on_error_ext(*args, **kwargs):
    raise

def catch_asyncio(loop, context):
    if "exception" not in context:
        logger.log(
            "warn",
            "An asyncio exception was thrown, but no exception was passed.",
            bold = True
        )
        return
    
    if type(context["exception"]) in [SystemExit, KeyboardInterrupt]:
        return

    elif type(context["exception"]) in [exceptions.CloseLoop]:
        humecord.bot.loop.stop()
        return

    # Just log it
    logger.log(
        "warn",
        "An asyncio exception wasn't handled!",
        bold = True
    )

    logger.log_long(
        "\n".join(traceback.format_tb(tb = context["exception"].__traceback__) + [f"{type(context['exception']).__name__}: {str(context['exception'])}"]).strip(),
        "yellow"
    )

asyncio.get_event_loop().set_exception_handler(catch_asyncio)