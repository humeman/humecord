from ..utils import fs
from ..utils import logger

import humecord

import os
import inspect
import sys
import traceback

class Config:
    def __init__(self):
        """
        Constructs a config object.

        Should only be called from classes.bot.Bot.__init__().
        """

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

        self.messages = fs.read_yaml(self.mesasges_path)

    def validate(
            self
        ):
        """
        Validates all config options.
        """

        # Read config types
        self.types = fs.read_yaml(f"{os.path.dirname(inspect.getfile(humecord))}/config.types.yml")

        # Parse
        for name, expected in self.types.items():
            # Check if conditional
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

                        if not hasattr(self, var):
                            self.log_error(f"Config requires value '{var}' for validation, but it is not present.")

                        # Exec it
                        try:
                            result = eval(f"self.{var} {sep}", locals())

                            if type(result) != bool:
                                raise "Result must be a boolean"

                        except:
                            self.log_error(f"Config validator could not evaluate: '{var}{sep}'. Incompatible types?", tb = True)

                        if result:
                            use = True

                if use:
                    # Validate everything inside
                    for name_, value_ in expected.items():
                        self.validate_item_feedback(name_, value_)

            else:
                # Make sure variable is valid
                self.validate_item_feedback(name, expected)

    def validate_item_feedback(
            self,
            name,
            expected
        ):

        result = self.validate_item(name, expected)

        if not result:
            self.log_error(f"Config value '{name}' is of invalid type (required: '{expected}')")
            
    def validate_item(
            self,
            name,
            expected
        ):

        if not hasattr(self, name):
            self.log_error(f"Config requires value '{name}' (type: '{expected}').")

        # Parse rule
        if "[" in expected:
            var_type, args = expected.rsplit("]", 1)[0].split("[", 1)
            args = args.split("&")

        else:
            var_type = expected
            args = []

        if var_type not in rules:
            self.log_error(f"Config validator asked for variable of type '{var_type}', but I don't know how to parse that. Open an issue on GitHub.")

        try:
            return rules[var_type](self, getattr(self, name), args)

        except Exception as e:
            if type(e) == SystemExit:
                return
            
            self.log_error(f"Config validator could not validate var '{name}' (type: '{expected}').", tb = True)
        
    def log_error(
            self,
            message,
            tb = False
        ):

        logger.log_step("A config validation error occurred:", "red", bold = True)
        logger.log_step(message, "red")
        print()

        if tb:
            logger.log_long(traceback.format_exc(), "red")
            print()

        logger.log_step("Please correct it and restart.", "red")
        sys.exit(-1)

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
    def _str(conf, var, args):
        return type(var) == str

    def _int(conf, var, args):
        return type(var) == int

    def _float(conf, var, args):
        return type(var) == float

    def _number(conf, var, args):
        return type(var) in [int, float]

    def _bool(conf, var, args):
        return type(var) == bool

    def _list(conf, var, args):
        if not type(var) == list:
            return False

        if len(args) == 0:
            return True

        for item in var:
            for rule in args:
                if rule not in rules:
                    conf.log_error(f"Config validator asked for variable of type '{rule}', but I don't know how to parse that. Open an issue on GitHub.")

                if not rules[rule](conf, item, []):
                    return False

        return True

    def _dict(conf, var, args):
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
                conf.log_error(f"Config validator rule 'dict[{'&'.join(args)}]' is invalid. Open an issue on GitHub.")

        for name, value in var.items():
            if name_type is not None:
                for rule in name_type:
                    if rule not in rules:
                        conf.log_error(f"Config validator asked for variable of type '{rule}', but I don't know how to parse that. Open an issue on GitHub.")

                    if not rules[rule](conf, name, []):
                        return False
            
            if value_type is not None:
                for rule in value_type:
                    if rule not in rules:
                        conf.log_error(f"Config validator asked for variable of type '{rule}', but I don't know how to parse that. Open an issue on GitHub.")

                    if not rules[rule](conf, value, []):
                        return False

        # Make sure each key is included
        for key in values:
            if key not in var:
                return False

        return True

    def _any(conf, var, args):
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