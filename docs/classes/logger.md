### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/logger

---
# logger

class: `humecord.classes.logger.Logger`

instance: `humecord.bot.logger`

---
Manages logging to the console in the typical readable format.

## user documentation
Coming soon.

## types
**Categories**:
Passed into `category` in any of the below functions that necessitate it.
- request
- requestcontent
- loops
- start
- botinit
- stop
- shutdown
- unhandlederror
- cacheinfo
- command
- commandinfo
- config
- erroredrequest
- interaction
- events
- loader
- reply
- ws
- api
- subprocess
- user
- ask

**Log types:**
Passed into `log_type` in any of the below functions that necessitate it.
- info
- warn
- error
- success
- start
- stop
- close
- cmd
- int
- obj
- ask

## outline
* **.get_placeholders(category: str, log_type: str, message: str, bold, color, reversed)**

    Gets the default placeholders with the specified arguments.

    *Returns:*
    - `placeholders`: Dict of placeholder name/values.

* **.log(category: str, log_type: str, message: str, \*bold: bool = False, \*reversed: bool = False, \*color: str = None, \*placeholder_ext: dict = {})**

    Logs something in the standard format.

* **.log_step(category, log_type, message, \*bold: bool = False, \*reversed: bool = False, \*color: str = None, \*placeholder_ext: dict = {})**

    Logs something as a sublog of another log (indented, arrow prefix instead of time).

* **.log_long(category: str, log_type: str, messages: list[str]|str, \*bold: bool = False, \*reversed: bool = False, \*color: str = None, \*placeholder_ext: dict = {})**

    Logs a long message by line. Either splits by linebreak (\\n) or sends a list of message strings.

* **.log_raw(category: str, log_type: str, messages: list[str]|str, \*bold: bool = False, \*reversed: bool = False, \*color: str = None, \*placeholder_ext: dict = {})**

    Logs a message without any formatting.

* **.log_ask(message: str, hint: str)**

    Logs an input question's message and hint to the terminal.

* **.log_type(name: str, category: str, log_type: str, messages: list[str]|str, \*bold: bool = False, \*reversed: bool = False, \*color: str = None, \*placeholder_ext: dict = {})**

    Logs a message with the specified format. Use the above functions instead.