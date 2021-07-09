from ..utils import exceptions

class ArgumentParser:
    def __init__(
            self,
            extra_rules: dict
        ):
        """
        Constructs an ArgumentParser.
        """


        self.rules = {
            **extra_rules
        }

    async def recursive_compile(
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
        checks, groups = await self.compile(
            parsestr
        )

        check_comp = []

        # Check if checks should be processed too
        for check in checks:
            if "&&" in check or "||" in check:
                check_comp.append(await self.recursive_compile(
                    check
                ))

            else:
                check_comp.append(check)

        return {
            "checks": check_comp, 
            "groups": groups
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

            """after = 0
            before = len(parsestr) - 1
            par = parsestr.find("(")
            if par != -1:
                # Check for separator after 2nd
                # Can be nested - so we want the last one before next sep
                sep = None
                for name in separators:
                    location = parsestr.find(name, after, before)

                    if location != -1:
                        if sep is None:
                            sep = location

                        else:
                            if location < sep:
                                sep = location

                # Try to find closing between 0 and separator
                closing = -1

                i = sep
                for char in reversed(parsestr[:sep]):
                    i -= 1

                    print(char, i)

                    if char == ")":
                        closing = i
                        break

                if closing == -1:
                    raise exceptions.InvalidRule("Unmatched '('")

                # If ( is index 0, search for separator after )
                # Otherwise, search for separator before (
                
                if par == 0:
                    after = closing

                else:
                    before = par

            for name in separators:
                location = parsestr.find(name, after, before)

                if location != -1:
                    separators[name] = location
            """

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

        return checks, groups

    async def is_valid(
            self,
            rules: dict,
            istr: str,
            data: dict
        ):
        """
        Automatically validates something,
        and returns any errors as a string.
        
        Arguments:
            rules: (dict, str) - Rules to validate.
                If this is a string, it'll be converted
                to a valid format.
            istr: (str) - Input to validate.
            data: (dict) - Data to pass along to the validator.

        Returns:
            error (str, None): Error. If this isn't None, the 
                input is invalid.    
        """

        if type(rules) != dict:
            rules = await self.compile_recursive(
                rules
            )

        # Validate it
        try:
            await self.validate(
                rules,
                istr,
                data
            )

        except Exception as e:
            return str(e)

    async def validate(
            self,
            rules: dict,
            istr: str,
            data: dict
        ):
        checked = {}

        results = []

        # Iterate over each group.
        for group in rules["groups"]:
            # See what we have to check
            if group["type"] == "solo":
                # Check the only arg
                if group["index"] not in checked:
                    # Check it
                    try:
                        checked[group["index"]] = {
                            "value": await self.check_rule(rules["checks"][group["index"]], istr, data)
                        }

                    except:
                        checked[group["index"]] = False

                # Append check result to results
                results.append(type(checked[group["index"]]) == dict)
                # (Valid only if result is a dict)

            elif group["type"] == "group":
                result = []
                check = {}
                # Check each index.
                for ind in group["groups"]:
                    if group["index"] not in checked:
                        # Check it
                        try:
                            checked[group["index"]] = {
                                "value": await self.check_rule(rules["checks"][group["index"]], istr, data)
                            }

                        except:
                            checked[group["index"]] = False

                    # Append check result to results
                    result.append(checked[group["index"]])

                # Check how we're comparing
                if group["check"] == "&&":
                    results.append(not (False in result)) # If there's a False in there, return False (invalid)

                elif group["check"] == "||":
                    results.append(True in result)

        # Check if any results are True
        return not (False in result), checked
            # If any check is False, the entire thing is invalid
            # Then, return the result list


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
            return await self.validate(
                rules,
                istr,
                str,
                data
            )

        else:
            # Run it through the one-time validator
            return await self.validate_one(
                rules,
                istr,
                str,
                data
            )

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
        for key, types in rule["data"].items():
            if key not in data:
                raise exceptions.MissingData(f"Missing key {key}")

            # Check type
            if type(types) == list:
                # Validate
                if type(data[key]) not in types:
                    raise exceptions.MissingData(f"Key {key} is of wrong type")

        # First, we have to parse it against the rule type
        value = await rule["main"](istr, **data)

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
            for i, req_types in enumerate(func_data["args"]):
                if len(funcargs) - 1 < i:
                    # Not included
                    raise exceptions.InvalidRule(f"Function {func} requires {len(func_data['args'])} arguments")

                # Check type
                if type(req_types) == list:
                    # Validate
                    if type(funcargs[i]) not in req_types:
                        raise exceptions.MissingData(f"Function {func}'s {i}-index arg is of wrong type")

            # Run it
            result = await func_data["function"](value, funcargs, **data)

            if result is not None:
                value = result

        # Value is good - return result
        return value
