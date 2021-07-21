"""
HumeCord/utils/debug

Lots of debugging and logging utils.
"""

import traceback

import humecord
from humecord.utils import discordutils

from . import logger
from .colors import TermColors

def print_traceback(
        error_message: str = "An error occured!"
    ):
    """
    Prints a formatted stack trace for the active exception.
    """

    try:
        tb = traceback.format_exc()

    except:
        logger.log("warn", "Tried to print stack trace but there is no active exception.")
        return

    logger.log("error", error_message, bold = True)

    logger.log_long(tb, "red", True)
    
    print()

def print_object(obj):
    """
    Prints out an expanded representation of an object.
    """

    logger.log("obj", f"Object {type(obj)} at {hex(id(obj))}:", bold = True)

    comp = []
    keys = dir(obj)

    bold = TermColors.get_color('bold')
    reset = TermColors.get_color('reset')
    magenta = TermColors.get_color('magenta')

    for key in keys:
        if not key.startswith("__"):
            comp.append(f"{key} {bold}= {reset}{magenta}{getattr(obj, key)}")

    logger.log_long("\n".join(comp), "light_magenta")

async def log_traceback(
        context: str
    ):

    await humecord.bot.debug_channel.send(
        embed = discordutils.create_embed(
            title = f"{humecord.bot.config.lang['emoji']['error']}  An exception was caught during: {context}",
            description = f"```py\n{traceback.format_exc()[:4080]}```",
            field = [
                {
                    "name": "%-a% Context",
                    "value": context
                }
            ],
            color = "error"
        )
    )