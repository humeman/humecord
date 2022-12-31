### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/discordclasses

---
# discord classes

module: `humecord.classes.discordclasses`

classes: `ResponseChannel (-> MessageResponseChannel, InteractionResponseChannel, ThreadResponseChannel), Args, Context`

---
This file contains a number of classes which serve as interfaces with various Discord methods -- or, more specifically, the arguments passed to a command/interaction callback.

## outline

### ResponseChannel
* **.type (humecord.RespTypes)**

    The type of the response channel.

    One of:
    `.NONE`, `.MESSAGE`, `.THREAD`, or `.INTERACTION`.
* **async .send(\*args)**

    Sends a new message in the designated channel.

    If this is an interaction and the response has already been used, this will automatically use the followup webhook instead.

    Additionally, if the interaction has been deferred, this will do the same thing.

    Has the same args and kwargs as Discord.py's `.send_message()`.

* **async .edit(*args)**

    Edits the message, if applicable.

    If a message has not yet been sent, it will send one.

* **async .send_modal(modal)**

    Sends a modal, if possible.

    *Params:*
    - `modal` (discord.ui.Modal)

* **async .defer(*args, \*\*kwargs)**

    Defers an interaction response. Args and kwargs are passed to `interaction.response.defer`.

### Context
Class which contains any command/interaction context. Attributes vary from case to case. Check the [command handler](./commands.md) and [interaction manager](./interactions.md) docs for possible attributes.

### Args
Class which contains any args received in the command call.

* **.exists(key)**:

    Checks if a specific attribute exists.

    *Params:*
    - `key` (str): Arg name

    *Returns:
    - `exists` (bool): Whether or not arg exists