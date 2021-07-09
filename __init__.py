version = "0.1.1"

import sys

# Base functions
from .funcs import *

from .classes.bot import Bot

from .utils.exceptions import InitError
from .utils import debug

try:
    bot = Bot()

    from . import classes
    from . import utils
    from . import interfaces
    from . import loops
    from . import commands

except InitError:
    # Forward it off to the logger
    debug.print_traceback(
        f"An initialization error occurred!"
    )
    sys.exit(1)

except:
    debug.print_traceback(
        f"An unexpected initialization error occurred!"
    )
    sys.exit(1)
    