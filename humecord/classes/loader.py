import humecord

from humecord.utils import (
    exceptions,
    dateutils
)

from .commandhandler import CommandHandler

import importlib
import traceback
import asyncio
import inspect

class Loader:
    def __init__(
            self,
            imports_imp,
            imports_module
        ):

        self.imports_imp = imports_imp
        self.imports_module = imports_module

    async def load(
            self,
            starting: bool = False,
            safe_stop: bool = False
        ):

        # Shut down the bot
        humecord.bot.available = False

        if not starting:
            humecord.logger.log("loader", "start", "Reloading...", bold = True)

        # Run on_close event
        if (not safe_stop) and (not starting):
            await humecord.bot.events.call("hc_on_stop", [])

        # Check if the imports class is defined - if so, del it
        if hasattr(self, "imports"):
            del self.imports

        # Check if we should delete the import file too
        if self.imports_module in globals():
            # Delete it
            exec(f"del {self.imports_module}", globals())

        exec(self.imports_imp, globals())
        # Reload imports method
        exec(
            f"importlib.reload({self.imports_module})",
            globals()
        )
        # Create new imports class
        exec(f"self.imports = {self.imports_module}.Imports()")

        # Store imports data to self
        self.data = self.imports.loader

        # Load in the imports
        await self.stop_all(safe_stop)

        # Prepare command handler
        if not starting:
            humecord.bot.commands.slashtree.clear_commands(guild = None)

            for gid in humecord.bot.config.dev_guilds:
                guild = humecord.bot.client.get_guild(gid)

                if guild is None:
                    continue

                humecord.bot.commands.slashtree.clear_commands(guild = guild)


        await self.load_loops()
        await self.load_commands()
        await self.load_msgadapter()
        await self.load_events()

        if (not safe_stop) or starting:
            # Call ready again
            await humecord.bot.events.call("on_ready", [None])

    async def load_config(
            self
        ):

        # Reload the config
        await humecord.bot.load_config()

        # Load globals
        humecord.bot.config.load_globals()

        # Load lang
        humecord.bot.config.load_lang()

        # Load messages
        humecord.bot.config.load_messages()

        # Validate
        humecord.bot.config.validate_all()

    async def stop_all(
            self,
            safe_stop: bool = False
        ):

        # Close loop handler
        if safe_stop:
            # Wait for loop task to stop
            humecord.bot.loops.stop = True

            cycles = 0
            while not humecord.bot.loops.task.done() and cycles < 20:
                await asyncio.sleep(0.1)
                cycles += 1

            if cycles >= 20:
                # Force kill
                try:
                    humecord.bot.loops.task.cancel()

                except:
                    pass

        else:
            # Kill loop task
            if humecord.bot.loops.task is not None:
                try:
                    humecord.bot.loops.task.cancel()

                except:
                    pass

        # Close each loop task
        for loop in humecord.bot.loops.loops:
            if hasattr(loop, "task"):
                if loop.task is not None:
                    if safe_stop:
                        cycles = 0
                        while not loop.task.done() and cycles < 100:
                            await asyncio.sleep(0.1)
                            cycles += 1

                    else:
                        cycles = 100
                    
                    if cycles >= 100:
                        # Force kill
                        try:
                            loop.task.cancel()

                        except:
                            traceback.print_exc()

        humecord.bot.loops.task = None

    async def load_loops(
            self
        ):
        # Set up loops
        humecord.bot.loops.loops = []

        self.data["loops"] += humecord.bot.loops.get_imports()

        for loop in self.data["loops"]:
            # Delete the old class
            if loop["class"] in globals():
                exec(
                    f"del {loop['class']}",
                    globals()
                )

            # Check if old import exists
            if loop["class"] not in globals():
                # Run the import
                exec(loop["imp"], globals())
            
            exec(
                f"importlib.reload({loop['module']})",
                globals()
            )

            # Create a class
            _loop = eval(f"{loop['module']}.{loop['class']}()")

            if "attrs" in loop:
                # Set attrs
                for attr, value in loop["attrs"].items():
                    if not attr.startswith("__"):
                        setattr(_loop, attr, value)

            # Validate it
            await self.validate(
                "loop",
                _loop
            )

            humecord.bot.loops.loops.append(_loop)

        # Prep loops
        humecord.bot.loops.stop = False
        await humecord.bot.loops.prep()


    async def load_commands(
            self
        ):
        # Set up commands
        humecord.bot.commands.reset()
        await humecord.bot.commands.prep_loader()

        for category, commands in self.data["commands"].items():
            # Tell CommandHandler all our imported commands, generate a tree
            await humecord.bot.commands.imp_add_command_category(
                category,
                commands
            )

        tree = await humecord.bot.commands.get_import_tree()

        generated = {}

        for category, commands in tree.items():
            for command in commands:
                # Check if the old command exists
                if command["class"] not in globals():
                    # Run the import
                    exec(command["imp"], globals())
            
                exec(
                    f"importlib.reload({command['module']})",
                    globals()
                )

                # Delete the old class
                if command["class"] in globals():
                    exec(
                        f"del {command['class']}",
                        globals()
                    )

                # Create a class, append to comp
                _command = eval(f"{command['module']}.{command['class']}()")

                if "attrs" in command:
                    # Set attrs
                    for attr, value in command["attrs"].items():
                        if not attr.startswith("__"):
                            setattr(_command, attr, value)

                # Validate it
                
                #await self.validate(
                #    "command",
                #    _command
                #)

                # Send off to command handler
                await humecord.bot.commands.add_command(
                    category,
                    _command
                )

        await humecord.bot.commands.sync()

    async def load_msgadapter(
            self
        ):
        await humecord.bot.msgadapter.generate_tree()

    async def load_msgcommands(
            self
        ):

        raise DeprecationWarning("no use")

        humecord.bot.msgcommands.commands = {}

        for category, commands in humecord.bot.msgcommands.get_imports().items():
            if category not in self.data["msgcommands"]:
                self.data["msgcommands"][category] = []

            self.data["msgcommands"][category] += commands

        for category, commands in self.data["msgcommands"].items():
            humecord.bot.msgcommands.commands[category] = []

            for command in commands:
                # Check if the old command exists
                if command["class"] not in globals():
                    # Run the import
                    exec(command["imp"], globals())
            
                exec(
                    f"importlib.reload({command['module']})",
                    globals()
                )

                # Delete the old class
                if command["class"] in globals():
                    exec(
                        f"del {command['class']}",
                        globals()
                    )

                # Create a class, append to comp
                _command = eval(f"{command['module']}.{command['class']}()")

                if "attrs" in command:
                    # Set attrs
                    for attr, value in command["attrs"].items():
                        if not attr.startswith("__"):
                            setattr(_command, attr, value)

                # Validate it
                await self.validate(
                    "command",
                    _command
                )

                humecord.bot.msgcommands.commands[category].append(_command)
        
        await humecord.bot.msgcommands.args.compile_all()

    async def load_events(
            self
        ):
        # Set up events
        humecord.bot.events.edb = {}
        humecord.bot.events.events = []

        self.data["events"] += humecord.bot.events.get_imports()

        for event in self.data["events"]:
            # Check if the old event exists
            if event["class"] not in globals():
                # Run the import
                exec(event["imp"], globals())
        
            exec(
                f"importlib.reload({event['module']})",
                globals()
            )

            # Delete the old class
            if event["class"] in globals():
                exec(
                    f"del {event['class']}",
                    globals()
                )

            # Create a class, append to comp
            _event = eval(f"{event['module']}.{event['class']}()")

            if "attrs" in event:
                # Set attrs
                for attr, value in event["attrs"].items():
                    if not attr.startswith("__"):
                        setattr(_event, attr, value)

            # Validate it
            await self.validate(
                "event",
                _event
            )

            humecord.bot.events.events.append(_event)

        # Do the thing
        await humecord.bot.events.prep()

    async def validate(
            self,
            object_type: str,
            object: str
        ):

        for key, details in validators[object_type]["keys"].items():
            # Check if this is required
            if details.get("optional") == True:
                if not hasattr(object, key):
                    continue # Still good

            else:
                # Check if the object has that attribute
                if not hasattr(object, key):
                    # Log an error
                    raise exceptions.InitError(
                        f"{object_type[0].upper()}{object_type[1:]} {object.name} is missing required attribute {key}.",
                        traceback = False
                    )

            # Check type
            if type(getattr(object, key)) not in details["type"]:
                raise exceptions.InitError(
                    f"{object_type[0].upper()}{object_type[1:]} {object.name}'s attribute {key} is of invalid type.",
                    traceback = False
                )

            # Run validators
            for validator in validators[object_type]["validators"]:
                result = await validator(
                    object
                )

                if result is not None:
                    raise exceptions.InitError(
                        result,
                        traceback = False
                    )

