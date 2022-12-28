import humecord

from humecord.utils import (
    exceptions,
    debug
)

import sys
import traceback
import asyncio
from typing import Union

async def wrap(
        function,
        exclude: list = [],
        context: dict = {},
        message = None,
        on_fail = None
    ):

    try:
        value = await function

    except exceptions.CloseLoop as e:
        raise e

    except Exception as e:
        if type(e) in exclude:
            return

        if type(e) == exceptions.APIOffline:
            if str(e) == "Failed to connect to bot API.":
                return # This was already logged.

        tb = traceback.format_exc().strip()
        tb_short = tb[:1900]

        send_long = False
        if len(tb) != len(tb_short):
            tb_short += "..."
            send_long = True

        humecord.logger.log("unhandlederror", "error", "Error handler caught an exception:", bold = True)

        humecord.logger.log_long("unhandlederror", "error", tb)

        match = ["'", "(", '"', "[", "{"]

        for char in match:
            if tb_short.count(char) % 2 != 0:
                tb_short = f"{char}{tb_short}"

        fields = [
            {
                "name": "Details",
                "value": f"Function: `{function.__name__}`\nException: `{str(type(e))}`\nMessage: `{str(e)}`"
            }
        ]

        for name, values in context.items():
            fields.append(
                {
                    "name": name,
                    "value": "\n".join(values)
                }
            )

        eid = humecord.utils.miscutils.generate_hexid(12)

        await humecord.bot.syslogger.send(
            "error",
            embed = humecord.utils.discordutils.create_embed(
                title = f"{humecord.bot.config.lang['emoji']['error']}  An uncaught exception occurred.",
                description = f"```py\n{tb_short}\n```",
                fields = fields,
                color = "error",
                footer = f"Exception ID: {eid}"
            )
        )

        if message is not None:
            if message.channel.id != humecord.bot.debug_channel.id:
                await message.channel.send(
                    embed = get_userfacing_err_embed(
                        message.author,
                        eid,
                        e
                    )
                )


        if on_fail:
            await wrap(
                on_fail[0](*on_fail[1])
            )

    else:
        return value

async def message_wrap(
        function,
        message,
        hcommand
    ):

    try:
        value = await function

    except exceptions.CloseLoop:
        raise

    except Exception as e:
        tb = traceback.format_exc().strip()
        tb_short = tb[:1900]

        if len(tb) != len(tb_short):
            tb_short += "..."

        humecord.logger.log("unhandlederror", "error", "Error handler caught an exception during message-based command execution:", bold = True)

        humecord.logger.log_long("unhandlederror", "error", tb)

        match = ["'", "(", '"', "[", "{"]

        for char in match:
            if tb_short.count(char) % 2 != 0:
                tb_short = f"{char}{tb_short}"

        eid = humecord.utils.miscutils.generate_hexid(12)

        await humecord.bot.syslogger.send(
            "error",
            embed = humecord.utils.discordutils.create_embed(
                title = f"{humecord.bot.config.lang['emoji']['error']}  An uncaught exception occurred during message-based command execution.",
                description = f"```py\n{tb_short}\n```",
                fields = [
                    {
                        "name": "Message",
                        "value": f"```\n{message.content[:950].replace('```', '')}\n```"
                    },
                    {
                        "name": "Call details",
                        "value": f"Function: `{function.__name__}`\nException: `{str(type(e))}`\nMessage: `{str(e)}`"
                    },
                    {
                        "name": "Discord details",
                        "value": f"Guild: `{message.guild.id} ({message.guild.name})`\nChannel: `{message.channel.id} (#{message.channel.name})`\nUser: `{message.author.id} ({message.author})`"
                    }
                ] + (
                    [
                        {
                            "name": "Command details",
                            "value": f"Command: `{hcommand.category}.{hcommand.name}`"
                        }
                    ]
                ),
                color = "error",
                footer = f"Exception ID: {eid}"
            )
        )


        if message.channel.id != humecord.bot.debug_channel.id:
            await message.channel.send(
                embed = get_userfacing_err_embed(
                    message.author,
                    eid,
                    e
                )
            )

    else:
        return value

