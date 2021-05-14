"""
HumeCord/classes/bot.py

The main Bot object.
"""

import os
import sys
import discord
import time

from .config import Config
from .events import Events

from .. import data

from humecord.utils import logger
from humecord.utils import fs
from humecord.utils import debug

class Bot:
    def __init__(
            self,
            imports
        ):

        logger.log("start", "Initializing bot instance...", bold = True)

        # -- CONFIG --
        # Load the config
        self.load_config()

        # Load globals
        self.config.load_globals()

        logger.log_step("Loaded config", "cyan")

        # -- MEM STORAGE --
        self.mem_storage = dict(self.config.mem_storage)

        # -- STARTUP VARS --
        self.started = False
        self.timer = time.time()
        self.client = discord.Client()

        logger.log_step("Initialized storage", "cyan")

        # -- HANDLERS --

        self.imports = imports

        # if self.config.use_api:
        #   self.api = API()
        # self.commands = Commands()
        # self.loops = Loops()
        self.events = Events(self)
        # self.overrides = Overrides()
        # self.console = Console()
        # self.dconsole = DConsole()

        logger.log_step("Initialized handlers", "cyan")

        data.bot_init = True
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
            sys.exit(-1)

        for key, value in self.config.config_raw.items():
            setattr(self.config, key, value)

    def start(
            self
        ):
        try:
            logger.log_step("Starting client...", "cyan")

            self.client.loop.run_until_complete(self.client.start(self.config.token))

        except KeyboardInterrupt:
            print()
            logger.log("close", "Shutting down...", bold = True)

            logger.log_step("Closing websocket", "cyan")

            logger.log_step("Logging out of API", "cyan")
            
            logger.log_step("Changing presence to offline", "cyan")
            self.client.loop.run_until_complete(self.client.change_presence(status = discord.Status.offline))
            
            logger.log_step("Logging out", "cyan")
            self.client.loop.run_until_complete(self.client.close())

            logger.log_step("Bye bye!", "cyan", bold = True)
            sys.exit(0)