import humecord

import time
import asyncio

class Loops:
    def __init__(
            self
        ):

        self.loops = []

        self.task = None

        self.stop = False

    def get_imports(
            self
        ):

        comp = [
            {
                "imp": "from humecord.loops import refresh_status",
                "module": "refresh_status",
                "class": "RefreshStatusLoop"
            }
        ]

        if humecord.bot.config.use_api:
            comp.append(
                {
                    "imp": "from humecord.loops import update_overrides",
                    "module": "update_overrides",
                    "class": "UpdateOverridesLoop"
                }
            )

        return comp

    async def prep(
            self
        ):
        self.expand()

        for loop in self.loops:
            if loop.name not in humecord.bot.files.files["__loops__.json"]:
                humecord.bot.files.files["__loops__.json"][loop.name] = {
                    "last_run": -1
                }

        humecord.bot.files.write("__loops__.json")

        self.recover_api = humecord.loops.recover_api.RecoverAPILoop()

        await self.start()

    def expand(
            self
        ):
        # Set all the settings we need on each loop

        change = {
            "last_run": -1,
            "logging": {
                "start_fail": False,
                "update_fail": False,
                "skip": False
            },
            "task": None,
            "errors": 0,
            "pause_until": None,
            "pause": False
        }

        for loop in self.loops:
            for key, value in change.items():
                setattr(loop, key, value)

    async def start(
            self
        ):

        if self.task:
            if not self.task.done():
                raise humecord.utils.exceptions.AlreadyRunning(f"Loop task is already running. Terminate it with humecord.bot.loops.task.terminate().")

        self.task = humecord.bot.client.loop.create_task(self.run())

    async def run(
            self
        ):

        await humecord.bot.client.wait_until_ready()

        while not self.stop:
            await asyncio.sleep(0.5)

            if not humecord.bot.client.is_ready:
                continue

            # Check API access
            if humecord.bot.config.use_api:
                if not humecord.bot.api_online:
                    await self.recover_api.run()
                    continue

            for loop in self.loops:
                if self.check_run(loop):
                    if loop.errors >= 3:
                        continue

                    # Manual pause
                    if loop.pause:
                        continue

                    if loop.pause_until:
                        if loop.pause_until > int(time.time()):
                            continue

                        else:
                            loop.pause_until = None
                            humecord.utils.logger.log("warn", f"Unpaused loop {loop.name}, which was paused 60 seconds ago because of an error.")

                    if loop.task:
                        if not loop.task.done():
                            humecord.utils.logger.log("warn", f"Tried to start {loop.name}, but previous execution is still running. Consider increasing delay.")
                            continue

                    # Needs to be run
                    self.store_run(loop)
                    loop.task = humecord.bot.client.loop.create_task(
                        humecord.utils.errorhandler.wrap(
                            loop.run(),
                            context = {
                                "Loop details": [
                                    f"Loop: `{loop.name}`",
                                    f"Execution will be paused for {humecord.bot.config.loop_pause_time} seconds since an error occurred.",
                                    f"Loop exception counter is now at {loop.errors + 1}. If 3 are accumulated, it will be stopped indefinitely."
                                ]
                            },
                            on_fail = [pause_execution, [loop]]
                        )
                    )

    def check_run(self, loop):
        if loop.type == "delay":
            if loop.last_run < int(time.time()) - loop.delay:
                return True

            return False

        elif loop.type == "period":
            # Check shortcuts
            return humecord.bot.files.files["__loops__.json"][loop.name]["last_run"] != humecord.utils.dateutils.get_datetime(loop.time)

    def store_run(self, loop):
        if loop.type == "delay":
            loop.last_run = int(time.time())

        elif loop.type == "period":
            # Check shortcuts
            humecord.bot.files.files["__loops__.json"][loop.name]["last_run"] = humecord.utils.dateutils.get_datetime(loop.time)
            humecord.bot.files.write("__loops__.json")


async def pause_execution(loop):
    loop.pause_until = int(time.time()) + humecord.bot.config.loop_pause_time
    loop.errors += 1

    if loop.errors >= 3:
        humecord.utils.logger.log("error", f"Loop {loop.name} has been indefinitely paused because 3 errors accumulated.")

        try:
            await humecord.bot.debug_channel.send(
                embed = humecord.utils.discordutils.create_embed(
                    f"{humecord.bot.config.lang['emoji']['error']}  Loop paused due to exceptions.",
                    description = f"Loop **{loop.name}** has been indefinitely paused since 3 exceptions occurred.\nTo unpause it, run `dev loops unpause {loop.name}`.",
                    color = "error"
                )
            )

        except:
            humecord.utils.logger.log("warn", f"Failed to log loop pause to debug channel.")
                    