async def slash_wrap(
        function,
        resp,
        ctx
    ):

    try:
        res = await function

    except (exceptions.CloseLoop, exceptions.CriticalError):
        raise

    except Exception as e:
        tb = traceback.format_exc().strip()
        tb_short = tb[:1900]

        if len(tb) != len(tb_short):
            tb_short += "..."

        match = ["'", "(", '"', "[", "{"]

        for char in match:
            if tb_short.count(char) % 2 != 0:
                tb_short = f"{char}{tb_short}"

        humecord.logger.log("unhandlederror", "error", "Error handler caught an exception during interaction:", bold = True)

        humecord.logger.log_long("unhandlederror", "error", tb)

        match = ["'", "(", '"', "[", "{"]

        for char in match:
            if tb_short.count(char) % 2 != 0:
                tb_short = f"{char}{tb_short}"

        eid = humecord.utils.miscutils.generate_hexid(12)

        details = ""

        if ctx.interaction.guild:
            details = f"Guild: `{ctx.interaction.guild.id}`\nUser: `{ctx.interaction.user.id} ({ctx.interaction.user})"

        details += f"Channel: `{ctx.channel.id}`\n"

        await humecord.bot.syslogger.send(
            "error",
            embed = humecord.utils.discordutils.create_embed(
                title = f"{humecord.bot.config.lang['emoji']['error']}  An uncaught exception occurred during command execution.",
                description = f"```py\n{tb_short}\n```",
                fields = [
                    {
                        "name": "Command",
                        "value": f"```\n{ctx.hcommand.full_name}\n```"
                    },
                    {
                        "name": "Call details",
                        "value": f"Function: `{function.__name__}`\nException: `{str(type(e))}`\nMessage: `{str(e)}`"
                    },
                    {
                        "name": "Discord details",
                        "value": details
                    }
                ],
                color = "error",
                footer = f"Exception ID: {eid}"
            )
        )


        if ctx.channel.id != humecord.bot.debug_channel.id:
            await resp.send(
                embed = get_userfacing_err_embed(
                    ctx.user,
                    eid,
                    e
                )
            )

    else:
        return res

async def get_userfacing_err_embed(
        author,
        eid,
        e
    ):
    expand = ""
    name = ""
    if humecord.bot.config.lang["error"].get("exception_details"):
        expand = humecord.bot.config.lang["error"]["exception_details"]

        name = str(e.__class__).split("'", 1)[1].rsplit("'", 1)[0]

        if humecord.bot.config.lang["error"]["only_share_if_humecord"]:
            if not name.startswith("humecord."):
                expand = ""
                name = ""

        if humecord.bot.config.lang["error"]["share_args"] and name != "":
            try:
                name += f": {' '.join(list(e.args))}"
            
            except:
                pass

    description = humecord.utils.miscutils.expand_placeholders(
        f"{humecord.bot.config.lang['error']['description']}{expand}",
        {
            "id": eid,
            "ex": name
        }
    )     

    return humecord.utils.discordutils.error(
        author,
        humecord.bot.config.lang["error"]["title"],
        description
    )   

def base_wrap(
        function,
        args: list = [],
        kwargs: dict = {}
    ):

    try:
        function(*args, **kwargs)

    except (exceptions.InitError, exceptions.CriticalError) as e:
        humecord.bot.loop.stop()

        humecord.terminal.log(" ", True)

        if type(e) == exceptions.InitError:
            title = "An initialization error occurred!"

        elif type(e) == exceptions.CriticalError:
            title = "A critical error occurred!"

        # Forward it off to the logger
        if e.traceback:
            debug.print_traceback(
                title
            )
            humecord.terminal.log(" ", True)
            humecord.logger.log_step("unhandlederror", "error", e.message, bold = True)

        elif e.log:
            humecord.logger.log("unhandlederror", "error", title, bold = True)
            humecord.logger.log_step("unhandlederror", "error", e.message)

        humecord.bot.shutdown(title, safe = True, error_state = True)

    except (SystemExit, KeyboardInterrupt, exceptions.CloseLoop):
        raise

    except:
        humecord.terminal.log(" ", True)
        debug.print_traceback(
            f"An unexpected initialization error occurred!"
        )

        humecord.bot.shutdown("Unexpected initialization error", error_state = True)

async def async_wrap(
        coro
    ):

    try:
        await coro

    except (exceptions.InitError, exceptions.CriticalError) as e:
        humecord.terminal.log(" ", True)

        if type(e) == exceptions.InitError:
            title = "An initialization error occurred!"

        elif type(e) == exceptions.CriticalError:
            title = "A critical error occurred!"

        # Forward it off to the logger
        if e.traceback:
            debug.print_traceback(
                title
            )
            humecord.terminal.log(" ", True)
            humecord.logger.log_step("unhandlederror", "error", e.message, bold = True)

        elif e.log:
            humecord.logger.log("unhandlederror", "error", title, bold = True)
            humecord.logger.log_step("unhandlederror", "error", e.message)

        await humecord.bot.shutdown(title, safe = True, error_state = True)

    except (SystemExit, KeyboardInterrupt, exceptions.CloseLoop):
        raise

    except:
        humecord.terminal.log(" ", True)
        debug.print_traceback(
            f"An unexpected initialization error occurred!"
        )

        await humecord.bot.shutdown("Unexpected initialization error", error_state = True)

