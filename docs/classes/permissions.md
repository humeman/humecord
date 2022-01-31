# classes.permissions.Permissions

This class allows you to easily check the discord, bot, and global permissions of a user.

It is available in `bot.permissions`.

## outline

The following attributes are available:
* `.bot` (dict): All "bot." permissions
* `.guild` (dict): All "guild." permissions
* `.user` (dict): All "user." permissions
* `async .check(member, permission, udb)`:
    **Returns:** valid (bool)
    **Raises:** exceptions.InvalidPermission
    **Arguments:**
        * **member** (discord.Member or discord.User): The member to check the permissions of.
        * **permission** (str): The [permission node](../misc/permissions.md) to check for.
        * **udb** (dict): The user's udb. Available in a command via the `udb` argument. Otherwise found in the `main/user` endpoint of the API.

    **Example:**
    To check if the user has the permission `guild.admin`:
    ```py
    allowed = await bot.permissions.check(
        message.author,
        "guild.admin",
        udb
    )

    if allowed:
        # do stuff
    
    else:
        await resp.error(
            message.author,
            "Missing permissions!",
            "You need the `guild.admin` permission to do this."
        )
    ```


For a list of all available permission nodes and what they do, visit the [argument parser](../misc/argparser.md) doc page.