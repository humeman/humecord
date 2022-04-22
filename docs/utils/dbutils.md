# dbutils

A primitive way to retrieve databases from the API. It will be replaced with a better method in the future, once GDBs are replaced with humecord.classes.Guild classes.

### import
```py
from humecord.utils import (
    dbutils
)
```

### dbutils.get_gdb()
**Returns:** dict

**Raises:** exceptions.APIError

**Arguments:**
  * **guild** (discord.Guild): guild to retrieve GDB of
  * **botapi** (str) = None: override bot to grab gdb from (defaults to running bot)

### dbutils.put_gdb()
**Returns:** None

**Raises:** exceptions.APIError

**Arguments:**
  * **guild** (discord.Guild): guild to push GDB of
  * **changes** (dict): dict of changes to push to API (does not have to be entire GDB, only keys and values to overwrite/create)
  * **botapi** (str) = None: override bot to push gdb to (defaults to running bot)