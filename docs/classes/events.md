### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/events

---
# events

class: `humecord.classes.events.Events`

instance: `humecord.bot.events`

---
Handles callback to various events that are sent to the bot or created by Humecord classes.

## user documentation
You're probably looking for the tutorial on **[how to create events](../basics/events.md)**. This document is only the technical outline for how the event handler works.

## outline
* **.get_imports()**: 

    Returns the default set of Humecord-required events.

    *Returns:*
    - `imports` (dict): Dict of default event imports.
* **async .prep()**:

    Loads and registers all events.
* **async .call(event: str, args: list)**:

    Forces a call of the specified event.

    *Arguments:*
    - `event` (str): String name of the event to call
    - `args` (list): List of all *args to pass to the event