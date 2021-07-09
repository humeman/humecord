import humecord

import importlib
import traceback
import asyncio

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

        # Run on_close event
        if (not safe_stop) and (not starting):
            await humecord.bot.events.call("hh_on_stop", [])

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
        await self.load_imports(safe_stop)

        if (not safe_stop) or starting:
            # Call ready again
            await humecord.bot.events.call("on_ready", [None])

    async def load_config(
            self
        ):

        # Reload all the config.
        humecord.bot.load_config()

        # Load globals
        humecord.bot.config.load_globals()

        # Load lang
        humecord.bot.config.load_lang()

        # Validate
        humecord.bot.config.validate_all()

    async def load_imports(
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

        # Set up loops
        humecord.bot.loops.loops = []

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

            #print(updater)

            # Import the class
            #exec(
            #    f"from {loop['module']} import {loop['class']}",
            #    globals()
            #)

            # Create a class, append to comp
            exec(f"__loop = {loop['module']}.{loop['class']}()", globals())

            exec("humecord.bot.loops.loops.append(__loop)")

        # Prep loops
        await humecord.bot.loops.prep()

        # Set up commands
        humecord.bot.commands.commands = {}

        for category, commands in self.data["commands"].items():
            humecord.bot.commands.commands[category] = []

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

                # Import the class
                #exec(
                #    f"from {command['module']} import {command['class']}",
                #    globals()
                #)

                # Create a class, append to comp
                exec(f"__cmd = {command['module']}.{command['class']}()", globals())

                exec(f"humecord.bot.commands.commands['{category}'].append(__cmd)")

        # Tell it to register internal commands
        humecord.bot.commands.register_internal()

        # Load up events
        humecord.bot.events.events = {}

        for name, events in self.data["events"].items():
            for event in events:
                # Check if old import exists
                if event["class"] not in globals():
                    # Run the import
                    exec(event["imp"], globals())

                # Reload it
                exec(
                    f"importlib.reload({event['class']})",
                    globals()
                )

                # Create events
                humecord.bot.events.events[name] = []

                for func in event["funcs"]:
                    exec(
                        f"humecord.bot.events.events['{name}'].append({event['class']}.{func})", 
                        globals()
                    )

        # Do the thing
        await humecord.bot.events.prep()
