version = "0.0.1"
bot = None

from . import classes
from . import utils
from . import interfaces
from . import loops
from . import commands
from . import bootstrap

from .bot_init import init
from . import data

data.init()