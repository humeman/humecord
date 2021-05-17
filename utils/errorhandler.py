import humecord

import traceback
from typing import Union

async def wrap(
        function,
        exclude: list = [],
        context: dict = {},
        on_fail = None
    ):

    try:
        await function

    except Exception as e:
        if type(e) in exclude:
            return

        tb = traceback.format_exc().strip()
        tb_short = tb[:1900]

        send_long = False
        if len(tb) != len(tb_short):
            tb_short += "..."
            send_long = True

        humecord.utils.logger.log("error", "Error handler caught an exception:", bold = True)

        humecord.utils.logger.log_long(tb, "red")

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

        await humecord.bot.debug_channel.send(
            embed = humecord.utils.discordutils.create_embed(
                title = f"{humecord.bot.config.lang['emoji']['error']}  An uncaught exception occurred.",
                description = f"```py\n{tb_short}\n```",
                fields = fields,
                color = "error"
            )
        )

        if on_fail:
            await wrap(
                on_fail[0](*on_fail[1])
            )

async def discord_wrap(
        function,
        message,
        command: Union[list, None] = None
    ):

    try:
        await function

    except Exception as e:
        tb = traceback.format_exc().strip()
        tb_short = tb[:1900]

        send_long = False
        if len(tb) != len(tb_short):
            tb_short += "..."
            send_long = True

        humecord.utils.logger.log("error", "Error handler caught an exception during discord call:", bold = True)

        humecord.utils.logger.log_long(tb, "red")

        match = ["'", "(", '"', "[", "{"]

        for char in match:
            if tb_short.count(char) % 2 != 0:
                tb_short = f"{char}{tb_short}"

        shortcut_details = ""
        if command:
            if command[2]["type"] == "shortcut":
                shortcut_details = f" ({' '.join(command[2]['match'])} -> {command[2]['replace_with']})"

            elif command[2]["type"] == "alias":
                shortcut_details = f" ({' '.join(command[2]['match'])} -> {command[1].name})"

        await humecord.bot.debug_channel.send(
            embed = humecord.utils.discordutils.create_embed(
                title = f"{humecord.bot.config.lang['emoji']['error']}  An uncaught exception occurred during command execution.",
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
                            "value": f"Command: `{command[0]}.{command[1].name}`\nMatch type: `{command[2]['type']}{shortcut_details}`"
                        }
                    ] if command else []
                ),
                color = "error"
            )
        )