class CommandValidators:
    async def validate_subcommands(
            command
        ):

        # Check if included
        if hasattr(command, "subcommands"):
            # Type already verified by key validator
            matched = []

            for name, value in command.subcommands.items():
                if name in matched:
                    return f"Command {command.name} has duplicate subcommand {name}"

                if name.startswith("__"):
                    if name not in ["__default__", "__syntax__"]:
                        return f"Command {command.name} has nonexistant subcommand override {name}"

                # Check if keys are included
                if type(value.get("description")) != str:
                    return f"Command {command.name}'s subcommand {name} has invalid description (not optional, must be a string)"
                
                if "function" not in value:
                    return f"Command {command.name}'s subcommand {name} has no defined function"

                # Need exactly 7 arguments (and self, optional)
                params = inspect.signature(value["function"]).parameters #.__code__.co_varnames

                args = []

                for name_, param in params.items():
                    if param.kind in [inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD]:
                        # Accepts any amount
                        return

                    elif param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and len(args) >= 7:
                        continue

                    args.append(name_)

                if args[0] == "self":
                    args = args[1:]

                if len(args) != 7:
                    return f"Command {command.name}'s subcommand {name}'s function has invalid number of arguments: {len(args)}"

                if "syntax" in value:
                    if type(value["syntax"]) != str:
                        return f"Command {command.name}'s subcommand {name} has invalid syntax (optional, must be a string)"

                matched.append(name)

    async def validate_function(
            command
        ):

        if not hasattr(command, "subcommands"):
            # Must have a run func instead.
            if not hasattr(command, "run"):
                return f"Command {command.name} has no callable element (define run() or subcommands)"

            if not callable(command.run):
                return f"Command {command.name}'s run attribute is not a function"

            params = inspect.signature(command.run).parameters #.__code__.co_varnames

            args = []

            for name, param in params.items():
                if param.kind in [inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD]:
                    # Accepts any amount
                    return

                elif param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD and len(args) >= 7:
                    continue

                args.append(name)

            if args[0] == "self":
                args = args[1:]

            if len(args) != 7:
                return f"Command {command.name}'s run function has invalid number of arguments: {len(args)}"

    async def validate_aliases(
            command
        ):

        if hasattr(command, "aliases"):
            for alias in command.aliases:
                if type(alias) != str:
                    return f"Command {command.name} has alias of invalid type (must be a string)"

