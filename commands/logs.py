from humecord.utils import (
    discordutils,
    components
)

import glob
import math
import aiofiles

class LogsCommand:
    def __init__(
            self
        ):

        self.name = "logs"
        self.description = "A handy log viewer for all Humecord logs."

        self.aliases = ["log", "thelogs"]

        self.permission = "bot.dev"

        self.subcommands = {
            "__default__": {
                "function": self.list_,
                "description": "Lists all log files."
            }
        }

        global bot
        from humecord import bot

        global terminal
        from humecord import terminal

    async def list_(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb = None,
            preferred_gdb = None,
            gen_new: bool = True,
            page: int = 0
        ):

        # Find all log files.
        logs = glob.glob("logs/*.log")

        if len(logs) == 0:
            await resp.error(
                message.author,
                "Can't list logs!",
                "No logs are available. Did you purge my log files? >:("
            )
            return
        
        # Sort it - get a number for each logfile
        log_sort = {}
        ext = []

        for log in logs:
            log = log.split("/", 1)[1].rsplit(".", 1)[0]

            try:
                name = int(log.replace("-", ""))

                log_sort[name] = log

            except:
                ext.append(log)

        logs = [v for k, v in sorted(log_sort.items(), key = lambda x: x[0], reverse = True)] + ext

        # Find the number of pages we can render
        max_pages = math.floor(len(logs) / 25)

        if page > max_pages:
            await resp.error(
                message.author,
                "Invalid page!",
                f"Page {page + 1} exceeds maximum page of {max_pages}."
            )
            return

        # Compile list
        comp = []
        options = {}

        for logfile in logs[page * 25:(page + 1) * 25]:
            comp.append(f"→ `{logfile}`")

            options[logfile] = {
                "name": logfile[:25],
                "emoji": "📜"
            }

        if page == 0:
            comp[0] += f" *(latest)*"
            options[list(options)[0]]["description"] = "(latest)"

        # Generate embed
        embed = discordutils.create_embed(
            f"{bot.config.cool_name}'s logs",
            description = "\n".join(comp)
        )

        if page == 0:
            back_button = ["secondary", lambda *args: self.pass_()]

        else:
            back_button = ["primary", lambda *args: self.list_(*args, False, page - 1)]

        if page >= max_pages:
            forward_button = ["secondary", lambda *args: self.pass_()]

        else:
            forward_button = ["primary", lambda *args: self.list_(*args, False, page + 1)]

        # Generate view
        view = components.create_view(
            [
                components.create_button(
                    message,
                    label = "←",
                    id = "backward",
                    style = back_button[0],
                    callback = back_button[1],
                    only_sender = False,
                    row = 1
                ),
                components.create_button(
                    message,
                    label = "→",
                    id = "forward",
                    style = forward_button[0],
                    callback = forward_button[1],
                    only_sender = False,
                    row = 1
                ),
                components.create_dropdown(
                    message,
                    placeholder = "Select a logfile to view",
                    id = "sel",
                    options = options,
                    row = 0,
                    callback = lambda *args: self.show_log(*args, False, page)
                )
            ]
        )

        if len(args) > 0:
            if args[0] == "thelogs":
                embed.set_author(name = "Do you... see the logs my dude? Do you see the logs in that clip")
                embed.add_field(
                    name = "God FUCKING damnit I can't han",
                    value = "dle how retarded and great you think you are, you stupid fucking retard. Honestly, you're so retarded sometimes, Eärendil. Fucking think, before you fucking open your fat fucking mouth. You're so fucking retarded I can't handle it. You think you're so right in everything you do you stupid egotistical fuck. Legitimately, shut the fuck up and listen for once in your god damn life."
                )
                embed.title = "you FUCKING RETARD?! LOOK AT THE LOGS!"

        if gen_new:
            await resp.send(
                embed = embed,
                view = view
            )

        else:
            await resp.edit(
                embed = embed,
                view = view
            )
        
    async def pass_(
            self,
            *args
        ):
        pass

    async def show_log(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb,
            values: list,
            gen_new: bool = False,
            origin: int = 0,
            scroll_factor: int = 1,
            page: int = 0
        ):

        if len(values) == 0:
            return

        # Read log file
        async with aiofiles.open(f"logs/{values[0]}.log", "r") as f:
            data = await f.readlines()

        # Compile into pages
        pages = []
        current = ""
        for line in data:
            if len(current) + len(line) + 2 > 4000:
                pages.append(current)
                current = line

            else:
                current += f"\n" if len(current) == 0 else ""
                current += line

        if current != "":
            pages.append(current)

        page_count = len(pages)

        if page < 1:
            page = 0

        if page >= page_count:
            page = page_count - 1

        embed = discordutils.create_embed(
            f"{values[0]} (page {page + 1}/{page_count})",
            description = pages[page]
        )

        if page == 0:
            back_button = ["secondary", lambda *args: self.pass_()]

        else:
            back_button = ["primary", lambda *args: self.show_log(*args, values, False, origin, scroll_factor, page - scroll_factor)]

        if page >= page_count - 1:
            forward_button = ["secondary", lambda *args: self.pass_()]

        else:
            forward_button = ["primary", lambda *args: self.show_log(*args, values, False, origin, scroll_factor, page + scroll_factor)]

        current = scroll_factors.index(scroll_factor) + 1

        if current >= len(scroll_factors):
            current = 0

        view = components.create_view(
            [
                components.create_button(
                    message,
                    label = "🏠",
                    id = "home",
                    style = "secondary",
                    callback = lambda *args: self.list_(*args, False, origin),
                    only_sender = False,
                    row = 1
                ),
                components.create_button(
                    message,
                    label = "←",
                    id = "backward",
                    style = back_button[0],
                    callback = back_button[1],
                    only_sender = False,
                    row = 1
                ),
                components.create_button(
                    message,
                    label = "→",
                    id = "forward",
                    style = forward_button[0],
                    callback = forward_button[1],
                    only_sender = False,
                    row = 1
                ),
                components.create_button(
                    message,
                    emoji = bot.config.lang['emoji']['forward'],
                    label = str(scroll_factor),
                    id = "sf",
                    style = "secondary",
                    callback = lambda *args: self.show_log(*args, values, False, origin, scroll_factors[current], page),
                    only_sender = False,
                    row = 1
                )
            ]
        )

        if gen_new:
            await resp.send(
                embed = embed,
                view = view
            )

        else:
            await resp.interaction.message.edit(
                embed = embed,
                view = view
            )


scroll_factors = [
    1,
    5,
    10
]