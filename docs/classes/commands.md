### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/commands

---
# commands

class: `humecord.classes.commands.CommandHandler, .msgcommands.MessageAdapter`

instance: `humecord.bot.commands, .msgcommands`

---
This file contains the API reference for Humecord's command handler.

The command handler is available in `bot.commands`, and there is a shortcut to .HumecordCommand at `humecord.Command`.
This only handles registration of commands and slash command interactions. For message-based command execution,
see the docs for the [MessageAdapter](./messageadapter.md)


## user documentation
⚠️ **NOTE**: You're probably looking for the tutorial on **[how to create commands](../basics/events.md)**. This document is only the technical outline for how the command handler works.

## outline
* **.reset()**: 

    Resets the internal command tree.
* **async .prep_loader()**:

    Prepares a command tree for the Humecord Loader to do its magic on.
* **async .sync()**:

    Prepares a slash command tree command tree for syncing to Discord. Does not actually push any changes -- it is stored locally until `.sync_to` or `.sync_global` is called.

    If you're looking to reload the command tree, check out the [Humecord Loader](./loader.md)'s reload function. Otherwise, call `.reset()`, then `.prep_loader()`, and finally `.sync()`.
* **async .sync_to(guild: discord.Guild, copy: bool = False)**:
    Syncs the local command tree to a single guild.
    
    *Params:*
    - `guild` (discord.Guild): Target guild to sync to
    - `copy` (bool = False): If True, the global command tree will be copied to this guild
        
    *Returns:*
    - `count` (int): Commands synced
* **async .clear_tree(guild: discord.Guild)**:
    Clears a guild's local command tree.
    
    *Params:*
    - `guild` (discord.Guild): Target guild to clear
* **async .sync_global()**:
    Syncs the local command tree globally. Changes take a while to propogate.
        
    *Returns:*
    - `count` (int): Commands synced