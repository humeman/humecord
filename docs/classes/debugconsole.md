### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/debugconsole

---
# debug console

class: `humecord.classes.debugconsole.DebugConsole`

instance: `humecord.bot.debug_console`

---
This helper class provides an interface for the interactive Python console available in the debugging console.

## usage
To start a debugging session, type `>` in your bot's debug channel. It will react with a checkmark if the action was successful.

Then, simply enter any valid Python statement or statements into the channel. They will be evaluated, and the corresponding value returned.

Sessions are persistent across restarts for debugging purposes.

To end a session, type `<`.