class EventValidators:
    async def validate_functions(
            event
        ):

        matched = []

        for name, function in event.functions.items():
            if type(name) != str:
                return f"Event {event.name} has function with invalid name (must be a string)"

            if name in matched:
                return f"Event {event.name} has duplicate function: {name}"

            if "function" not in function:
                return f"Event {event.name}'s function {name} has no function defined"

            if not callable(function["function"]):
                return f"Event {event.name}'s function isn't callable"

            # Check priority
            if type(function.get("priority")) != int:
                return f"Event {event.name}'s function {name} has invalid priority (not optional, must be an int)"

            if function["priority"] < 0 or function["priority"] > 100:
                return f"Event {event.name}'s function {name} has priority not within 0 and 100"

            if "description" in function:
                if type(function["description"]) != str:
                    return f"Event {event.name}'s function {name} has invalid description (optional, must be a string)"

class LoopValidators:
    async def validate_type(
            loop
        ):

        if loop.type == "delay":
            if not hasattr(loop, "delay"):
                return f"Loop {loop.name} has no delay defined (not optional, must be an int)"

        elif loop.type == "period":
            if not hasattr(loop, "time"):
                return f"Loop {loop.name} has no time defined (not optional, must be a str)"

            valid = False
            for name, aliases in dateutils.aliases.items():
                if loop.time == name or loop.time in aliases:
                    valid = True

            if not valid:
                return f"Loop {loop.name} has invalid time {loop.time}"

        else:
            return f"Loop {loop.name} has invalid type {loop.type}"

validators = {
    "command": {
        "keys": {
            "name": {
                "type": [str]
            },
            "description": {
                "type": [str]
            },
            "aliases": {
                "type": [list]
            },
            "permission": {
                "type": [str]
            },
            "subcommands": {
                "optional": True,
                "type": [dict]
            },
            "shortcuts": {
                "optional": True,
                "type": [dict]
            }
        },
        "validators": [
            CommandValidators.validate_subcommands,
            CommandValidators.validate_function
        ]
    },
    "event": {
        "keys": {
            "name": {
                "type": [str]
            },
            "description": {
                "optional": True,
                "type": [str]
            },
            "event": {
                "type": [str]
            },
            "functions": {
                "type": [dict]
            }
        },
        "validators": [
            EventValidators.validate_functions
        ]
    },
    "loop": {
        "keys": {
            "name": {
                "type": [str]
            },
            "type": {
                "type": [str]
            },
            "delay": {
                "optional": True,
                "type": [int, float]
            },
            "time": {
                "optional": True,
                "type": [str]
            }
        },
        "validators": [
            LoopValidators.validate_type
        ]
    }
}