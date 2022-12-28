from typing import Union
import time

import humecord

from humecord.utils import (
    exceptions
)

async def check_command_ratelimit(
        category: str,
        command,
        udb: dict,
        subcommand: str = "__main__"
    ):

    if hasattr(command, "ratelimit"):
        ratelimit = command.ratelimit

    else:
        ratelimit = humecord.bot.config.default_ratelimit

    if hasattr(command, "global_ratelimit"):
        global_ratelimit = command.global_ratelimit

    else:
        global_ratelimit = False

    return await check_ratelimited(
        [category, command.name],
        ratelimit,
        udb,
        global_ratelimit,
        subcommand
    )

async def check_ratelimited(
        command_name: list,
        ratelimit: Union[dict, str],
        udb: dict,
        global_ratelimit: bool = False,
        subcommand: str = "__main__"
    ):
    write = False
    write_to = []

    # Retrieve the command's ratelimit
    # Check if string or dict
    if type(ratelimit) == str:
        # This is a group - actual rate limit is in config
        if ratelimit not in humecord.bot.config.ratelimit_groups:
            raise exceptions.DevError(f"Ratelimit group {ratelimit} doesn't exist")

        # Get the actual ratelimit values
        ratelimit = humecord.bot.config.ratelimit_groups[ratelimit]

    # Otherwise, this is a manual group definition - so go with it
    # Get the user's group
    group = udb["group"]

    me = humecord.bot.config.self_api
    if "per_bot" in udb:
        # Check if I'm in there
        if me in udb["per_bot"]:
            group = udb["per_bot"][me]
            write = True
            write_to.append("udb")

    # Check if the group is in the ratelimit
    if group not in ratelimit:
        raise exceptions.DevError(f"Group {group} isn't registered for this ratelimit")

    # Get the time from that group
    delay = ratelimit[group]

    # Check if the command has been run before
    if global_ratelimit:
        if me not in udb["ratelimits"]:
            udb["ratelimits"][me] = {}
            write = True
            write_to.append("udb")
        
        using = "udb"
        base = udb["ratelimits"][me]

    else:
        using = "file"
        base = humecord.bot.files.files["__users__.json"]["ratelimits"]

    # Check if category in details
    if command_name[0] not in base:
        base[command_name[0]] = {}
        write = True
        write_to.append(using)

    # Check if command in details
    if command_name[1] not in base[command_name[0]]:
        # Define it
        base[command_name[0]][command_name[1]] = {}
        write = True
        write_to.append(using)

    new = base[command_name[0]][command_name[1]]
    # Check if subcommand in details
    if subcommand not in new:
        new[subcommand] = None
        write = True
        write_to.append(using)

    # Check if ratelimited
    limited = False
    left = None
    if new[subcommand] is not None:
        if new[subcommand] + delay > time.time():
            # Rate limited
            limited = True
            left = (new[subcommand] + delay) - time.time()

    # If not limited, store the new last run time
    if not limited:
        if using == "file":
            humecord.bot.files.files["__users__.json"]["ratelimits"][command_name[0]][command_name[1]][subcommand] = float(time.time())
        
        else:
            udb["ratelimits"][command_name[0]][command_name[1]][subcommand] = float(time.time())

        write = True
        write_to.append(using)

    # Write stuff
    if write:
        if "file" in write_to:
            humecord.bot.files.write("__users__.json")

        write = "udb" in write_to # Whatever runs this has to deal with that

    # Return things
    return (
        limited,
        delay,
        left,
        udb, # New udb, so whatever's using this can write changes
        write
    )