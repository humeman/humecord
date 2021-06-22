import time

import humecord

from humecord.utils import (
    dateutils
)

def get_loop_runtime(loop):
    if loop.type == "delay":
        return f"Every {dateutils.get_duration(loop.delay)}"

    elif loop.type == "period":
        return f"Every {loop.time}"

def get_loop_last_run(loop):
    if loop.type == "delay":
        if loop.last_run == -1:
            return "Never"

        return dateutils.get_duration(time.time() - loop.last_run) + " ago"

    elif loop.type == "period":
        return humecord.bot.files.files["__loops__.json"][loop.name]["last_run"]