# humecord.utils.discordutils

This utility library contains a bunch of miscellaneous functions that help you interact with Discord better.

## import

```py
from humecord.utils import discordutils
```

## methods

### discordutils.create_embed()

**Returns:** discord.Embed
**Raises:** Nothing
**Arguments:** (All arguments are optional. At least one text option must be specified or Discord will refuse to post the embed.)
  * **title** (str): Title of the embed.
  * **description** (str): Description of the embed.
  * **fields** (list): Embed fields, formatted as follows:
    ```py
    [
        {
            "name": "field1",
            "value": "test",
            "inline": False # Optional, defaults to False
        },
        {
            "name": "field2",
            "value": "test2",
            "inline": True
        }
    ]
    ```
  * **color** (str or int): Color to use.
    See all possible string color values in [colors.py](/utils/colors.py).
  * **footer** (str): Footer to add.
  * **thumbnail** (str - url): URL to an image to post in the upper right corner of the embed.
  * **image** (str - url): URL to an image to post as the embed's image.
  * **author** (discord.User or discord.Member): Sets a discord user as the author of the embed.
  * **profile** (list): Manually changes the embed's profile with a list: [name, icon, url] (icon and url are optional)

This method is also available via `await resp.embed()`. Learn more about response channels [here](../classes/responsechannels.md).

### discordutils.error()

**Returns:** discord.Embed
**Raises:** Nothing
**Arguments:**
  * **member** (discord.Member or discord.User or None): Member to point the error to (typically `message.author`)
  * **title** (str): Error message title
  * **description** (str): Error message description (optional)

This method is also available via `await resp.error()`. Learn more about response channels [here](../classes/responsechannels.md).
