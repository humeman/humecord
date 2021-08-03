version = "0.3.0"

import sys

# Base functions
from .funcs import *
from .classes.terminal import TerminalManager

init_finished = False
terminal = TerminalManager()

from .classes.bot import Bot

from .utils.exceptions import InitError

from . import classes
from . import utils
from . import interfaces
from . import loops
from . import commands

extra_events = []
bot = Bot()