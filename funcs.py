import sys
from functools import wraps
import humecord


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