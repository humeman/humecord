import humecord

from . import exceptions

import datetime
import time
import re
import pytz

from typing import Optional

specs = {
    "second": "%Y-%m-%d %H:%M-%S",
    "minute": "%Y-%m-%d %H:%M",
    "hour": "%Y-%m-%d %H",
    "day": "%Y-%m-%d",
    "week": "%Y-%U",
    "month": "%Y-%m",
    "year": "%Y"
}

aliases = {
    "second": ["secondly"],
    "minute": ["minutely"],
    "hour": ["hourly"],
    "day": ["daily"],
    "week": ["weekly"],
    "month": ["monthly"],
    "year": ["yearly"]
}

def get_datetime(
        specificity: str, 
        timedelta: Optional[dict] = None,
        format_override: str = None
    ):
    time_format = None

    if specificity in specs:
        time_format = specs[specificity]

    else:
        for change_to, names in aliases.items():
            if specificity in names:
                time_format = specs[change_to]

    if (not time_format) and format_override:
        time_format = format_override

    if not time_format:
        raise humecord.utils.exceptions.InvalidFormat(f"Specificity {specificity} does not exist")

    if timedelta is None:
        current = datetime.datetime.utcnow()

    else:
        current = datetime.datetime.utcnow() + datetime.timedelta(**timedelta)


    if hasattr(humecord, "bot"):
        return pytz.utc.localize(current).astimezone(humecord.bot.timezone).strftime(time_format)

    else:
        return datetime.datetime.now().strftime(time_format)

times = {
    "year": 31556952,
    "month": 2629800,
    "day": 86400,
    "hour": 3600,
    "minute": 60,
    "second": 0
}

friendly_names = {
    "year": "y",
    "month": "mo",
    "day": "d",
    "hour": "h",
    "minute": "m",
    "second": "s"
}
    
def get_duration(
        seconds: int,
        short: bool = True
    ):
    seconds = int(seconds)

    comp = {}

    while seconds > 0:
        for name, bound in times.items():
            if seconds >= bound:
                # Find number
                if name == "second":
                    comp[name] = seconds
                    seconds = 0

                else:
                    comp[name] = seconds // bound
                    seconds = seconds % bound

    if len(comp) == 0:
        comp["second"] = 0

    # Compile into string
    comp_str = []
    for name, value in comp.items():
        if value == 0 and (name != "second" and len(comp_str) > 0):
            print("skipping")
            continue

        if short:
            comp_str.append(f"{value}{friendly_names[name]}")

        else:
            comp_str.append(f"{value} {name}s")

    return ", ".join(comp_str)

def parse_duration(
        duration: str
    ):

    comp = {}

    for name, value in friendly_names.items():
        comp[name] = 0
        # Find every instance
        for value in re.findall(f"(\d+){name}", duration) + re.findall(f"(\d+){value}", duration):
            try:
                comp[name] += float(value)

            except:
                raise exceptions.InvalidDate(f"{value} is not a number")

    # Compile into seconds
    total = 0
    for unit, value in comp.items():
        if unit == "second":
            total += value

        else:
            total += times[unit] * value

    return total

def get_timestamp(seconds):
    if type(seconds) in [int, float]:
        dateobj = datetime.datetime.fromtimestamp(seconds)

    else:
        dateobj = seconds

    return f"{dateobj.strftime('%b %d, %Y at %H:%M %Z')}".strip()

int_times = [
    1,
    60,
    3600,
    86400,
    604800,
    2628000,
    31540000
]

def timestamp_to_seconds(
        timestamp: str
    ):
    seconds = timestamp.split(":")

    i = len(seconds) - 1
    total = 0
    for duration in seconds:
        duration = int(duration)

        total += duration * int_times[i]

        i -= 1

    return total