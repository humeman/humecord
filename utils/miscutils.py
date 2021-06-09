import math
from re import search
import time
import datetime
import random

from . import exceptions

def get_duration(seconds):
    seconds = math.trunc(seconds)

    if seconds < 60:
        return time.strftime("%Ss", time.gmtime(seconds))

    elif seconds < 3600: # 1 hour
        if seconds % 60 > 0:
            return time.strftime("%Mm, %Ss", time.gmtime(seconds))

        return time.strftime("%Mm", time.gmtime(seconds))
    
    else:
        return time.strftime("%Hh, %Mm, %Ss", time.gmtime(seconds))

def get_datetime(seconds):
    return f"{datetime.datetime.fromtimestamp(seconds).strftime('%b %d, %Y at %H:%M %Z')}"

def expand_placeholders(
        message: str,
        placeholders: dict
    ):

    for placeholder, value in placeholders.items():
        message = message.replace(f"%{placeholder}%", str(value))

    return message

def generate_hexid(
        length: int = 10
    ):

    chars = "1234567890abcdef"
    comp = ""

    for i in range(length):
        comp += random.choice(chars)

    return comp

def follow(
        search_in: dict,
        path: list
    ):

    current = search_in

    for name in path:
        if name not in current:
            raise exceptions.NotFound(f"Path {'.'.join(path)} doesn't exist ({name})")

        current = current[name]

    return current