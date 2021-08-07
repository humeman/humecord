version = "0.3.1a"

import sys

# Base functions
from .funcs import *
from .classes.terminal import TerminalManager
from .classes.logger import Logger

init_finished = False
terminal = TerminalManager()

logger = Logger()

from .classes.bot import Bot

from .utils.exceptions import InitError

from . import classes
from . import utils
from . import interfaces
from . import loops
from . import commands

extra_events = []
bot = Bot()