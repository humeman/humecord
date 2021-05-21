import humecord

import datetime
import time
import pytz

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


def get_datetime(specificity):
    time_format = None

    if specificity in specs:
        time_format = specs[specificity]

    else:
        for change_to, names in aliases.items():
            if specificity in names:
                time_format = specs[change_to]

    if not time_format:
        raise humecord.utils.exceptions.InvalidFormat(f"Specificity {specificity} does not exist")

    return pytz.utc.localize(datetime.datetime.utcnow()).astimezone(humecord.bot.timezone).strftime(time_format)