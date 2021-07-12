version = "0.1.2"

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

bot = Bot()