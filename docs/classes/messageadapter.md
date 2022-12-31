### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/messages

---
# message commands

class: `humecord.classes.msgcommands.MessageAdapter`

instance: `humecord.bot.msgadapter`

---
This helper class processes, parses, and forwards any message commands to the command handler.

## outline

* **async .run(message)**:

    Checks for and runs a message.

    Params:
        message: discord.Message

* **.get_syntax_err_string(args, index)**:

    Returns a string in the following format:

    ```
    arg1 arg2 arg3 arg4
                ^^^^
    ```
    given an args array and an index.
    If index is out of bounds, pointer will be at the end of the string.

    *Params:*
    - `args` (List[str])
    - `index` (int)

    *Returns:*
    - `errstr` (str)

* **.get_err_embed(hcommand, error)**:

    Generates an error embed giving info on a command (description, args, shortcuts, aliases, subcommands).

    *Params:*
    - `hcommand` (humecord.Command): Command to gather info from
    - `error` (bool = False): If True, message's title will be "Invalid syntax" and color will be red

    *Returns:*
    - `embed` (discord.Embed)