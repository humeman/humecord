version = "0.4.0a"

# Base functions
from .funcs import *
from .enums import *

# Check versions
verify_min_py_version(3, 11)
verify_min_dpy_version(2, 2)

# Loop setup and more crucial imports
import asyncio
loop = asyncio.new_event_loop()

from .classes.terminal import TerminalManager, ClassicTerminal
from .classes.logger import Logger

# General temporary global storage
_temp = {}

init_finished = False
try:
    with open(".classicterminal"):
        pass

    terminal = ClassicTerminal()

except:
    terminal = TerminalManager()

logger = Logger()

from .classes.bot import Bot

from .utils.exceptions import InitError

from . import classes

# Shorthand command reference
Command = classes.commandhandler.HumecordCommand

from . import utils
from . import interfaces
from . import loops
#from . import msg_commands

extra_events = []
reg_permas = []
bot = Bot()