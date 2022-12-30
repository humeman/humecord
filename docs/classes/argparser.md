### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/argparser

---
# argparser

class: `humecord.classes.argparser.ArgumentParser`

instance: `humecord.bot.args`

---
This class manages the execution and preparation of argument parsing rules.

It does not contain any of the rules themselves; only references to them. For a complete list of rules, visit [docs/misc/argparser](../misc/argparser.md).

## outline
* **.rules**

    A dictionary containing all rules to be compiled.
* **async .compile_recursive(parsestr: str)**

    Compiles an argument rule string into a readable object, recursively. 

    *Returns:*
    - `argule` (dict) - compiled argument rule
* **async .compile(parsestr: str)**

    Compiles a single rule, non-recursively.

    *Returns:*
    - `checks`
    - `groups`
    - `ret`
* **async .parse(rules: dict|str, istr: str, data: dict)**

    Parses and validates an input string based on the specified rules.

    *Arguments:*
    - `rules`: A compiled rule dict (from recursive_compile) or an uncompiled string to check based on.
    - `istr`: Input string to validate.
    - `data`: Dict of required data to pass to parser/validator.
    
    *Returns:*
    - `valid` (bool): Whether parsing succeeded or not
    - `value`: If valid, the actual parsed value -- otherwise, a list of errors

* **async .validate(rules: dict, istr: str, data: dict)**

    Parses and validates an input string based on the specified rules.
    Identical to `.parse()`, but does not allow for an uncompiled input rule.

    *Arguments:*
    - `rules`: A compiled rule dict (from recursive_compile) or an uncompiled string to check based on.
    - `istr`: Input string to validate.
    - `data`: Dict of required data to pass to parser/validator.
    
    *Returns:*
    - `valid` (bool): Whether parsing succeeded or not
    - `value`: If valid, the actual parsed value -- otherwise, a list of errors
* **async .format(rules: dict, istr: str, data: dict)**

    Formats a value into a human-readable string via the specified rule type.

    *Arguments:*
    - `rule`: Rule type only (ex: str, int, etc.)
    - `value`: Value to format to specified rule type.
    - `data`: Dict of extra data to use as necessary.

    *Returns:*
    - `formatted`: Formatted string.

    *Raises:*
    - `MissingData`: Missing data in `data` dict
    - `InvalidRule`: Rule type does not exist
* **async .format_rule(rule: dict)**

    Formats a compiled/uncompiled rule into a human-readable string.

    *Arguments:*
    - `rule`: Rule dict/str.

    *Returns:*
    - `formatted`: Formatted string.

    *Raises:*
    - `InvalidRule`: Rule is invalid
* **async .dissect(rule: str)**

    Parses an input rule string, returning its type and args separately.
    
    *Arguments:*
    - `rule`: Rule str

    *Returns:*
    - `rtype`: Rule type used.
    - `args`: List of args passed to the rule.

    *Raises:*
    - `InvalidRule`: Rule is invalid
* ~~**async .check_rule(rules: dict, istr: str, data: dict)**~~

    *Deprecated*: Use `.parse()`.

    Checks an input against the specified rules (str/dict).
* ~~**async .validate_once(rules: dict, istr: str, data: dict)**~~

    *Deprecated*: Use `.parse()`.

    Checks an input against the specified rules (dict).
* ~~**async .validate_one(rules: dict, istr: str, data: dict)**~~

    *Deprecated*: Use `.parse()`.

    Checks an input against the specified rules (str).


