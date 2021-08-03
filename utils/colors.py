from . import exceptions

import humecord

col = {
    "soft_pink": 0xf2d7d5,
    "hot_pink": 0xec407a,
    "dark_red": 0x7b241c,
    "red": 0xb71c1c,
    "light_red": 0xcd6155,
    "dark_orange": 0xe65100,
    "orange": 0xffa726,
    "light_orange": 0xffe0b2,
    "dark_yellow": 0x827717,
    "yellow": 0xffeb3b,
    "light_yellow": 0xfff59d,
    "dark_green": 0x1b5e20,
    "green": 0x43a047,
    "light_green": 0xace36d,
    "dark_blue": 0x1a237e,
    "blue": 0x1565c0,
    "light_blue": 0x80deea,
    "turquoise": 0x006064,
    "aqua": 0x00CDD6,
    "magenta": 0x880e4f,
    "indigo": 0x4a148c,
    "purple": 0x311b92,
    "dark_brown": 0x3e2723,
    "brown": 0x795548,
    "light_brown": 0xbcaaa4,
    "black": 0x000000,
    "dark_gray": 0x212121,
    "gray": 0x757575,
    "light_gray": 0xe0e0e0,
    "white": 0xffffff,
    "invisible": 0x2f3136,
    "shit": 0x3e2724,
    "error": 0xff4141,
    "success": 0x009300,
    "warning": 0xFFBB00,
    "icon_gray": 0x959595,
    "icon_blue": 0x1565c0
}

termcolors = {
    "default": "\033[37m",
    "bold": "\033[1m",
    "reset": "\033[0m",

    "red": "\033[31m",
    "light_red": "\033[91m",

    "green": "\033[32m",
    "light_green": "\033[92m",

    "yellow": "\033[33m",
    "light_yellow": "\033[93m",

    "blue": "\033[34m",
    "light_blue": "\033[94m",

    "magenta": "\033[35m",
    "light_magenta": "\033[95m",

    "cyan": "\033[36m",
    "light_cyan": "\033[96m",

    "light_gray": "\033[37m",
    "dark_gray": "\033[90m"
}

class Colors:
    def get_color(
            color: str
        ):
        if color.startswith("#"):
            color = color.replace("#", "")

            try:
                hex_val = int(color, base = 16)

            except:
                raise exceptions.InvalidColorException(f"Invalid hex code `{color}`")
            
            if hex_val > 0xFFFFFF or hex_val < 0x000000:
                raise exceptions.InvalidColorException(f"Invalid hex code '{hex_val}'")
            
            return hex_val

        if color.lower() in col:
            return col[color.lower()]

        raise exceptions.InvalidColorException(f"Color '{color}' not found")

    def get_color_string(
            color
        ):
        for key, value in col.items():
            if value == color:
                return key

        new = str(hex(color)).replace("0x", "#")

        if len(new) == 6:
            new = "#0" + new.replace("#", "")
        
        return new

class TermColors:
    def get_color(
            name: str
        ):
        if name in termcolors:
            return termcolors[name]
        
        raise exceptions.InvalidColorException("Color not found")