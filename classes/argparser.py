from ..utils import (
    exceptions,
    debug,
    argrules
)

from typing import Union

class ArgumentParser:
    def __init__(
            self,
            extra_rules: dict
        ):
        """
        Constructs an ArgumentParser.
        """

        self.rules = {
            **argrules.rules,
            **extra_rules
        }

    async def compile_recursive(
            self,
            parsestr: str
        ):
        """
        Converts a parse string into an ArgumentParser-readable
        object, recursively.

        This allows for nested statements, using parenthesis.

        Arguments:
            parsestr (str): String to compile
        """

        # Strip leading & trailing (
        parsestr = parsestr.strip()
        count = 0
        for i, char in enumerate(parsestr):
            if char == "(":
                count += 1

            elif char == ")":
                count -= 1

            if count == 0:
                if i != len(parsestr) - 1:
                    break # Don't strip - parenthesis are matched, and string continues

                else:
                    # Unecessary parenthesis - strip them
                    parsestr = parsestr[1:-1]
                    break

        # Parse the current string
        checks, groups, ret = await self.compile(
            parsestr
        )

        check_comp = []

        # Check if checks should be processed too
        for check in checks:
            if "&&" in check or "||" in check:
                check_comp.append(await self.compile_recursive(
                    check
                ))

            else:
                check_comp.append(check)

        return {
            "checks": check_comp, 
            "groups": groups,
            "ret": ret
        }

    async def compile(
            self,
            parsestr: str
        ):
        """
        Converts a parse string into an ArgumentParser-readable
        object.
        
        Arguments:
            parsestr (str): String to compile
        """

        # Final desired format:
        """
        [
            ParseRule(),
            [
                ParseRule()
            ]
        ]
        """

        # 1. Create a list of rule groups
        # Groups will reference them by index, so we don't check multiple times for comparisons.
        groups = []
        checks = []


        # - See if there's a separator anywhere - while there
        #   is one, take the thing immediately after & before,
        #   and create a group out of it
        while True:
            separators = {
                "&&": None,
                "||": None
            }

            # Strip it, before we check stuff
            parsestr = parsestr.strip()

            # Check if there's a ( in this parsestr
            # - Iterate over each character, start to finish
            #   Count the number of (
            #   Each time we encounter a ), subtract one
            #   If total is 0 (excluding start) and we're at a sep, we're good
            #   Take everything in between

            ret = 0
            count = 0
            sep = None
            for i, char in enumerate(parsestr):
                if char == "(":
                    count += 1

                elif char == ")":
                    count -= 1

                if count == 0:
                    # Check if there's a separator **directly** after
                    after = parsestr[i + 1:]
                    i_ = 0
                    real_i = i + 1
                    for char_ in after:
                        curr = after[i_:i_+2]
                        if curr in separators:
                            # Good - this is our separator
                            separators[curr] = real_i
                            # Tell not to search for sep
                            sep = curr
                            break

                        i_ += 1
                        real_i += 1

                    if sep is None:
                        # sep should be defined by now - we finished the loop
                        # This means the rest should be treated as its own thing.
                        # Don't define anything, just break.
                        break
                        #raise exceptions.InvalidRule(f"Expected ' ' or separator, not '{char_}' at index {i_}")


                if sep is not None:
                    break

            # Find the bounds that we should split at.
            location = None
            next_ = None
            check = None
            for name, value in separators.items():
                if value is not None:
                    # Don't do it yet if it's after the current group.
                    if location is not None:
                        if value > location:
                            # So we have our bounds, save where the next separator is
                            if next_ is not None:
                                if next_ < value: # If it's already defined, only do it if it's before the old "next" location
                                    next_ = value

                            else:
                                # Just set it - it's not defined yet
                                next_ = value

                            continue

                    location = value
                    check = name

            # Check if we found anything.
            if location is None:
                # Check if we have to add it to groups (if there are no other groups).
                if len(groups) == 0:
                    groups.append(
                        {
                            "type": "solo", # One comparison
                            "index": len(checks) # The last (and only, in this case) check in the list
                        }
                    )

                # Check if we want to save the data for this check
                if parsestr.startswith("@"):
                    parsestr = parsestr[1:]
                    ret = len(checks)

                # Append the check
                checks.append(
                    parsestr
                )

                break # Done!

            else:
                # Split it at the found separator.

                # Sample: test&&another
                # location = 4
                # before: parsestr[:4] = "test"
                # after: parsestr[6:] = "another"

                before = parsestr[:location]
                after = parsestr[location + 2:]

                # Check if we want to save the data for this check
                if before.startswith("@"):
                    before = before[1:]
                    ret = len(checks)

                # Add the current group
                groups.append(
                    {
                        "type": "group",
                        "check": check,
                        "groups": [len(checks), len(checks) + 1] # Current index and whatever's after - second will be added on next iteration
                    }
                )

                # Add the current check (only "before")
                checks.append(
                    before
                )

                # Prep parsestr for next iteration
                parsestr = after

        return checks, groups, ret

    async def parse(
            self,
            rules: Union[dict, str],
            istr: str,
            data: dict
        ):
        """
        Automatically validates something,
        and returns either errors or a parsed value.
        
        Arguments:
            rules: (dict, str) - Rules to validate.
                If this is a string, it'll be converted
                to a valid format.
            istr: (str) - Input to validate.
            data: (dict) - Data to pass along to the validator.

        Returns:
            valid (bool) - Whether or not the data is valid
            value - Value returned from validator
                If valid: The actual parsed value
                Else: A list of errors (failed checks) 
        """

        if type(rules) != dict:
            rules = await self.compile_recursive(
                rules
            )

        # Validate it
        return await self.validate(
            rules,
            istr,
            data
        )

    async def validate(
            self,
            rules: dict,
            istr: str,
            data: dict
        ):
        checked = {}

        results = []

        errors = []

        final_value = None

        # Iterate over each group.
        for group in rules["groups"]:
            # See what we have to check
            if group["type"] == "solo":
                # Check the only arg
                if group["index"] not in checked:
                    # Check it
                    valid, value = await self.check_rule(rules["checks"][group["index"]], istr, data)

                    if valid:
                        # Check if this is the result we should return
                        if rules["ret"] == group["index"] or final_value is None:
                            # Set value
                            final_value = value

                        checked[group["index"]] = {
                            "valid": True,
                            "value": value
                        }
                        results.append(True)

                    else:
                        errors.append(value)
                        checked[group["index"]] = {
                            "valid": False
                        }
                        results.append(False)

            elif group["type"] == "group":
                result = []
                check = {}
                # Check each index.
                for ind in group["groups"]:
                    if ind not in checked:
                        # Check it
                        valid, value = await self.check_rule(rules["checks"][ind], istr, data)

                        if valid:
                            if rules["ret"] == ind:
                                # Set value
                                final_value = value

                            # Check if this is the result we should return
                            if rules["ret"] == ind or final_value is None:
                                # Set value
                                final_value = value

                            checked[ind] = {
                                "valid": True,
                                "value": value
                            }
                            result.append(True)

                        else:
                            errors.append(value)
                            checked[ind] = {
                                "valid": False
                            }

                            result.append(False)


                        """
                        try:
                            value = await self.check_rule(rules["checks"][ind], istr, data)

                            # Check if this is the result we should return
                            if rules["ret"] == ind:
                                # Set value
                                final_value = value

                            checked[ind] = {
                                "value": value
                            }

                            result.append(True)

                        except:
                            debug.print_traceback()

                            checked[ind] = {
                                "valid": False
                            }

                            result.append(False)
                        """

                # Check how we're comparing
                if group["check"] == "&&":
                    results.append(not (False in result)) # If there's a False in there, return False (invalid)

                elif group["check"] == "||":
                    results.append(True in result)

        # Check if any results are True
        valid = not (False in results)
        if valid:
            return True, final_value

        else:
            return False, errors
            # If any check is False, the entire thing is invalid
            # Then, return the chosen result


    async def check_rule(
            self,
            rules: dict,
            istr: str,
            data: dict
        ):

        # Either a string or dict can be passed as rules.
        # If it's a string, forward it to validate_one.
        # If it's a dict, forward it to validate().
        if type(rules) == dict:
            # Run it through the dict validator
            return (await self.validate(
                rules,
                istr,
                data
            ))[:2]

        else:
            # Run it through the one-time validator
            try:
                val = await self.validate_one(
                    rules,
                    istr,
                    data
                )

                return True, val

            except exceptions.InvalidData as e:
                return False, str(e)

    async def validate_once(
            self,
            rule: str,
            istr: str,
            data: dict
        ):

        # Compile into rule
        rules = await self.compile_recursive(
            rule
        )

        # Validate
        return await self.validate(
            rules,
            istr,
            data
        )

    async def validate_one(
            self,
            rulestr: str,
            istr: str,
            data: dict
        ):

        # First, find the type.
        if "[" in rulestr:
            # Type is everything before that.
            rtype, args = rulestr.split("[", 1)
            # Strip the final "]" on args.

            if args[-1] != "]":
                raise exceptions.InvalidRule("Unmatched '['")

            args = args[:-1]

            # Split the args
            args = args.split("&")

        else:
            # Entire thing is a rule. No args.
            rtype = rulestr
            args = []

        # Lower rule
        rtype = rtype.lower()

        # Check if it exists
        if rtype not in self.rules:
            raise exceptions.InvalidRule(f"Rule type {rtype} doesn't exist")

        # Get rule
        rule = self.rules[rtype]

        # Make sure we have all the data we need.
        comp_data = {}
        for key, types in rule["data"].items():
            if key not in data:
                raise exceptions.MissingData(f"Missing key {key}")

            # Check type
            if type(types) == list:
                # Validate
                if type(data[key]) not in types:
                    raise exceptions.MissingData(f"Key {key} is of wrong type")

            comp_data[key] = data[key]

        # First, we have to parse it against the rule type
        value = await rule["main"](istr, **comp_data)

        # Then, run all the arg functions
        for arg in args:
            if "(" in arg:
                # Split at (
                func, funcargs = arg.split("(", 1)
                func, funcargs = func.strip(), funcargs.strip()

                if funcargs[-1] != ")":
                    raise exceptions.InvalidRule(f"Unmatched ')' for arg {arg}")

                # Strip out )
                funcargs = funcargs[:-1].split(",")

            else:
                func = arg.strip()
                funcargs = []

            # Lower func
            func = func.lower()

            # Check if it exists
            if func not in rule["functions"]:
                raise exceptions.InvalidRule(f"Function {func} doesn't exist for rule type {rtype}")

            # Get func data
            func_data = rule["functions"][func]

            # Check if we have proper arg count
            if "args" in func_data:
                for i, req_types in enumerate(func_data["args"]):
                    if len(funcargs) - 1 < i:
                        # Not included
                        raise exceptions.InvalidRule(f"Function {func} requires {len(func_data['args'])} arguments")

                    # Check type
                    if type(funcargs[i]) not in req_types:
                        try:
                            funcargs[i] = req_types[0](funcargs[i])

                        except:
                            raise exceptions.MissingData(f"Function {func}'s {i}-index arg is of wrong type")

            if "arg_types" in func_data:
                # Make sure everything is this type
                for i, arg in enumerate(funcargs):
                    if type(arg) not in func_data["arg_types"]:
                        try:
                            funcargs[i] = func_data["arg_types"][0](funcargs[i])

                        except:
                            raise exceptions.MissingData(f"Function {func}'s {i}-index arg is of wrong type")

            # Run it
            result = await func_data["function"](value, funcargs, **comp_data)

            if result is not None:
                value = result

        # Value is good - return result
        return value

    async def format(
            self,
            rule: str,
            value,
            data: dict
        ):

        # Find if rule exists
        if rule not in self.rules:
            raise exceptions.InvalidRule(f"Rule type {rule} doesn't exist")

        rule = self.rules[rule]

        # Get all data
        func_data = {}
        for key, types in rule["format"]["data"].items():
            if key not in data:
                raise exceptions.MissingData(f"Missing key {key}")

            # Check type
            if type(types) == list:
                # Validate
                if type(data[key]) not in types:
                    raise exceptions.MissingData(f"Key {key} is of wrong type")

            func_data[key] = data[key]

        # Run formatter
        return await rule["format"]["function"](
            value,
            **data
        )