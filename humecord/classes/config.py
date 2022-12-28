from ..utils import fs
from ..utils import exceptions


import humecord

import os
import inspect
import sys
import traceback
import asyncio

class Config:
    def __init__(self):
        """
        Constructs a config object.

        Should only be called from classes.bot.Bot.__init__().
        """

        global logger
        from humecord import logger

    def load_globals(
            self
        ):
        """
        Loads global configuration values from
        the specified global config file.
        """

        self.raw_globals = fs.read_yaml(self.globals_path)

        self.globals = Globals(self)

        for key, value in self.raw_globals.items():
            setattr(self.globals, key, value)

    def load_lang(
            self
        ):
        """
        Loads global configuration values from
        the specified global config file.
        """

        self.lang = fs.read_yaml(self.lang_path)

    def load_messages(
            self
        ):
        """
        Loads global message defaults.
        """

        self.messages = fs.read_yaml(self.messages_path)

    def validate_all(
            self
        ):
        self.reserved = {
            "samples": {},
            "types": {}
        }

        for name, value in self.reserved.items():
            if hasattr(self, name):
                self.log_error("config", "Config", f"Config is using reserved keyword '{name}'. Please rename it.")

            setattr(self, name, value)

        check = {
            "config": self,
            "lang": self.lang,
            "globals": self.globals
        }

        #if self.use_api:
        #    check["endpoints"] = self.globals.endpoints

        for name, obj in check.items():
            if self.validate(obj, name) == False:
                return

    def validate(
            self,
            obj,
            cat: str
        ):
        """
        Validates all config options.
        """

        cat_name = f"{cat[0].upper()}{cat[1:]}"

        # Read config sample
        with open(f"{os.path.dirname(inspect.getfile(humecord))}/config/{cat}.default.yml", "r") as f:
            self.samples[cat] = f.read().split("\n")

        # Read config types
        self.types[cat] = fs.read_yaml(f"{os.path.dirname(inspect.getfile(humecord))}/config/{cat}.types.yml")

        # Parse
        for name, expected in self.types[cat].items():
            # Check conditionals
            if name.startswith("__") and name.endswith("__"):
                name = name.strip("__")

                if "[" in name:
                    # Split out args
                    condition, args = name.rsplit("]", 1)[0].split("[", 1)
                    args = args.split("&")

                else:
                    condition = name
                    args = []

                use = False
                if condition == "if":
                    for check in args:
                        var, sep = check.split(":", 1)

                        if type(obj) == dict:
                            if var not in obj:
                                self.log_error(cat, cat_name, f"{cat_name} file requires value '{var}' for validation, but it is not present.", var = var)

                            search = f"obj['{var}']"

                        else:
                            if not hasattr(obj, var):
                                self.log_error(cat, cat_name, f"{cat_name} file requires value '{var}' for validation, but it is not present.", var = var)
                            
                            search = f"obj.{var}"

                        # Exec it
                        try:
                            result = eval(f"{search} {sep}", locals())

                            if type(result) != bool:
                                raise "Result must be a boolean"

                        except:
                            self.log_error(cat, cat_name, f"Config validator could not evaluate: '{var}{sep}' in {cat_name}. Incompatible types?", tb = True)

                        if result:
                            use = True

                if use:
                    # Validate everything inside
                    for name_, value_ in expected.items():
                        if self.validate_item_feedback(obj, cat, cat_name, name_, value_) == False:
                            return False

            else:
                # Make sure variable is valid
                if self.validate_item_feedback(obj, cat, cat_name, name, expected) == False:
                    return False

    def validate_item_feedback(
            self,
            obj,
            cat,
            cat_name,
            name,
            expected
        ):
        
        if expected.startswith("!"):
            required = True
            expected = expected[1:].strip()

        else:
            required = False

        result = self.validate_item(obj, cat, cat_name, name, expected, required)

        if not result:
            self.log_error(cat, cat_name, f"Config value '{name}' is of invalid type (required: '{expected}')", var = name)
            return False

    def validate_item(
            self,
            obj,
            cat,
            cat_name,
            name,
            expected,
            required
        ):

        if type(obj) == dict:
            if name not in obj and required:
                self.log_error(cat, cat_name, f"{cat_name} file requires value '{name}' (type: '{expected}').", var = name)

        else:
            if not hasattr(obj, name) and required:
                self.log_error(cat, cat_name, f"{cat_name} file requires value '{name}' (type: '{expected}').", var = name)
            
            elif not required:
                # Populate with default value
                #setattr(self, )
                pass


        # Parse rule
        comp = []
        for rule in expected.split("||"):
            if "[" in rule:
                var_type, args = rule.rsplit("]", 1)[0].split("[", 1)
                args = args.split("&")

            else:
                var_type = rule
                args = []

            if var_type not in rules:
                self.log_error(cat, cat_name, f"Config validator asked for variable of type '{var_type}' in {cat} file, but I don't know how to parse that. Open an issue on GitHub.")

            try:
                if type(obj) == dict:
                    val = obj[name]

                else:
                    val = getattr(obj, name)

                comp.append(rules[var_type](cat, cat_name, self, val, args))

            except Exception as e:
                if type(e) == SystemExit:
                    return
                
                self.log_error(cat, cat_name, f"Config validator could not validate var '{name}' (type: '{expected}').", tb = True)
                
        return True in comp
        
    def log_error(
            self,
            cat,
            cat_name,
            message,
            tb = False,
            var = None
        ):

        logger.log("config", "error", "A config validation error occurred:", bold = True)
        logger.log_step("config", "error", message)
        print()

        if tb:
            logger.log_long("config", "error", traceback.format_exc())
            print()

        logger.log_step("config", "error", "Please correct it and restart.")

        # Find
        if var is not None:
            humecord.terminal.log(" ")
            humecord.terminal.log("\033[96m-- \033[1mHere's a sample for this config option:\033[0m\033[96m --\033[0m")
            #logger.log_step("Here's a sample for this config option:", "light_cyan", bold = True)

            for i, line in enumerate(self.samples[cat]):
                if line.startswith(f"{var}:"):
                    # Find everything before & after
                    comp = []
                    
                    # First, go above & look for comments
                    active = self.samples[cat][i - 1]
                    active_i = i - 1
                    while active.startswith("#"):
                        comp.append(active)
                        active_i -= 1
                        if active_i < 0:
                            active = ""

                        else:
                            active = self.samples[cat][active_i]

                    # Reverse comp
                    comp.reverse()

                    comp.append(f"\033[1m{line}") # Add actual line

                    # Find everything after
                    active = self.samples[cat][i + 1]
                    active_i = i + 1
                    while active.startswith(" "):
                        comp.append(active)

                        active_i += 1
                        if active_i > len(self.samples[cat]) - 1:
                            active = ""

                        else:
                            active = self.samples[cat][active_i]

                    for line in comp:
                        humecord.terminal.log(f"\033[96m{line}\033[0m")

        humecord.terminal.reprint(log_logs = True)

        #humecord.bot.loop.create_task(humecord.bot.shutdown("Config error", error_state = True))

        raise exceptions.InitError(f"Config validation error", traceback = False, log = False)

