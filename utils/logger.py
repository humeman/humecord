from .colors import TermColors
from . import exceptions
import textwrap
import time

import humecord

adapters = {
    "warn": "yellow",
    "error": "red",
    "success": "green",
    "start": "cyan",
    "stop": "cyan",
    "close": "cyan",
    "cmd": "blue",
    "int": "blue",
    "info": "default",
    "obj": "magenta"
}

def log(
        log_type: str = "",
        message: str = "",
        bold: bool = False,
        color: str = "default",
        condition: bool = True
    ):
    if not condition:
        return

    color = color.lower()

    if color == "default":
        if log_type in adapters:
            color = adapters[log_type]

    try:
        col = TermColors.get_color(color)

        if color in ["bold", "reset"]:
            raise exceptions.InvalidColorException(f"Color cannot be bold or reset.")

    except:
        raise exceptions.InvalidColorException(f"Invalid color {color}.")

    if hasattr(humecord.bot, "timer"):
        timer = humecord.bot.timer

    else:
        timer = time.time()

    timelen = 16
    typelen = 8

    timestr = f"[{round(time.time() - timer, 3)}]"
    typestr = f"[{log_type.upper()}]"

    timestr += " " * (timelen - len(timestr))
    typestr += " " * (typelen - len(typestr))

    bold_str = TermColors.get_color("bold") if bold else ""

    print(f"{col}{TermColors.get_color('bold')}{timestr}{typestr}\t{TermColors.get_color('reset')}{col}{bold_str}{message}{TermColors.get_color('reset')}")

def ask(
        message: str,
        args: str,
        color: str
    ):
    color = color.lower()
    
    try:
        col = TermColors.get_color(color)

        if color in ["bold", "reset"]:
            raise exceptions.InvalidColorException(f"Color cannot be bold or reset.")

    except:
        raise exceptions.InvalidColorException(f"Invalid color {color}.")

    if hasattr(humecord.bot, "timer"):
        timer = humecord.bot.timer

    else:
        timer = time.time()

    timelen = 16
    typelen = 8

    timestr = f"[{round(time.time() - timer, 3)}]"
    typestr = f"[ASK]"

    timestr += " " * (timelen - len(timestr))
    typestr += " " * (typelen - len(typestr))

    return input(f"{col}{TermColors.get_color('bold')}{timestr}{typestr}\t{TermColors.get_color('reset')}{col}{TermColors.get_color('bold')}{message}{TermColors.get_color('reset')} {col}[{args}]{TermColors.get_color('reset')} ")

def log_step(
        content: str,
        color: str = "default",
        bold: bool = False
    ):
    
    color = TermColors.get_color(color)
    bold_col = TermColors.get_color("bold")
    reset = TermColors.get_color("reset")

    for line in [content[i:i+150] for i in range(0, len(content), 150)]:
        print(f"                                {color}{bold_col}→ {reset}{color}{bold_col if bold else ''}{line}{reset}")


def log_long(
        content: str,
        color: str,
        remove_blank_lines: bool = False,
        extra_line: bool = True
    ):
    color = TermColors.get_color(color)
    bold = TermColors.get_color("bold")
    reset = TermColors.get_color("reset")

    for line in textwrap.dedent(content).split("\n"):
        if line.strip() == "" and remove_blank_lines:
            continue
        
        print(f"                                {color}{bold}→ {reset}{color}{line}{reset}")

    if extra_line:
        print()