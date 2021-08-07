import math
import time
import datetime
import random

from typing import Union

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

def follow_path(
        current: dict,
        path: str
    ):

    path = path.strip("/").split("/")

    for name in path:
        cd_to = None
        if ":" in name:
            name, cd_to = name.split(":", 1)

            cd_to = int(cd_to)

        if name not in current:
            raise exceptions.NotFound(f"Path {'/'.join(path)} doesn't exist ({name})")

        current = current[name]

        if cd_to is not None:
            current = current[cd_to]

    return current

sizes = {
    "byte": "B",
    "kilobyte": "KB",
    "megabyte": "MB",
    "gigabyte": "GB",
    "terabyte": "TB",
    "petabyte": "PB"
}

def get_size(
        size: int,
        round_: bool = False,
        short: bool = True
    ):

    comp = []
    
    while size > 0:
        for i, name in reversed(list(enumerate(sizes))):
            unit = 1024 ** i
            if unit > size:
                # Unit is too large
                continue

            # Find remainder
            if i == 0: # bytes (can't divide by 0)
                count = size
                size = 0

            else:
                count = size // unit
                size = size % unit

            if round_:
                return f"{count}.{str(round((size / unit) * 100, 1))[:2].strip('.')} {sizes[name] if short else name}"

            else:
                comp.append(f"{count}{sizes[name] if short else f' {name}'}")

    return ", ".join(comp)

def friendly_number(
        number: Union[int, float],
        trunc: bool = False
    ):

    if number is None:
        return "0"

    if trunc:
        number = int(number)

    
    value = "{:,.2f}".format(number)

    if value.strip("0").endswith("."):
        value = value.split(".")[0]

    return value

def pad_to(
        value: str,
        length: int,
        trunc: bool = True
    ):

    if trunc:
        value = value[:length]

    return value + (" " * (length - len(value)))