class Globals:
    def __init__(
            self,
            parent: Config
        ):
        """
        Initializes a global config object.
        """

        self.parent = parent

        # If we have the API enabled, load API endpoints
        if self.parent.use_api:
            self.endpoints = fs.read_yaml(self.parent.endpoint_path)

class ValidationRules:
    def _str(cat, cat_name, conf, var, args):
        return type(var) == str

    def _int(cat, cat_name, conf, var, args):
        return type(var) == int

    def _float(cat, cat_name, conf, var, args):
        return type(var) == float

    def _number(cat, cat_name, conf, var, args):
        return type(var) in [int, float]

    def _bool(cat, cat_name, conf, var, args):
        return type(var) == bool

    def _list(cat, cat_name, conf, var, args):
        if not type(var) == list:
            return False

        if len(args) == 0:
            return True

        for item in var:
            for rule in args:
                if rule not in rules:
                    conf.log_error(cat, cat_name, f"Config validator asked for variable of type '{rule}', but I don't know how to parse that. Open an issue on GitHub.")

                if not rules[rule](cat, cat_name, conf, item, []):
                    return False

        return True

    def _dict(cat, cat_name, conf, var, args):
        if type(var) != dict:
            return False

        if len(args) == 0:
            return True

        # Check rules
        name_type, value_type = None, None
        values = []

        for rule in args:
            if ":" in rule:
                name_type, value_type = rule.split(":")

                name_type = name_type.split(",")
                value_type = value_type.split(",")

            elif "," in rule:
                values += rule.split(",")
            
            else:
                conf.log_error(cat, cat_name, f"Config validator rule 'dict[{'&'.join(args)}]' is invalid. Open an issue on GitHub.")

        for name, value in var.items():
            if name_type is not None:
                for rule in name_type:
                    if rule not in rules:
                        conf.log_error(cat, cat_name, f"Config validator asked for variable of type '{rule}', but I don't know how to parse that. Open an issue on GitHub.")

                    if not rules[rule](cat, cat_name, conf, name, []):
                        return False
            
            if value_type is not None:
                for rule in value_type:
                    if rule not in rules:
                        conf.log_error(cat, cat_name, f"Config validator asked for variable of type '{rule}', but I don't know how to parse that. Open an issue on GitHub.")

                    if not rules[rule](cat, cat_name, conf, value, []):
                        return False

        # Make sure each key is included
        for key in values:
            if key not in var:
                return False

        return True

    def _any(cat, cat_name, conf, var, args):
        return True

rules = {
    "str": ValidationRules._str,
    "int": ValidationRules._int,
    "float": ValidationRules._float,
    "number": ValidationRules._number,
    "bool": ValidationRules._bool,
    "list": ValidationRules._list,
    "dict": ValidationRules._dict,
    "any": ValidationRules._any
}