"""
/logs: humecord base commands

Views the bot's logs from Discord.
"""

import glob
from typing import Optional
import aiofiles

import humecord

from humecord.utils import (
    discordutils
)

class LogsCommand(humecord.Command):
    def __init__(
            self
        ) -> None:
        self.name = "logs"
        self.description = "Views the bot's logs from Discord."
        self.command_tree = {
            "": self.run
        }
        self.args = {}
        self.subcommand_details = {}
        self.messages = {
            "aliases": ["thelogs"]
        }
        self.dev = True
        self.perms = "bot.mod"
        self.default_perms = "guild.admin"

        global bot
        from humecord import bot
    
    async def run(
            self,
            resp: humecord.ResponseChannel,
            ctx: humecord.Context,
            page: int = 0
        ) -> None:
        # Find all log files.
        logs = glob.glob("logs/*.log")

        if len(logs) == 0:
            await resp.error(
                ctx.user,
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
        max_pages = len(logs) // 25 + (1 if len(logs) % 25 != 0 else 0)

        if page > max_pages:
            await resp.error(
                ctx.user,
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
            f"{bot.config.cool_name}'s logs (page {page + 1}/{max_pages})",
            description = "\n".join(comp)
        )

        if page == 0:
            back_button = [humecord.ButtonStyles.SECONDARY, bot.interactions.skip]

        else:
            back_button = [humecord.ButtonStyles.PRIMARY, lambda *args: self.run(*args, page - 1)]

        if page >= max_pages:
            forward_button = [humecord.ButtonStyles.SECONDARY, bot.interactions.skip]

        else:
            forward_button = [humecord.ButtonStyles.PRIMARY, lambda *args: self.run(*args, page + 1)]

        # Generate view
        view = await bot.interactions.create_view(
            [
                await bot.interactions.create_button(
                    "backward",
                    callback = back_button[1],
                    row = 1,
                    sender = ctx.user,
                    label = "←",
                    style = back_button[0],
                    disabled = page == 0
                ),
                await bot.interactions.create_button(
                    "forward",
                    callback = forward_button[1],
                    row = 1,
                    sender = ctx.user,
                    label = "→",
                    style = forward_button[0],
                    disabled = page == max_pages - 1
                ),
                await bot.interactions.create_select(
                    "sel",
                    callback = self.show_log,
                    row = 0,
                    options = options,
                    placeholder = "Select a logfile to view"
                )
            ]
        )

        await resp.edit(
            embed = embed,
            view = view
        )

    async def show_log(
            self,
            resp: humecord.ResponseChannel,
            ctx: humecord.Context,
            file: Optional[str] = None,
            scroll_factor_i: int = 0,
            page: int = 0
        ) -> None:

        if file is None:
            file = ctx.values[0]

        if scroll_factor_i < 0:
            scroll_factor_i = 0

        if scroll_factor_i >= len(scroll_factors):
            scroll_factor_i = len(scroll_factors) - 1

        scroll_factor = scroll_factors[scroll_factor_i]
        
        # Read log file
        async with aiofiles.open(f"logs/{file}.log", "r") as f:
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
            f"{file} (page {page + 1}/{page_count})",
            description = pages[page]
        )

        if page == 0:
            back_button = [humecord.ButtonStyles.SECONDARY, bot.interactions.skip]

        else:
            back_button = [humecord.ButtonStyles.PRIMARY, lambda *args: self.show_log(*args, file, scroll_factor_i, page - scroll_factor)]

        if page >= page_count - 1:
            forward_button = [humecord.ButtonStyles.SECONDARY, bot.interactions.skip]

        else:
            forward_button = [humecord.ButtonStyles.PRIMARY, lambda *args: self.show_log(*args, file, scroll_factor_i, page + scroll_factor)]

        current = scroll_factors.index(scroll_factor) + 1

        if current >= len(scroll_factors):
            current = 0

        view = await bot.interactions.create_view(
            [
                await bot.interactions.create_button(
                    "home",
                    callback = self.run,
                    sender = ctx.user,
                    style = humecord.ButtonStyles.PRIMARY,
                    label = "🏠"
                ),
                await bot.interactions.create_button(
                    "backward",
                    callback = back_button[1],
                    sender = ctx.user,
                    style = back_button[0],
                    label = "←",
                    disabled = page == 0
                ),
                await bot.interactions.create_button(
                    "forward",
                    callback = forward_button[1],
                    sender = ctx.user,
                    style = forward_button[0],
                    label = "→",
                    disabled = page == page_count - 1
                ),
                await bot.interactions.create_button(
                    "sf",
                    callback = lambda *args: self.show_log(*args, file, scroll_factor_i + 1, page),
                    sender = ctx.user,
                    emoji = bot.config.lang['emoji']['forward'],
                    style = humecord.ButtonStyles.GRAY,
                    label = f"Scroll factor: {scroll_factor}"
                ),
                await bot.interactions.create_button(
                    "search",
                    callback = lambda *args: self.show_search_modal(*args, file, scroll_factor_i, page),
                    sender = ctx.user,
                    style = humecord.ButtonStyles.GRAY,
                    label = "Search"
                )
            ]
        )
        await resp.edit(
            embed = embed,
            view = view
        )

    async def show_search_modal(
            self,
            resp: humecord.ResponseChannel,
            ctx: humecord.Context,
            file: Optional[str] = None,
            scroll_factor_i: int = 0,
            page: int = 0
        ) -> None:

        modal = await bot.interactions.create_modal(
            "search",
            callback = lambda *args: self.do_search(*args, file, scroll_factor_i, 0, page, None),
            sender = ctx.user,
            title = f"Search log",
            components = [
                await bot.interactions.create_textinput(
                    "search",
                    label = "Search term",
                    placeholder = "Enter search term here",
                    required = True
                )
            ]
        )

        await resp.send_modal(modal)

    async def do_search(
            self,
            resp: humecord.ResponseChannel,
            ctx: humecord.Context,
            file: Optional[str] = None,
            scroll_factor_i: int = 0,
            page: int = 0,
            old_page: int = 0,
            search: Optional[str] = None
        ) -> None:

        if search is None:
            search = ctx.modal_args["search"]

        if scroll_factor_i < 0:
            scroll_factor_i = len(scroll_factors) - 1

        if scroll_factor_i >= len(scroll_factors):
            scroll_factor_i = 0

        scroll_factor = scroll_factors[scroll_factor_i]
        logfile = f"logs/{file}.log"

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

        if page < 0:
            page = 0

        if page >= page_count:
            page = page_count - 1

        if page <= 0:
            back_button = [humecord.ButtonStyles.SECONDARY, bot.interactions.skip]

        else:
            back_button = [humecord.ButtonStyles.PRIMARY, lambda *args: self.do_search(*args, file, scroll_factor_i, page - scroll_factor, old_page, search)]

        if page >= page_count - 1:
            forward_button = [humecord.ButtonStyles.SECONDARY, bot.interactions.skip]

        else:
            forward_button = [humecord.ButtonStyles.PRIMARY, lambda *args: self.do_search(*args, file, scroll_factor_i, page + scroll_factor, old_page, search)]

        current = scroll_factors.index(scroll_factor) + 1

        if current >= len(scroll_factors):
            current = 0

        view = await bot.interactions.create_view(
            [
                await bot.interactions.create_button(
                    "home",
                    callback = lambda *args: self.show_log(*args, file, scroll_factor_i, old_page),
                    sender = ctx.user,
                    style = humecord.ButtonStyles.PRIMARY,
                    label = "🏠"
                ),
                await bot.interactions.create_button(
                    "backward",
                    callback = back_button[1],
                    sender = ctx.user,
                    style = back_button[0],
                    label = "←",
                    disabled = page == 0
                ),
                await bot.interactions.create_button(
                    "forward",
                    callback = forward_button[1],
                    sender = ctx.user,
                    style = forward_button[0],
                    label = "→",
                    disabled = page == page_count - 1
                ),
                await bot.interactions.create_button(
                    "sf",
                    callback = lambda *args: self.do_search(*args, file, scroll_factor_i + 1, page, old_page, search),
                    sender = ctx.user,
                    emoji = bot.config.lang['emoji']['forward'],
                    style = humecord.ButtonStyles.GRAY,
                    label = f"Scroll factor: {scroll_factor}"
                ),
                await bot.interactions.create_button(
                    "search",
                    callback = lambda *args: self.show_search_modal(*args, file, scroll_factor_i, old_page),
                    sender = ctx.user,
                    style = humecord.ButtonStyles.GRAY,
                    label = "Search"
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
            f"Search results (page {page + 1}/{page_count})",
            description = content,
            fields = [
                {
                    "name": "%-a% Details",
                    "value": f"**Search term:** `{search}`\n**Log:** `{file}`"
                }
            ]
        )

        await resp.edit(
            embed = embed,
            view = view
        )


scroll_factors = [
    1,
    5,
    10,
    50,
    100
]