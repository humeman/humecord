### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/permissions

---
# permissions

class: `humecord.classes.permissions.Permissions`

instance: `humecord.bot.permissions`

---
This class allows you to easily check the discord, bot, and global permissions of a user.

## outline

The following attributes are available:
* **.bot** (dict)

    All "bot." permissions.
* **.guild** (dict)

    All "guild." permissions.
* **.user** (dict)

    All "user." permissions
* **async .check(member, permission, udb)**

    Checks a user's permissions.

    *Arguments:*
    - `member` (discord.Member or discord.User): The member to check the permissions of.
    - `permission` (str): The [permission node](../misc/permissions.md) to check for.
    - `udb` (dict): The user's udb. Available in a command via the `udb` argument. Otherwise found in the `main/user` endpoint of the API.

    *Returns:* 
    - `valid` (bool): Whether or not the user has these permissions

    *Raises:* 
    - `InvalidPermission`

    *Example:*
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