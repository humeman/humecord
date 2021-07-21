version = "0.2.1"

import sys

# Base functions
from .funcs import *

from .classes.bot import Bot

from .utils.exceptions import InitError

from . import classes
from . import utils
from . import interfaces
from . import loops
from . import commands

extra_events = []
bot = Bot()