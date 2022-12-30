### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/syslogger

---
# system logger

class: `humecord.classes.syslogger.SystemLogger`

instance: `humecord.bot.syslogger`

---
The system logger is how Humecord logs messages to your bot's debug channel. It allows for sending, as well as management in the form of disabling/pausing various message types.

## outline

Sending a message via the syslogger is simple:

```py
from utils import discordutils

await bot.syslogger.send(
    "user", # Message type = user - other types are system reserved
    "Some message content!", # Usual args from await channel.send() from here on out
    embed = discordutils.create_embed(
        "Test embed",
        "This is a test embed."
        color = "orange"
    )
)
```

## api reference

* **.log_types** (dict)

    A dict of all log type defaults: start, stop, api, ws, error, and user.
* **.override** (dict)

    Overrides a log type while the bot is running. Overwritten and not saved.
* **await .send(message_type: str, *args, **kwargs)**

    Sends a message of type `message_type` (from `log_types`) to the debug channel.

    *Arguments:*
    - `message_type` (str): Log type to use
    - `*args`, `**kwargs`: Args to pass to `channel.send()`

    *Returns:*
    - `message`: discord.Message object sent. None if message wasn't sent.

    *Raises:*
    - `DevError`: Message type doesn't exist

* **.get_status(message_type: str)**

    Gets the current status of a particular log type.

    *Arguments:*
    - `message_type` (str): Log type to check

    *Returns:*
    - `run` (bool): Whether or not the message type is active
    - `status`: Reason the message type is active/inactive

    *Raises:*
    - `DevError`: Message type doesn't exist

    