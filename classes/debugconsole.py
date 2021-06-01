import discord
import traceback
import aiofiles

import humecord


class DebugConsole:
    def __init__(
            self
        ):
        """
        Constructs a DebugConsole.

        DebugConsoles handle the evaluation of code in a bot's
        debug channel.
        """

        self.channel = None
        self.listen = []

    async def prep(
            self
        ):
        """
        Prepares the console.
        Loads the channel, and imports the list of active users
        to listen to.
        """

        self.channel = humecord.bot.debug_channel

        self.listen = humecord.bot.files.files["__debugconsole__.json"]["listen"]

    def add_listen(
            self, 
            user
        ):
        """
        Begins listening to the specified user.
        """

        if user.id not in self.listen:
            self.listen.append(user.id)

        humecord.bot.files.write("__debugconsole__.json")

    def remove_listen(
            self, 
            user
        ):
        """
        Stops listening to the specified user.
        """

        if user.id in self.listen:
            del self.listen[self.listen.index(user.id)]

        humecord.bot.files.write("__debugconsole__.json")

    async def check_listen(
            self,
            message
        ):
        """
        Handles listening/unlistening and permissions of someone
        trying to call something via the console.
        """

        msg = message.content.lower().strip()

        if msg == ">":
            # Check permissions
            if message.author.id not in humecord.bot.config.eval_perms:
                await message.channel.send(
                    embed = humecord.utils.discordutils.error(
                        "Can't enable debug console!",
                        "You don't have permission to use this feature.",
                        message
                    )
                )
                return False

            if message.author.id not in self.listen:
                self.add_listen(message.author)
                await message.add_reaction(humecord.bot.config.lang["emoji"]["success"])

            return False # Don't want to evaluate this one - just switch listen on/off

        elif msg == "<":
            if message.author.id not in humecord.bot.config.eval_perms:
                await message.channel.send(
                    embed = humecord.utils.discordutils.error(
                        "Can't disable debug console!",
                        "You don't have permission to use this feature.",
                        message
                    )
                )
                return False

            if message.author.id in self.listen:
                self.remove_listen(message.author)
                await message.add_reaction(humecord.bot.config.lang["emoji"]["success"])

            return False

        else:
            return message.author.id in self.listen

    async def parse_task(
            self,
            message
        ):
        """
        Parses a message to be executed.
        """

        tasks = []

        lines = [x for x in message.content.strip().strip("```").split("\n")]

        active = ""
        for line in lines:
            if line == "":
                continue

            if line.endswith(":") and active == "":
                active = line
                continue

            if active != "":
                if line.startswith(" "):
                    active += f"\n{line}"
                    continue

                else:
                    tasks.append(
                        {
                            "type": "exec",
                            "cmd": active
                        }
                    )

                    active = ""

            if "=" in line and "if" not in line:
                if " " not in line.split("=")[0].strip():
                    tasks.append(
                        {
                            "type": "exec",
                            "cmd": "line"
                        }
                    )
                    continue

            elif line.startswith("import") or (line.startswith("from") and "import" in line) or line.startswith("return") or line.startswith("raise"):
                tasks.append(
                    {
                        "type": "exec",
                        "cmd": line
                    }
                )

            else:
                if line.strip().startswith("await "):
                    tasks.append(
                        {
                            "type": "asynceval",
                            "cmd": line.split("await ")[1]
                        }
                    )

                else:
                    tasks.append(
                        {
                            "type": "eval",
                            "cmd": line
                        }
                    )

        if active != "":
            tasks.append(
                {
                    "type": "exec",
                    "cmd": active
                }
            )

        return tasks

    async def run(
            self,
            message,
            tasks: list
        ):

        globals()["message"] = message
        globals()["humecord"] = humecord
        globals()["bot"] = humecord.bot

        r = None

        for task in tasks:
            try:
                if task["type"] == "exec":
                    r = exec(task["cmd"], globals())

                elif task["type"] == "asynceval":
                    r = await eval(task["cmd"], globals())

                else:
                    r = eval(task["cmd"], globals())


            except:
                r = traceback.format_exc()

        if r is not None:
            if len(str(r)) > 1975:
                async with aiofiles.open("data/dc_temp.txt", "w+") as f:
                    await f.write(r)

                await message.channel.send(file = discord.File("data/dc_temp.txt", "console.txt"))

            else:
                await message.channel.send(f"```py\n{str(r)[:1975]}\n```")

    async def execute(
            self,
            message
        ):
        """
        Executes a message.
        """

        if await self.check_listen(message):
            tasks = await self.parse_task(message)

            await self.run(message, tasks)