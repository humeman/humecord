import humecord

from humecord.utils import (
    colors
)

def prep():
    global bot
    from humecord import bot

async def help(
        parent,
        args,
        error = None
    ):

    if len(args) <= 1:
        # List every command
        await parent.send(0, "Command list:", True)

        # Compile a list of messages
        msgs = []

        for name, command in parent.commands.items():
            padding = " " * (12 - len(name))

            msgs.append(f"{colors.termcolors['bold']}{name}{padding}: {colors.termcolors['reset']}{humecord.terminal.color['response']}{command['description']}")

        # Send it back
        await parent.send(0, msgs)

    else:
        search = args[1].lower()

        match = None
        cmd = None

        # Find the specified command/alias/shortcut
        for name, command in parent.commands.items():
            if (search == name
                or name in (command["aliases"] if "aliases" in command else [])
                or name in (command["shortcuts"] if "shortcuts" in command else [])
            ):
                match = name
                cmd = command
                break

        if match is None:
            await parent.send(1, f"No command, alias, or shortcut found by name '{name}'.")
            return

        await parent.send(0, f"{match}{(' ' + cmd['syntax']) if 'syntax' in cmd else ''}", True)

        msgs = [
            cmd["description"]
        ]

        msg_comp = {}

        if "aliases" in cmd:
            msg_comp["Aliases"] = ", ".join(cmd["aliases"])

        if "shortcuts" in cmd:
            msg_comp["Shortcuts"] = ", ".join([f"{x} → {y}" for x, y in cmd['shortcuts'].items()])

        for name, value in msg_comp.items():
            msgs.append(f" • {humecord.terminal.terminal.underline}{name}{humecord.terminal.terminal.reset}{humecord.terminal.color['response']}: {value}")

        await parent.send(0, msgs)

async def say(
        parent,
        args
    ):

    if len(args) < 3:
        await parent.syntax("say")
        return

    valid, value = await bot.args.parse("int", args[1], {})

    if not valid:
        await parent.send(1, "Specify a channel for the first argument.", True)
        return

    channel = bot.client.get_channel(value)

    if channel is None:
        user = bot.client.get_user(value)

        if user is None:
            await parent.send(1, f"No channel by ID {args[1]}!", True)
            return

    msg = " ".join(args[2:])

    if len(msg) == 0:
        await parent.send(1, "Message can't be empty!", True)
        return
    
    if len(msg) > 2000:
        await parent.send(1, f"Message is too long! ({len(msg)})", True)
        return

    try:
        await channel.send(msg)

    except Exception as e:
        await parent.send(1, f"Failed to send message!", True)
        await parent.send(1, str(e))

    else:
        await parent.send(0, f"Sent message '{msg[:50]}{'...' if len(msg) > 50 else ''}' to #{channel.name}.")

async def eval_(
        parent,
        args
    ):

    if len(args) < 2:
        await parent.syntax("eval")
        return

    cmd = " ".join(args[1:])

    exec(f"async def __eval_cmd(parent, args):\n  return {cmd}", globals())

    val = await globals()["__eval_cmd"](parent, args)

    del globals()["__eval_cmd"]

    await parent.send(0, str(val))

async def reload(
        parent,
        args
    ):

    safe = True
    if len(args) > 1:
        if args[1].lower() == "force":
            safe = False

    await bot.loader.load(safe_stop = safe)

    await parent.send(0, f"Reloaded! (Safe reload: {'Yes' if safe else 'No'})", True)

async def disable(
        parent,
        args
    ):

    with open(".classicterminal", "w+"):
        pass

    await parent.send(0, f"Terminal disabled.", True)
    await parent.send(0, f"Restart to take effect. To undo, delete '.classicterminal' from the bot's directory.")