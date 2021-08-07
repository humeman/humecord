#import aioconsole
from humecord import utils
import asyncio
import sys
import curses
from threading import Thread
import re

import humecord

from humecord.utils import (
    discordutils,
    colors,
    debug,
    consolecommands
)

from humecord.utils.async_mcrcon import MinecraftClient

ansi_escape = re.compile(r'''
    \x1B  # ESC
    (?:   # 7-bit C1 Fe (except CSI)
        [@-Z\\-_]
    |     # or [ for CSI, followed by a control sequence
        \[
        [0-?]*  # Parameter bytes
        [ -/]*  # Intermediate bytes
        [@-~]   # Final byte
    )
''', re.VERBOSE)

class Console:
    def __init__(self):
        global bot
        from humecord import bot

        self.error_state = False

        self.char = None

        self.screen = curses.initscr()

        self.current = ""
        self.history = []
        self.hist_current = None

        self.location = 0

        #logger.on_log.append(
        #    self.log_current
        #)

        self.loop = asyncio.get_event_loop()

        self.shutdown = False

        self.sequences = {
            343: Actions.execute, # Enter
            263: Actions.backspace, # Backspace
            330: Actions.delete, # Delete
            337: lambda *args: Actions.history(*args, -1), #lambda *args: Actions.scroll(*args, -1), # Shift arrow up
            336: lambda *args: Actions.history(*args, 1), #lambda *args: Actions.scroll(*args, 1), # Shift arrow down
            339: lambda *args: Actions.scroll(*args, -1 * (humecord.terminal.terminal.height - 8)), # Page up
            338: lambda *args: Actions.scroll(*args, humecord.terminal.terminal.height - 8), # Page down
            259: lambda *args: Actions.scroll(*args, -1), # Arrow up
            258: lambda *args: Actions.scroll(*args, 1), # Arrow down
            361: Actions.activate_esc,
            385: Actions.shutdown,
            360: Actions.shutdown,
            260: lambda *args: Actions.scroll_terminal(*args, -1), # Scroll left
            261: lambda *args: Actions.scroll_terminal(*args, 1), # Scroll right
            331: Actions.reload, # Insert
            362: Actions.home # you'd never believe it
        }

        self.chars = {
            "\x17": Actions.backspace,
            "\x04": Actions.shutdown
        }

        self.escapes = {
            "[1;5D": lambda *args: Actions.scroll_far(*args, -1), # Ctrl arrow left
            "[1;5C": lambda *args: Actions.scroll_far(*args, 1), # Ctrl arrow right
            "[1;5A": lambda *args: Actions.history(*args, -1), # Ctrl arrow up
            "[1;5B": lambda *args: Actions.history(*args, 1) # Ctrl arrow down
        }

        self.commands = ConsoleCommandHandler(self)

        self.escape = False
        self.escape_mem = ""

        self.start()

    def start(self):
        self.thread = Thread(target = self.wait_for_key)
        self.thread.start()

    def wait_for_key(self):
        while not self.shutdown:
            try:
                char = humecord.terminal.getch(timeout = 0.02)

                if not char:
                    if self.escape:
                        self.escape = False
                        self.current = ""
                        self.location = 0
                        humecord.terminal.reprint(log_console = True)

                    continue

                self.got_input(char)

            except Exception as e:
                humecord.terminal.log(f"{type(e)} {str(e)}", True)

    def got_input(self, char):
        self.incoming_char(char)

    def incoming_char(self, char):
        if char.is_sequence:
            # Check for sequences
            code = char.code
            try:
                if code in self.sequences:
                    self.sequences[code](self, char)

                else:
                    humecord.terminal.log(str(code))

            except:
                debug.print_traceback("An error occured while processing keypress!")

        else:
            # Check for chars
            code = str(char)

            run = False
            try:
                if code in self.chars:
                    self.chars[code](self, char)
                    run = True

            except:
                debug.print_traceback("An error occured while processing keypress!")

            # Collect escape chars
            if self.escape:
                self.escape_mem += char.__str__()
                run = True

                if len(self.escape_mem) == 5:
                    if self.escape_mem in self.escapes:
                        # Run
                        try:
                            self.escapes[self.escape_mem](self, char)

                        except:
                            debug.print_traceback("An error occured while processing keypress!")

                    else:
                        # Not an escape char - treat it like clear, then append escape mem and run
                        self.current = self.escape_mem
                        self.location = 5
                        run = False

                    self.escape = False
                    self.escape_mem = ""

            # Append to current if not an action
            if not run:
                self.current = f"{self.current[:self.location]}{char.__str__()}{self.current[self.location:]}"
                self.location += 1

        humecord.terminal.reprint(log_logs = True, log_console = True)

    async def call(
            self,
            command: str
        ):

        await self.commands.run(command)

