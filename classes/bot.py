"""
HumeCord/classes/bot.py

The main Bot object.
"""

import sys
import discord
import time
import pytz
import os
import inspect
import asyncio

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

from ..interfaces.apiinterface import APIInterface
from ..interfaces.fileinterface import FileInterface

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
            *args,
            **kwargs
        ):
        errorhandler.base_wrap(
            self._init,
            args,
            kwargs
        )

    def _init(
            self,
            imports_imp,
            imports_class
        ):

        # Create a loader
        self.loader = Loader(
            imports_imp,
            imports_class
        )

        # Tell the loader to only do config things :)
        asyncio.get_event_loop().run_until_complete(self.loader.load_config())

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
                subprocess.sync_run(
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
            errorhandler.base_wrap(
                on_error_ext,
                args,
                kwargs
            )

        self.timezone = pytz.timezone(self.config.timezone)

        logger.log_step("Initialized storage", "cyan")

        # -- HANDLERS --

        if self.config.use_api:
            self.api = APIInterface()
            self.overrides = OverrideHandler(self)
            
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

        logger.log_step("Initialized handlers", "cyan")
        
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

            print()

            choice = logger.ask("Would you like to automatically generate a new config file?", "Y/n", "cyan")

            if choice.lower().strip() in ["yes", "y", ""]:
                # Read config default
                with open(f"{os.path.dirname(inspect.getfile(humecord))}/config.default.yml", "r") as f:
                    config_sample = f.read().split("\n")

                # Write to base dir
                with open("config.yml", "w+") as f:
                    f.write("\n".join(config_sample))

                logger.log("info", f"Wrote default config file to 'config.yml'.", color = "cyan", bold = True)
                logger.log_step("Edit the file as needed, then start HumeCord again to get going!", color = "cyan")

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


        print()

    def start(
            self
        ):

        errorhandler.base_wrap(
            self._start
        )

    def _start(
            self
        ):
        try:
            logger.log_step("Starting client...", "cyan")

            self.client.loop.run_until_complete(self.client.start(self.config.token))

        except KeyboardInterrupt:
            print()
            logger.log("close", "Shutting down...", bold = True)

            self.client.loop.run_until_complete(
                self.debug_channel.send(
                    embed = discordutils.create_embed(
                        title = f"{self.config.lang['emoji']['success']}  Shutting down client.",
                        description = f"```yml\nRuntime: {miscutils.get_duration(time.time() - self.timer)}\nSession started: {dateutils.get_timestamp(self.timer)}\nSession closed: {dateutils.get_timestamp(time.time())}\n\nBye bye!```",
                        color = "success"
                    )
                )
            )

            logger.log_step("Closing websocket", "cyan")

            logger.log_step("Logging out of API", "cyan")
            
            logger.log_step("Changing presence to offline", "cyan")
            self.client.loop.run_until_complete(self.client.change_presence(status = discord.Status.offline))
            
            logger.log_step("Logging out", "cyan")
            self.client.loop.run_until_complete(self.client.close())

            logger.log_step("Bye bye!", "cyan", bold = True)
            sys.exit(0)

def on_error_ext(*args, **kwargs):
    raise

def catch_asyncio(loop, context):
    if "exception" in context:
        if type(context["exception"]) in [SystemExit, KeyboardInterrupt]:
            raise context["exception"] # Reraise

    # Just log it
    logger.log(
        "warn",
        "An asyncio exception wasn't handled!",
        bold = True
    )
    logger.log_step(
        str(context.get("exception")),
        "yellow"
    )

asyncio.get_event_loop().set_exception_handler(catch_asyncio)