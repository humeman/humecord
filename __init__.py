version = "0.1.1"

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

try:
    bot = Bot()


except InitError as e:
    # Forward it off to the logger
    if e.traceback:
        utils.debug.print_traceback(
            f"An initialization error occurred!"
        )
        print()
        utils.logger.log_step(e.message, 'red', bold = True)

    else:
        utils.logger.log("error", e.message, bold = True)

    sys.exit(1)

except:
    utils.debug.print_traceback(
        f"An unexpected initialization error occurred!"
    )
    sys.exit(1)
    