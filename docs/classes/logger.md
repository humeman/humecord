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
* **.get_placeholders(category: str, log_type: str, message: str, bold, reversed, color, remove_blank_lines, extra_line)**

    Gets the default placeholders with the specified arguments.

    *Returns:*
    - `placeholders`: Dict of placeholder name/values.

* **.log(category: str, log_type: str, message: str, \*bold: bool = False, \*reversed: bool = False, \*color: str = None, \*placeholder_ext: dict = {})**

    Logs something in the standard format.

    *Params:*
    - `category` (str): Category to log into
    - `log_type` (str): Log type to use (info, warn, error, etc.). Defines the style of the message.
    - `message` (str): Message to log
    - `bold` (bool = False): Whether to bold the message
    - `reversed` (bool = False): Whether to display the message on reversed text
    - `color` (str): Color to log the line in (normal terminal color names - see [utils.colors](../utils/colors.md))
    - `placeholder_ext` (dict[str, Any]): Extra placeholders to use

* **.log_step(category, log_type, message, \*bold: bool = False, \*reversed: bool = False, \*color: str = None, \*placeholder_ext: dict = {})**

    Logs something as a sublog of another log (indented, arrow prefix).

    *Params:*
    - `category` (str): Category to log into
    - `log_type` (str): Log type to use (info, warn, error, etc.). Defines the style of the message.
    - `message` (str): Message to log
    - `bold` (bool = False): Whether to bold the message
    - `reversed` (bool = False): Whether to display the message on reversed text
    - `color` (str): Color to log the line in (normal terminal color names - see [utils.colors](../utils/colors.md))
    - `placeholder_ext` (dict[str, Any]): Extra placeholders to use

* **.log_long(category: str, log_type: str, messages: list[str]|str, \*bold: bool = False, \*reversed: bool = False, \*color: str = None, \*placeholder_ext: dict = {})**

    Logs a long message by line. Either splits by linebreak (\\n) or sends a list of message strings.

    *Params:*
    - `category` (str): Category to log into
    - `log_type` (str): Log type to use (info, warn, error, etc.). Defines the style of the message.
    - `message` (str): Message to log
    - `bold` (bool = False): Whether to bold the message
    - `reversed` (bool = False): Whether to display the message on reversed text
    - `color` (str): Color to log the line in (normal terminal color names - see [utils.colors](../utils/colors.md))
    - `remove_blank_lines` (bool = False): Whether to remove any line left blank
    - `extra_line` (bool = False): Whether to print an extra blank line afterward


* **.log_raw(category: str, log_type: str, messages: list[str]|str, \*bold: bool = False, \*reversed: bool = False, \*color: str = None, \*placeholder_ext: dict = {})**

    Logs a message without any editing.

    *Params:*
    - `category` (str): Category to log into
    - `log_type` (str): Log type to use (info, warn, error, etc.). Defines the style of the message.
    - `message` (str): Message to log
    - `bold` (bool = False): Whether to bold the message
    - `reversed` (bool = False): Whether to display the message on reversed text
    - `color` (str): Color to log the line in (normal terminal color names - see [utils.colors](../utils/colors.md))
    - `placeholder_ext` (dict[str, Any]): Extra placeholders to use

* **.log_ask(message: str, hint: str)**

    Logs an input question's message and hint to the terminal.

    *Params:*
    - `message` (str): Question
    - `hint` (str): Placeholder text to enter into terminal