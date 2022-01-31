# bot

This document outlines the main Humecord bot class, which holds all the important data and objects for your bot's operation.

## outline

Each bot class has the following attributes:

* **bot.loop**: active asyncio loop
* **bot.console** ([humecord.classes.console.Console](https://github.com/humeman/humecord/blob/docs/classes/console.md)): Humecord Console instance
* **bot.loader** ([humecord.classes.loader.Loader](https://github.com/humeman/humecord/blob/docs/classes/imports.md)): Humecord Loader instance
* **bot.names** (List[str)): list of all possible identifying bot names (config name, cool name, name aliases)
* **bot.mem_storage** (Dict[str, any)): Memory storage instance, defined in config.mem_storage
* **bot.started** (bool): Defines if the bot has started or not
* **bot.timer** (time.time): Time at which the bot started
* **bot.client** (discord.Client): Active discord client instance
* **bot.timezone** (pytz.timezone): Configured timezone object
* **bot.syslogger** ([humecord.classes.syslogger.SysLogger](https://github.com/humeman/humecord/blob/docs/classes/syslogger.md)): Humecord syslogger instance
* **bot.commands** ([humecord.classes.commands.Commands](https://github.com/humeman/humecord/blob/docs/classes/commands.md)): Command handler instance
* **bot.loops** ([humecord.classes.loops.Loops](https://github.com/humeman/humecord/blob/docs/classes/loops.md)): Loop handler instance
* **bot.events** ([humecord.classes.events.Events](https://github.com/humeman/humecord/blob/docs/classes/events.md)): Event handler instance
* **bot.replies** ([humecord.classes.replies.Replies](https://github.com/humeman/humecord/blob/docs/classes/replies.md)): Reply handler instance
* **bot.interactions** ([humecord.classes.interactions.Interactions](https://github.com/humeman/humecord/blob/docs/classes/interactions.md)): Interaction handler instance
* **bot.files** ([humecord.interfaces.files.FileInterface](https://github.com/humeman/humecord/blob/docs/interfaces/files.md)): File interface instance
* **bot.debug_console** ([humecord.classes.debugconsole.DebugConsole](https://github.com/humeman/humecord/blob/docs/classes/debugconsole.md)): Debug console instance
* **bot.permissions** ([humecord.classes.permissions.Permissions](https://github.com/humeman/humecord/blob/docs/classes/permissions.md)): Permission checker instance
* **bot.args** ([humecord.classes.argparser.ArgumentParser](https://github.com/humeman/humecord/blob/docs/classes/argparser.md)): Argument parser instance
* **bot.messages** ([humecord.classes.messages.Messages](https://github.com/humeman/humecord/blob/docs/classes/messages.md)): Messenger instance
* **async bot.shutdown(reason, safe = True, error_state = False, skip_shutdown = False)**
  Shuts down the bot with the specified `reason`.
  If safe, Humecord will attempt to shut down the command handler/api interface/ws handler/etc safely before closing the asyncio loop.
  If error_state, Humecord will notify the user of the last thrown exception.
  If skip_shutdown, Humecord will close immediately with no logging or any attempt to shut down safely.