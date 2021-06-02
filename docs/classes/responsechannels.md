# response channels

This document outlines how to use the ResponseChannel class. ResponseChannels should be used instead of old calls, like `message.channel.send()`, since they allow for compatibility with interactions (like slash commands and buttons). If you don't use them, chances are the command will still work - but the user will get a "This interaction failed" error message, and you won't be able to use some of the new features they offer.

## outline

Each slash command has the following attributes:

* `.type` - defines the type of the response channel (or where it forwards to)
    * Can be one of `component`, `slashcommand`, or `message`
    
* `.channel` - The actual discord.TextChannel which messages are forwarded to

* `async .send(*args)` - Same syntax as `channel.send` in discord.py. Sends the message in the designated channel.

* `async .edit(*args)` - Same as the above, but edits the message (if applicable).
    * Not defined for MessageResponseChannels or SlashCommandResponseChannels.