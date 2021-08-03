from blessed import Terminal
import tty
import termios
import signal
from unidecode import unidecode
import os
import re


from humecord.utils import (
    colors,
    consolecommands
)

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

class TerminalManager:
    def __init__(
            self
        ):
        global humecord
        import humecord

        self.terminal = Terminal()
        tty.setcbreak(self.terminal._keyboard_fd, termios.TCSANOW)
        print(self.terminal.enter_fullscreen)
        print(self.terminal.home + self.terminal.clear)

        self.lines = []

        self.color = {
            "border": "default",
            "info": "cyan",
            "secondary": "dark_gray",
            "terminal": "green",
            "response": "cyan",
            "remote": "magenta"
        }

        self.color = {
            x: colors.termcolors[y] for x, y in self.color.items()
        }

        signal.signal(signal.SIGWINCH, self.on_resize)

        self.location = 0
        self.manual_scroll = False
        self.line_numbers = True

        self.on_resize()

        self.colors = colors.termcolors.values()

    def finish_start(
            self
        ):

        self.color.update(
            {
                x: colors.termcolors[y] for x, y in humecord.bot.config.terminal_colors.items()
            }
        )

        self.line_numbers = humecord.bot.config.line_numbers

        self.reprint(True)

        consolecommands.prep()

    def close(
            self
        ):

        print(self.terminal.exit_fullscreen)
        print(self.terminal.move_x(0))

        os.system("stty sane")

    def on_resize(
            self,
            *args
        ):

        if not self.manual_scroll and hasattr(self, "log_count"):
            self.location = len(self.lines) - self.log_count

            if self.location < 0:
                self.location = 0

        self.log_count = self.terminal.height - 7

        self.reprint(True)

    def log(
            self,
            message,
            update: bool = False
        ):

        self.lines.append(message)

        if not self.manual_scroll:
            self.location = len(self.lines) - self.log_count

            if self.location < 0:
                self.location = 0

        if update:
            self.reprint(log_logs = True)

    def reprint(
            self,
            needs_relog: bool = False,
            log_title: bool = False,
            log_logs: bool = False,
            log_console: bool = False
        ):
        if needs_relog:
            print(self.terminal.clear)
            self.draw_box()
            self.draw_title()
            self.draw_logs()
            self.draw_console()
        
        if log_title:
            self.draw_title()

        if log_logs:
            self.draw_logs()

        if log_console:
            self.draw_console()

    def draw_box(
            self
        ):
        self.log_box(1, 0)

        with self.terminal.location(0, 2):
            print(self.gen_box_mid(""))

        self.log_box(3, 1)

        print(self.terminal.move_y(2))
        for i in range(0, self.terminal.height - 7):
            print(self.terminal.move_down(1) + self.terminal.move_x(0) + self.gen_box_mid(""), end = "")

        self.log_box(self.terminal.height - 3, 1)

        with self.terminal.location(0, self.terminal.height - 2):
            print(self.gen_box_mid(""))

        self.log_box(self.terminal.height - 1, 2)

    def draw_title(
            self
        ):
        with self.terminal.location(2, 2):
            if humecord.init_finished:      
                print(self.center(f"{self.color['info']}{colors.termcolors['bold']}{humecord.bot.config.cool_name} {colors.termcolors['reset']}{self.color['info']}v{humecord.bot.config.version} (humecord {humecord.version})"), end = "")

            else:
                print(self.center(f"{colors.termcolors['cyan']}{colors.termcolors['bold']}Humecord is initializing..."), end = "")

    def draw_console(
            self
        ):

        try:
            if hasattr(humecord.bot, "console"):
                with self.terminal.location(0, self.terminal.height - 2):
                    print(self.gen_box_mid(f"{self.color['terminal']}{colors.termcolors['bold']}${colors.termcolors['reset']} {self.color['terminal']}{humecord.bot.console.current}", True), end = "")

        except AttributeError:
            pass # Not initialized yet

        else:
            print(self.terminal.move_xy(4 + humecord.bot.console.location, self.terminal.height - 3))

    def draw_logs(
            self
        ):
        
        scrollbar = self.gen_scrollbar()

        # Get line set
        cl = len(self.lines)
        for i in range(0, self.terminal.height - 7):
            i_ = i + self.location
            if i_ < cl:
                try:
                    with(self.terminal.location(0, i + 4)):
                        line = self.lines[i_].replace("\t", "    ")

                        line_numbers = False
                        if self.terminal.width < 80:
                            line = line.strip()
                        
                        else:
                            line_numbers = True

                        ext = ""
                        
                        if self.line_numbers and (line_numbers):
                            if line.strip() != "":
                                ext = f"{self.color['secondary']}{i_ + 1} "
                                line_numbers = True

                        stripped = re.sub(ansi_escape, "", line)

                        bounds = self.terminal.width - 3 - (2 if line_numbers else 0) - len(ext) + (len(line) - len(stripped))

                        print(self.gen_box_mid(f"{ext}{line[:bounds]}{self.terminal.move_x(self.terminal.width - 3)}{self.color['info']}{scrollbar[i]}", True))

                except Exception as e:
                    humecord.bot.console.current = str(e)
                    self.reprint(log_console = True)

    def gen_scrollbar(
            self
        ):

        block = "█"
        empty = "░"

        height = self.terminal.height - 7

        # Find out how much of the terminal we're viewing
        lines = len(self.lines)
        if lines == 0:
            ll = 1

        else:
            ll = lines

            if ll <= 0:
                ll = 1

        percent = height / ll

        if percent > 1:
            percent = 1

        # Multiply that percent by the total line count to determine chars
        chars = int(percent * height)

        if chars == 0:
            chars = 1

        # Find terminal location by percentage
        location_percent = self.location / ll

        # Scale it to the total line count to get a location
        bar_start = int(location_percent * height)

        # Compile to a string
        bar = f"{empty * bar_start}{block * (chars + 1)}{empty * (height - bar_start - chars - 1)}"

        return bar

        for i, char in enumerate(bar):
            #with self.terminal.location(i + 4, self.terminal.width - 3):
            print(f"{self.terminal.move_y(i + 4)}{self.terminal.move_x(self.terminal.width - 3)}{self.color['info']}{char}", end = "")

    def center(
            self,
            message: str
        ):

        stripped = len(re.sub(ansi_escape, "", message))

        message = message[:(self.terminal.width - 4 + len(message) - stripped)]

        padding = ((self.terminal.width - 4) - stripped) // 2

        return f"{' ' * padding}{message}{' ' * padding}"

    def clear(
            self,
            message: str
        ):

        w = self.terminal.width - 4

        message = message[:w]

        return f"{message}{'-' * (w - len(message))}"

    def getch(
            self,
            timeout: int = 1
        ):

        return self.terminal.inkey(timeout = timeout)

    def log_box(
            self,
            line: int,
            border: int
        ):

        chars = box_chars[border]

        with self.terminal.location(0, line):
            print(f"{self.color['border']}{chars[0]}{chars[1] * (self.terminal.width - 2)}{chars[2]}", end = "")

    def gen_box_mid(
            self,
            msg,
            clear: bool = False
        ):

        if clear:
            print(self.terminal.clear_eol + self.terminal.move_up(1) + self.terminal.move_x(0))
            #print((" " * (self.terminal.width - 1)) + self.terminal.move_x(0))

        return f"{self.color['border']}│ {colors.termcolors['reset']}{msg}{self.terminal.move_x(self.terminal.width - 2)} {self.color['border']}│"

    def scroll(
            self,
            change: int
        ):

        max_scroll = len(self.lines) - self.log_count + 1

        # Check if trying to scroll beyond bottom
        if self.location + change >= max_scroll:
            self.manual_scroll = False
            return

        # Check if trying to scroll above top
        if self.location + change < 0:
            return

        # Change location
        self.location += change

        # Check if we're at the bottom
        if self.location >= max_scroll:
            # Set to max
            self.location = max_scroll
            # Enable autoscroll
            self.manual_scroll = False

        # Otherwise, don't autoscroll to bottom on new line
        else:
            self.manual_scroll = True

        if not self.manual_scroll:
            self.location = len(self.lines) - self.log_count

            if self.location < 0:
                self.location = 0

        # Relog
        self.reprint(log_logs = True)

    def log_action(
            self,
            action: str
        ):

        self.log(f"{humecord.terminal.color['terminal']}{colors.termcolors['bold']}>{colors.termcolors['reset']} {humecord.terminal.color['terminal']}{action}", True)
        


box_chars = {
    0: ["┌", "─", "┐"],
    1: ["├", "─", "┤"],
    2: ["└", "─", "┘"]
}