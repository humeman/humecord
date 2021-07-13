from humecord.utils import (
    exceptions
)

from humecord.utils.exceptions import InvalidData as IE

import re



class ParseStr:
    async def main(
            inp
        ):

        try:
            inp = str(inp)

        except:
            raise IE(f"Unable to convert to string")

        return inp

    async def len(
            inp,
            args
        ):
        l = len(inp)

        if l < args[0] or l > args[1]:
            raise IE(f"Value's length isn't within bounds: {args[0]} to {args[1]}")

    async def includes(
            inp,
            args
        ):

        inp = inp.lower()

        for arg in args:
            arg = arg.lower()

            if arg in inp:
                return

        raise IE(f"Value doesn't include any of required words: {', '.join(args)}")

    async def alnum(
            inp,
            args
        ):

        if not inp.replace("-", "").replace("_", "").isalnum():
            raise IE("Value isn't alphanumeric")

    async def in_(
            inp,
            args
        ):

        args = [x.lower() for x in args]

        if inp.lower() not in args:
            raise IE(f"Value isn't one of required phrases: {', '.join(args)}")
    
    async def regex(
            inp,
            args
        ):

        for arg in args:
            if not re.match(arg, inp):
                raise IE(f"Value failed regex check: {arg}")

    async def format(
            inp
        ):

        return str(inp)

class ParseInt:
    async def main(
            inp
        ):

        try:
            inp = int(inp)

        except:
            raise IE(f"Unable to convert to int")

        return inp

    async def between(
            inp,
            args
        ):

        if inp < args[0] or inp > args[1]:
            raise IE(f"Value is outside of bounds: {args[0]} to {args[1]}")

    async def less(
            inp,
            args
        ):

        if inp >= args[0]:
            return IE(f"Value isn't less than {args[0]}")

    async def greater(
            inp,
            args
        ):

        if inp <= args[0]:
            return IE(f"Value isn't greater than {args[0]}")

    async def format(
            inp
        ):

        return str(inp)

# Argument rules
# Imported by the argument parser on init.
rules = {
    "str": {
        "main": ParseStr.main,
        "functions": {
            "len": {
                "function": ParseStr.len,
                "args": [[int], [int]]
            },
            "includes": {
                "function": ParseStr.includes,
                "arg_types": [str]
            },
            "alnum": {
                "function": ParseStr.alnum
            },
            "in": {
                "function": ParseStr.in_,
                "arg_types": [str]
            },
            "regex": {
                "function": ParseStr.regex,
                "arg_types": [str]
            }
        },
        "data": {},
        "format": {
            "data": {},
            "function": ParseStr.format
        }
    },
    "int": {
        "main": ParseInt.main,
        "functions": {
            "between": {
                "function": ParseInt.between,
                "args": [[int], [int]]
            },
            "less": {
                "function": ParseInt.less,
                "args": [[int]]
            },
            "greater": {
                "function": ParseInt.greater,
                "args": [[int]]
            }
        },
        "data": {},
        "format": {
            "data": {},
            "function": ParseInt.format
        }
    }
}