class Actions:
    def execute(self, char):
        if self.error_state:
            return

        humecord.terminal.log(f"{humecord.terminal.color['terminal']}{colors.termcolors['bold']}$ {colors.termcolors['reset']}{humecord.terminal.color['terminal']}{self.current}", True)
        
        self.loop.create_task(self.commands.run(self.current))

        self.current = ""
        
        #self.current = ""
        self.location = 0

    def backspace(self, char):
        c = char.__str__()

        if c == "\x7f":
            # Backspace
            index = self.location - 1

            if index >= 0:
                self.current = f"{self.current[:index]}{self.current[index + 1:]}"

                self.location = index

        elif c in ["\x08", "\x17"]:
            # Ctrl backspace
            # Start at index, remove until space
            search = self.current.rfind(" ", 0, self.location)

            if search == -1:
                self.current = self.current[self.location:]
                self.location = 0

            else:
                # Remove everything in between
                self.current = f"{self.current[:search]}{self.current[self.location:]}"
                self.location = search

    def delete(self, char):
        index = self.location

        if index < len(self.current):
            self.current = f"{self.current[:index]}{self.current[index + 1:]}"

    def scroll(self, char, diff):
        humecord.terminal.scroll(diff)

    def activate_esc(self, char):
        self.escape = True
        self.escape_mem = ""

    def scroll_far(self, char, direction):
        if direction > 0:
            # Scrolling forward - find first space after current
            location = self.current.find(" ", self.location + 1)

            if location == -1:
                # Jump to end
                self.location = len(self.current)

            else:
                # Jump to letter after space
                self.location = location + 1

        else:
            # Scrolling backwards - find last space before current
            location = self.current.rfind(" ", 0, self.location)

            if location == -1:
                # Go to start of message
                self.location = 0

            else:
                # Jump to space
                self.location = location

    def scroll_terminal(self, char, diff):
        self.location += diff

        if diff > 0:
            if self.location > len(self.current):
                self.location = len(self.current)

        elif diff < 0:
            if self.location < 0:
                self.location = 0

    def shutdown(self, char):
        humecord.bot.loop.create_task(humecord.bot.shutdown("Terminal shutdown"))

    def history(self, char, new):
        if self.hist_current is None:
            self.hist_current = len(self.history)

        self.hist_current += new

        if self.hist_current < 0:
            self.hist_current = 0

        if self.hist_current >= len(self.history):
            self.hist_current = None

        if self.hist_current == None:
            # Set to nothing
            self.current = ""
            self.location = 0

        else:
            # Set to hist index
            self.current = str(self.history[self.hist_current])
            self.location = len(self.current)

    def reload(self, char):
        humecord.terminal.log_action(f"reload")
        humecord.bot.loop.create_task(humecord.bot.loader.load(safe_stop = True))
        
    def home(self, char):
        humecord.terminal.manual_scroll = False

        humecord.terminal.location = len(humecord.terminal.lines) - humecord.terminal.log_count

        if humecord.terminal.location < 0:
            humecord.terminal.location = 0

