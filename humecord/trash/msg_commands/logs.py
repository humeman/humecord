from humecord.utils import (
    discordutils,
    components
)
import humecord

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
        for i, line in enumerate(data):
            if len(current) + len(line) + len(str(i)) + 7 > 4000:
                pages.append(current)
                current = f"**{i + 1}** | {line.strip()}"

            else:
                current += f"" if len(current) == 0 else "\n"
                current += f"**{i + 1}** | {line.strip()}"

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
                ),
                components.create_button(
                    message,
                    emoji = bot.config.lang['emoji']['info'],
                    label = "Search",
                    id = "search",
                    style = "secondary",
                    callback = lambda *args: self.show_search(*args, values, None, origin, page),
                    only_sender = False,
                    row = 1
                )
            ]
        )

        if gen_new:
            msg = await resp.send(
                embed = embed,
                view = view
            )

        else:
            msg = await resp.interaction.message.edit(
                embed = embed,
                view = view
            )

        bot.replies.add_callback(
            resp.interaction.message.id,
            message.author.id,
            lambda *args: self.search(resp, *args, values, False, origin, page),
            delete_after = False
        )

    async def show_search(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb,
            values,
            search: str,
            origin: int,
            origin_log: int,
            page: int = 0,
            scroll_factor: int = 1
        ):

        matches = {}

        if search is None:
            pages = [""]

        else:
            logfile = f"logs/{values[0]}.log"

            # Read logfile
            async with aiofiles.open(logfile, "r") as f:
                data = await f.readlines()

            # Find the message in content
            matches = []

            for i, line in enumerate(data):
                line_ = line.lower()

                if search in line_:
                    matches.append(i)

            found = []

            for i in matches:
                match = data[i].strip()

                location = match.lower().find(search)

                if location != -1:
                    match = f"{match[:location]}**{match[location:location + len(search)]}**{match[location + len(search):]}"

                found.append(f"**{i + 1}** | {match}")

                # Find every log_step after
                for i_, line in enumerate(data[i + 1:]):
                    if i + i_ + 1 in matches:
                        break

                    if " ] " in line:
                        if line.split(" ] ", 1)[1].startswith(" "):
                            found.append(f"{i + i_ + 2} | {line.strip()}")

                        else:
                            break

                    else:
                        break

                found.append("")

            pages = []
            current = ""

            for line in found:
                if len(current) + len(line) + 2 > 4000:
                    pages.append(current)
                    current = line

                else:
                    current += f"" if len(current) == 0 else "\n"
                    current += line

            if current != "":
                pages.append(current)

        page_count = len(pages)

        if page < 1:
            page = 0

        if page >= page_count:
            page = page_count - 1

        if page <= 0:
            back_button = ["secondary", lambda *args: self.pass_()]

        else:
            back_button = ["primary", lambda *args: self.show_search(*args, values, search, origin, origin_log, page - scroll_factor, scroll_factor)]

        if page >= page_count - 1:
            forward_button = ["secondary", lambda *args: self.pass_()]

        else:
            forward_button = ["primary", lambda *args: self.show_search(*args, values, search, origin, origin_log, page + scroll_factor, scroll_factor)]

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
                    callback = lambda *args: self.show_log(*args, values, False, origin, 1, origin_log),
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
                    callback = lambda *args: self.show_search(*args, values, search, origin, origin_log, page, scroll_factors[current]),
                    only_sender = False,
                    row = 1
                )
            ]
        )

        if len(pages) == 0:
            content = f"No search results!"

        elif search is None:
            content = "Reply to this message with a search term."

        else:
            content = pages[page]

        embed = discordutils.create_embed(
            f"{'Ready to search!' if search is None else f'Search results (page {page + 1}/{page_count})'}",
            description = content,
            fields = [
                {
                    "name": "%-a% Details",
                    "value": f"**Search term:** `{search}`\n**Log:** `{values[0]}`"
                }
            ]
        )

        await resp.interaction.message.edit(
            embed = embed,
            view = view
        )

        bot.replies.add_callback(
            resp.interaction.message.id,
            message.author.id,
            lambda *args: self.search(resp, *args, values, False, origin, origin_log),
            delete_after = False
        )

    async def search(
            self,
            resp,
            message,
            new_resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb,
            data,
            values: list,
            gen_new: bool,
            origin: int,
            origin_log: int
        ):

        if message.content is None or len(message.content) == 0:
            await new_resp.error(
                message.author,
                "Invalid message!",
                "Reply for a search term, or -[line number] to skip to a line number."
            )
            return

        if len(values) == 0:
            return

        search = message.content.lower()

        # Parse search term
        if search.startswith("-"):
            try:
                num = int(search[1:])

            except:
                await new_resp.error(
                    message.author,
                    "Invalid syntax!",
                    f"Reply with -[line number] to skip to a line number."
                )
                return

            async with aiofiles.open(f"logs/{values[0]}.log", "r") as f:
                data = await f.readlines()

            # Send the original page at line #
            page = 0
            count = 0
            for i, line in enumerate(data):
                count += 8 + len(str(i)) + len(line.strip())
                if count > 4000:
                    page += 1
                    count = 0

                if i + 1 == num:
                    await self.show_log(
                        message,
                        resp,
                        args,
                        udb,
                        gdb,
                        alternate_gdb,
                        preferred_gdb,
                        values,
                        False,
                        origin,
                        1,
                        page
                    )
                    return

            await new_resp.error(
                message.author,
                "Line out of bounds!",
                f"Line {num} doesn't exist."
            )
            return

        await self.show_search(
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb,
            values,
            search,
            origin,
            origin_log,
            0
        )
        



scroll_factors = [
    1,
    5,
    10,
    50,
    100
]