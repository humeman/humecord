import sys
from functools import wraps
import humecord
import discord

def add_path(
        path: str
    ):

    sys.path.append(path)

def event(event_name, priority = 5):
    def inner(function):
        humecord.extra_events.append(
            GeneratedEvent(
                event_name,
                priority,
                function
            )
        )

        @wraps(function)
        async def dec(*args, **kwargs):
            return await function(*args, **kwargs)

        return dec

    return inner

class GeneratedEvent:
    def __init__(self, event_name, priority, function):
        self.name = f"__hc_generated_{event_name}"
        self.description = "Generated on the fly via a decorated function."

        self.event = event_name

        self.__function = function

        self.functions = {
            "main": {
                "function": self.__function,
                "priority": priority
            }
        }

# Verifies the Python version installed
def verify_min_py_version(major, minor):
    ver = sys.version_info

    if ver.major != major or ver.minor < minor:
        print(f"\033[31m\033[1m[ERR] \033[0m\033[31mYou need Python {major}.{minor}.X installed to use Humecord (currently {ver.major}.{ver.minor}.{ver.micro}).\033[0m")
        sys.exit(-1)

# Verifies discord.py version
def verify_min_dpy_version(major, minor):
    ver = discord.__version__

    c_major, c_minor, __ = ver.split(".", 2)
    
    c_major = int(c_major)
    c_minor = int(c_minor)

    if c_major != major or c_minor < minor:
        print(f"\033[31m\033[1m[ERR] \033[0m\033[31mYou need discord.py {major}.{minor}.X installed to use Humecord (currently {ver}).\033[0m")
        sys.exit(-1)