class ConsoleCommandHandler:
    def __init__(
            self,
            parent: Console
        ):
        self.commands = {
            "help": {
                "description": "Lists all available commands.",
                "syntax": "(command)",
                "aliases": ["commands", "?"],
                "shortcuts": {
                    "hsquared": "help help"
                },
                "func": consolecommands.help
            },
            "say": {
                "description": "Says something in a channel.",
                "syntax": "[channel] [message]",
                "aliases": ["send"],
                "shortcuts": {
                    "debug": "send 804505336430067763"
                },
                "func": consolecommands.say
            },
            "eval": {
                "description": "Evaluates code.",
                "syntax": "[code]",
                "aliases": ["exec"],
                "func": consolecommands.eval_
            },
            "reload": {
                "description": "Reloads the bot.",
                "syntax": "(force)",
                "shortcuts": {
                    "fr": "reload force",
                    "r": "reload"
                },
                "func": consolecommands.reload
            }
        }

        self.parent = parent

    async def run(
            self,
            command: str
        ):

        await self.wrap(self.run_(command))

    async def run_(
            self,
            content: str
        ):

        # Read self.current
        run = True
        args = content.strip().split(" ")

        valid = False
        if len(args) > 0:
            for arg in args:
                if arg.strip() != "":
                    valid = True
                    break

        if not valid:
            await self.send(1, f"No command specified! Run 'help' for a list of commands.", True)
            run = False

        # Search for this command
        if run:
            command_name = args[0].lower()

            if command_name.startswith("/") and hasattr(humecord.bot.config, "minecaft"):
                command = (" ".join(args))[1:]

                async with MinecraftClient(humecord.bot.config.minecaft["host"], humecord.bot.config.minecaft["port"], humecord.bot.config.minecaft["pass"]) as mc:
                    out = await mc.send(command)

                    if out is None:
                        out = [""]

                    if out == "":
                        out = [f"{colors.termcolors['yellow']}No response."]

                    else:
                        out = out.strip().split("\n")

                    for msg in out:
                        rem = []
                        for i, char in enumerate(msg):
                            if char == "§":
                                rem.append(i)

                        offset = 0
                        for num in rem:
                            num -= offset

                            msg = msg[:num] + msg[num + 2:]
                            offset += 2

                        await self.send(0, re.sub(ansi_escape, "", msg))

            else:
                match = None
                for name, command in self.commands.items():
                    if (command_name == name):
                        # This command matches directly
                        match = name
                        details = command
                        break

                    elif ( # Only check if aliases are enabled for this command
                        command_name in command["aliases"]
                        if "aliases" in command
                        else False
                    ):
                        match = name
                        details = command
                        break

                    elif (
                        command_name in command["shortcuts"]
                        if "shortcuts" in command
                        else False
                    ):
                        # Matched to a shortcut
                        match = name
                        details = command

                        # Insert args
                        args = details["shortcuts"][command_name].split(" ") + args[1:]
                        break

                if match is None:
                    await self.send(1, f"Invalid command: '{command_name}'. Run 'help' for a list of commands.", True)

                else:
                    await command["func"](self, args)

        humecord.terminal.log(" ")
        self.parent.history.append(str(content))
        #self.parent.current = ""
        self.parent.hist_current = None
        humecord.terminal.reprint(log_logs = True, log_console = True)

    async def send(
            self,
            code,
            messages,
            bold: bool = False,
            done: bool = False
        ):

        if type(messages) != list:
            messages = [messages]

        if code == 0: # OK
            for line in messages:
                humecord.terminal.log(f"  {humecord.terminal.color['response']}{colors.termcolors['bold']}→ {colors.termcolors['reset']}{humecord.terminal.color['response']}{colors.termcolors['bold'] if bold else ''} {line}")

        elif code == 1: # Error
            for line in messages:
                humecord.terminal.log(f"  {colors.termcolors['red']}{colors.termcolors['bold']}→ {colors.termcolors['reset']}{colors.termcolors['red']}{colors.termcolors['bold'] if bold else ''} {line}")

    async def syntax(
            self,
            command: str
        ):

        cmd = self.commands[command]

        await self.send(1, "Invalid syntax!", True)
        await self.send(1, f"{command}{(' ' + cmd['syntax']) if 'syntax' in cmd else ''}")

    async def wrap(
            self,
            coro
        ):

        try:
            await coro

        except:
            debug.print_traceback("Run terminal command")