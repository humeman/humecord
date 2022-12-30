### [humecord](../..)/[docs](../README.md)/[basics](./README.md)/events

---
# events

This document outlines the Humecord events system, which allows you to create custom event hooks on top of any Discord event. It also allows you to intercept and manage default Humecord event hooks, as well as run code when specific Humecord actions occur.

---
## event format

As is the case with both commands and loops, Humecord events are defined as a simple class, then imported in your imports file.

For example:
```py
class OnMessageEvent:
    def __init__(self):
        self.name = "on_message"

        self.description = "Custom events to run whenever Discord sends an on_message event"

        self.event = "on_message"
        

        self.functions = {
            "function_1": {
                "function": self.function_1,
                "description": "A sample function.",
                "priority": 5
            }
        }

    async def function_1(
            self,
            message
        ):
        # Event
```

## class variables

Each class can use a number of variables that Humecord will parse whenever it fires an event - as shown above. Define these to "self" in your \_\_init\_\_() event.

* `self.name` (str) - The name of the event. Used internally, and must be unique.

* `self.description` (str) - The description of the event. Also only used internally.

* `self.event` (str) - The discord.py or Humecord event name.

* `self.functions` (dict<str: dict>) - The functions to run on event fire.
    * Each function should be formatted as follows:
    ```py
    "name": {
        "description": "Sample description",
        "function": self.function_name,
        "priority": 5
    }
    ```

    * Description is only used internally. Must be a string, if defined at all. Optional.

    * Function should be an asynchronous function to call on event fire. Any args given by Discord will be passed to this function. You can find what will be passed below.

    * Priority should be a number between 0 and 100 which defines what order functions will be called in. Functions can cancel other functions (by returning `False`) - so if you have an function that needs to fire before others so it won't be cancelled, or want a preliminary checker to validate something first, you can change the priority. 
        * Functions with a lower priority will be called first. So, `0` will take precedence over `100`.

        * To cancel every function that would run after one, just return `False`. Humecord will stop all functions with a higher priority value (=> lower priority).

## event reference

Any discord.py event, listed [here](https://discordpy.readthedocs.io/en/master/api.html#event-reference), will work with the Humecord event system.

Additionally, there's a growing number of Humecord-specific events which are fired alongside these when other events occur.

| Name                  | Description                                      | Arguments                                     |
|:---------------------:| ------------------------------------------------ | --------------------------------------------- |
| hh_on_close           | Fired before a Humecord bot shuts down.          |                                               |
| hh_on_ready           | Fired after all Humecord ready events are done.  |                                               |
| hh_on_command         | Fired when Humecord commands are dispatched.     | message, command                              |