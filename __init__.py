version = "0.1.1"

# Base functions
from .funcs import *

from .classes.bot import Bot

bot = Bot()

from . import classes
from . import utils
from . import interfaces
from . import loops
from . import commands