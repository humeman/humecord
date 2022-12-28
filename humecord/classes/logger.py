from humecord.utils import (
    colors,
    exceptions,
    miscutils,
    dateutils
)
import humecord

import math
import time
from typing import Optional, Union

class Logger:
    def __init__(
            self
        ):

        self.log_types = {
            "warn": "yellow",
            "error": "red",
            "success": "green",
            "start": "cyan",
            "stop": "cyan",
            "close": "cyan",
            "cmd": "blue",
            "int": "blue",
            "info": "default",
            "obj": "magenta",
            "ask": "magenta"
        }

        self.colors = colors.termcolors

        self.ready = False

        self.timer = time.time()

        self.logging = {
            "request": False,
            "requestcontent": False,
            "loops": False,
            "start": True,
            "botinit": True,
            "stop": True,
            "shutdown": True,
            "unhandlederror": True,
            "cacheinfo": True,
            "command": True,
            "commandinfo": True,
            "config": True,
            "dev": True,
            "erroredrequest": True,
            "interaction": True,
            "events": True,
            "loader": True,
            "reply": True,
            "ws": True,
            "api": True,
            "subprocess": True,
            "user": True,
            "ask": True,
            "deprecation": True
        }

        self.format = {
            "log": "%color%%reverseopt%%bold%%timep% %typep% %reset%%color%%reverseopt%%boldopt%%message%%reset%",
            "step": "                            %color%%reverseopt%%bold%→ %reset%%color%%reverseopt%%boldopt%%message%%reset%",
            "long": "                            %color%%reverseopt%%bold%→ %reset%%color%%reverseopt%%boldopt%%message%%reset%",
            "raw": "%color%%reverseopt%%boldopt%%message%%reset%",
            "ask": "%color%%reverseopt%%bold%%timep% %typep% %reset%%color%%reverseopt%%boldopt%%message% %reset%%color%[%hint%]%reset%",
        }

        self.format_type = {}

    def prep(
            self
        ):

        global bot
        from humecord import bot

        for name, value in bot.config.log_colors.items():
            if name not in self.log_types:
                raise exceptions.InitError(f"Log type {name} doesn't exist")

            if not value.startswith("&"):
                if value not in self.colors:
                    raise exceptions.InitError(f"Terminal color {value} doesn't exist")

            self.log_types[name] = value

        for name, value in bot.config.log_formats.items():
            if name not in self.format:
                raise exceptions.InitError(f"Log format type {name} doesn't exist")

            self.format[name] = value

        for name, value in bot.config.logging.items():
            if name not in self.logging:
                raise exceptions.InitError(f"Log category {name} doesn't exist")

            self.logging[name] = value

        #for name, value in bot.config.format_type.items():
        #    if name not in self.log_types:
        #        raise exceptions.InitError(f"Log type {name} doesn't exist")

        #    self.format_type[name] = value

        #self.timer = bot.timer

        self.ready = True

    def get_placeholders(
            self,
            category,
            log_type,
            message,
            bold,
            color,
            reversed
        ):

        current_time = time.time() - self.timer
        time_str = str(round(current_time, 3))
        time_f = dateutils.get_duration(time_str.split(".", 1)[0])
        
        return {
            "color": color,
            "bold": self.colors["bold"],
            "reset": self.colors["reset"],
            "underline": self.colors["underline"],
            "reversed": self.colors["reversed"],
            "reverseopt": self.colors["reversed"] if reversed else "",
            "boldopt": self.colors["bold"] if bold else "",
            "time": time_str,
            "timep": miscutils.pad_to(f"[{time_str}]", 14),
            "timef": time_f,
            "timepf": miscutils.pad_to(time_f, 16),
            "typep": miscutils.pad_to(f"[{log_type.upper()}]", 10),
            "logtype": log_type.upper(),
            "logtypel": log_type,
            "message": message,
            "category": category
        }

    def log(
            self,
            *args,
            **kwargs
        ):

        self.log_type(
            "log",
            *args,
            **kwargs
        )

    def log_step(
            self,
            *args,
            **kwargs
        ):

        self.log_type(
            "step",
            *args,
            **kwargs
        )

    def log_long(
            self,
            category: str,
            log_type: str,
            messages: Union[list, str],
            bold: bool = False,
            reversed: bool = False,
            color: Optional[str] = None,
            remove_blank_lines: bool = False,
            extra_line: bool = False
        ):

        if type(messages) == str:
            messages = messages.split("\n")

        for line in messages:
            if line.strip() == "":
                continue

            self.log_type(
                "long",
                category,
                log_type,
                line,
                bold,
                reversed,
                color
            )

        if extra_line:
            humecord.terminal.log(" ", True)

    def log_raw(
            self,
            *args,
            **kwargs
        ):

        self.log_type(
            "raw",
            *args,
            **kwargs
        )
    
    def log_ask(
            self,
            message: str,
            hint: str
        ):

        self.log_type(
            "ask",
            "ask",
            "ask",
            message,
            bold = True,
            placeholder_ext = {
                "hint": hint
            }
        )

    def log_type(
            self,
            name: str,
            category: str,
            log_type: str,
            message: str,
            bold: bool = False,
            reversed: bool = False,
            color: Optional[str] = None,
            placeholder_ext: dict = {}
        ):

        # Make sure we should log this
        log = True
        if "bot" in globals():
            if hasattr(bot, "config"):
                if f"log_{category}" not in bot.config.logging:
                    log = self.logging[category]

                else:
                    log = bot.config.logging[f"log_{category}"]

        if not log:
            return

        # Verify log type exists
        if log_type not in self.log_types:
            raise exceptions.DevError(f"Log type {log_type} doesn't exist")

        # Get the color
        if color is None:
            color = self.log_types[log_type]

            if color.startswith("&"):
                color = f"\033[38;5;{color[1:]}m"

        if not color.startswith("\033"):
            color = self.colors[color]

        placeholders = {
            **self.get_placeholders(
                category,
                log_type,
                message,
                bold,
                color,
                reversed
            ),
            **placeholder_ext
        }

        msg = str(self.format[name])

        for placeholder, value in placeholders.items():
            msg = msg.replace(f"%{placeholder}%", str(value))

        humecord.terminal.log(
            msg,
            True
        )