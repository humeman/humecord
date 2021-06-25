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

import humecord

from .config import Config
from .events import Events
from .commands import Commands
from .loops import Loops
from .debugconsole import DebugConsole
from .interactions import Interactions
from .permissions import Permissions
from .overrides import OverrideHandler

from ..interfaces.apiinterface import APIInterface
from ..interfaces.fileinterface import FileInterface

from humecord.utils import logger
from humecord.utils import fs
from humecord.utils import debug
from humecord.utils import discordutils
from humecord.utils import miscutils
from humecord.utils import errorhandler
from humecord.utils import subprocess

class Bot:
    def __init__(
            self
        ):
        pass

    def init(
            self,
            imports_class
        ):

        self.imports_class = imports_class

        # -- CONFIG --
        # Load the config
        self.load_config()

        # Load globals
        self.config.load_globals()

        # Load lang
        self.config.load_lang()

        # Validate
        self.config.validate()

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
        intents = discord.Intents().all()
        self.client = discord.Client(intents = intents)
        self.timezone = pytz.timezone(self.config.timezone)

        logger.log_step("Initialized storage", "cyan")

        # -- HANDLERS --

        if self.config.use_api:
            self.api = APIInterface()
            self.overrides = OverrideHandler(self)
            
        self.commands = Commands({})
        self.loops = Loops()
        self.events = Events(self)
        self.interactions = Interactions()
        self.files = FileInterface(self)
        # self.overrides = Overrides()
        # self.console = Console()
        self.debug_console = DebugConsole()
        self.permissions = Permissions(self)

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
        self.imports = self.imports_class()
        
        self.loops.loops = self.imports.loops
        await self.loops.prep()

        self.commands.commands = self.imports.commands
        self.commands.register_internal()

        await self.events.prep()


        print()

    def start(
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
                        description = f"```yml\nRuntime: {miscutils.get_duration(time.time() - self.timer)}\nSession started: {miscutils.get_datetime(self.timer)}\nSession closed: {miscutils.get_datetime(time.time())}\n\nBye bye!```",
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