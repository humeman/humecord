import discord
import humecord
from humecord.utils import (
    discordutils,
    miscutils,
    components,
    dateutils,
    miscutils
)

import traceback
import asyncio
import time
import random

class ExecCommand:
    def __init__(
            self
        ):

        self.name = "exec"

        self.description = "Executes Python code."

        self.aliases = ["eval"]

        self.permission = "bot.dev"
        
        self.permission_hide = True

        self.info = {
            "Execute a function": "To execute a function, run %p%exec \\`\\`\\`function\\`\\`\\`."
        }

        self.subcommands = {
            "__syntax__": {
                "function": self.exec,
                "description": "Runs an asynchronous function."
            },
            "list": {
                "function": self.list,
                "description": "Lists all active exec tasks."
            },
            "cancel": {
                "function": self.cancel,
                "description": "Cancels exec tasks."
            },
            "eval": {
                "function": self.eval,
                "description": "Evaluates code."
            }
        }

        global bot
        from humecord import bot

    async def exec(
            self,
            message, 
            resp,
            args, 
            udb,
            gdb, 
            alternate_gdb, 
            preferred_gdb
        ):
        if not " ".join(args[1:]).strip().startswith("```"):
            await bot.commands.syntax_error(
                message,
                resp,
                args,
                gdb,
                "exec"
            )
            return

        function = " ".join(args[1:]).strip()

        if function.endswith("silent"):
            silent = True
            function = function.rsplit("silent", 1)[0].strip()

        else:
            silent = False

        # Remove backticks & whitespace
        function = function.strip("```").strip()

        func_spaced = "\n".join([f"    {x}" for x in function.split("\n")])

        # Store in globals
        exec(f"async def __run_exec(bot, message, resp, args, gdb, alternate_gdb, preferred_gdb):\n{func_spaced}", globals())

        # Create hex ID
        task_id = miscutils.generate_hexid(6)

        # Create task
        task = bot.client.loop.create_task(
            globals()["__run_exec"](bot, message, resp, args, gdb, alternate_gdb, preferred_gdb)
        )

        bot.mem_storage["evals"][task_id] = {
            "started": int(time.time()),
            "task": task,
            "silent": silent
        }
        

        counter = 0
        long_logged = False
        while not task.done():
            await asyncio.sleep(0.1)
            counter += 0.1

            # If it takes more than a second, we log a task start, and give
            # them the task ID so it can be cancelled.

            if counter >= 1 and not long_logged and not silent:
                await resp.send(
                    embed = discordutils.create_embed(
                        title = "Exec task created",
                        description = f"This task is taking a while. If you'd like to cancel it, use `{preferred_gdb['prefix']}dev exec cancel {task_id}`.",
                        color = "green",
                        footer = f"Task ID {task_id}"
                    )
                )
                long_logged = True

        try:
            result = str(task.result())

        except asyncio.CancelledError:
            if not bot.mem_storage["evals"][task_id]["silent"]:
                await resp.send(
                    embed = discordutils.create_embed(
                        title = f"{bot.config.lang['emoji']['error']} Exec task cancelled.",
                        footer = f"Task ID {task_id} | Cancelled after {round(time.time() - bot.mem_storage['evals'][task_id]['started'], 1)}s",
                        color = "error"
                    )
                )

            del bot.mem_storage["evals"][task_id]
            return # Will be handled by a "dev cancel" call
        
        except asyncio.InvalidStateError:
            return

        except:
            result = None
            pass

        exception = task.exception()

        if exception:
            try:
                raise exception

            except Exception as e:
                tb = traceback.format_exc()
                result_title = f"{bot.config.lang['emoji']['error']} Exec task raised an exception"
                result_name = "Exception"
                result_content = f"```py\n{tb[-1000:] + ('...' if len(tb) >= 1000 else '')}\n```"
                color = "error"

        elif result:
            result_title = f"{bot.config.lang['emoji']['success']} Exec complete!"
            result_name = "Result"
            result_content = f"```{result[:1000] + ('...' if len(result) >= 1000 else '')}```"
            color = "success"

        else:
            result_title = f"{bot.config.lang['emoji']['success']} Exec complete!"
            result_name = None
            result_content = None
            color = "success"

        del globals()["__run_exec"]

        if not bot.mem_storage["evals"][task_id]["silent"]: # Refresh it
            await resp.send(
                embed = discordutils.create_embed(
                    title = result_title,
                    fields = [
                        {
                            "name": "Function executed",
                            "value": f"```{function[:1000]}{'...' if len(function) >= 1000 else ''}```"
                        }
                    ] + ([
                        {
                            "name": result_name,
                            "value": result_content
                        } 
                    ] if result_name else []),
                    color = color,
                    footer = f"Task ID {task_id} | Took {round(time.time() - bot.mem_storage['evals'][task_id]['started'], 1)}s"
                )
            )

        del bot.mem_storage["evals"][task_id]
    
    async def eval(
            self,
            message, 
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb, 
            preferred_gdb
        ):
        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify an expression to evaluate."
                )
            )

        expression = " ".join(args[2:])

        try:
            result = str(eval(expression))

        except Exception as e:
            tb = traceback.format_exc()
            await resp.send(
                embed = discordutils.create_embed(
                    title = f"{bot.config.lang['emoji']['error']} Eval raised an exception",
                    fields = [
                        {
                            "name": "Expression evaluated",
                            "value": f"```{expression[:1000]}{'...' if len(expression) >= 1000 else ''}```"
                        },
                        {
                            "name": "Exception",
                            "value": f"```py\n{tb[:1000] + ('...' if len(tb) >= 1000 else '')}\n```"
                        }
                    ],
                    color = "error"
                )
            )
            return

        await message.channel.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']} Eval complete!",
                fields = [
                    {
                        "name": "Expression evaluated",
                        "value": f"```{expression[:1000]}{'...' if len(expression) >= 1000 else ''}```"
                    },
                    {
                        "name": "Result",
                        "value": f"```{result[:1000] + ('...' if len(result) >= 1000 else '')}\n```"
                    }
                ],
                color = "success"
            )
        )

    async def cancel(
            self,
            message, 
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb, 
            preferred_gdb
        ):
        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify exec tasks to cancel."
                )
            )
            return

        ids = args[2].split(",")

        if "all" in ids:
            ids = list(bot.mem_storage["evals"])

        if len(ids) == 0:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Couldn't cancel tasks.",
                    "There are no available tasks to cancel."
                )
            )
            return
    
        if len(args) > 3:
            silent = args[3].lower() in ['yes', "silent", "s", "true"]

        else:
            silent = False

        killed = []
        passed = []

        for task_id in ids:
            task_id = task_id.lower()
            if task_id in bot.mem_storage["evals"]:
                task_data = bot.mem_storage["evals"][task_id]
                bot.mem_storage["evals"][task_id]["silent"] = task_data["silent"] if not silent else True

                try:
                    task_data["task"].cancel()

                    killed.append(
                        {
                            "id": task_id,
                            "after": time.time() - task_data["started"],
                            "silent": task_data["silent"] if not silent else True
                        }
                    )

                except:
                    passed.append(
                        {
                            "id": task_id,
                            "reason": "Exception raised while attempting to cancel"
                        }
                    )

            else:
                passed.append(
                    {
                        "id": task_id,
                        "reason": "Task does not exist"
                    }
                )

        fields = []
        if len(killed) > 0:
            comp = []
            for task in killed:
                comp.append(f"`{task['id']}` | Cancelled after {round(task['after'], 1)}s of activity{' (silenced)' if task['silent'] else ''}")

            fields.append(
                {
                    "name": f"Task{'s' if len(comp) != 1 else ''} cancelled ({len(comp)})",
                    "value": "\n".join(comp)
                }
            )

        if len(passed) > 0:
            comp = []
            for task in passed:
                comp.append(f"`{task['id']}` | {task['reason']}")

            fields.append(
                {
                    "name": f"Couldn't cancel ({len(comp)})",
                    "value": "\n".join(comp)
                }
            )

        if len(killed) > 0 and len(passed) > 0:
            color = "warning"
            emoji = bot.config.lang['emoji']['warning']

        elif len(passed) > 0:
            color = "error"
            emoji = bot.config.lang['emoji']['error']

        else:
            color = "success"
            emoji = bot.config.lang['emoji']['success']

        await resp.send(
            embed = discordutils.create_embed(
                title = f"{emoji} Sent cancel request to {len(ids)} task{'s' if len(ids) != 1 else ''}",
                color = color,
                fields = fields
            )
        )

    async def list(
            self,
            message, 
            resp, 
            args, 
            udb,
            gdb, 
            alternate_gdb, 
            preferred_gdb
        ):
        # Compile list
        comp = []

        for eval_id, eval in bot.mem_storage["evals"].items():
            comp.append(
                {
                    "name": f"→ {eval_id}",
                    "value": f"• Running for: `{dateutils.get_duration(int(time.time()) - eval['started'])}`\n• Silent: `{'yes' if eval['silent'] else 'no'}`"
                }
            )

        if len(comp) == 0:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Can't list active evals!",
                    "Nothing is being evaluated right now."
                )
            )
            return

        await resp.send(
            embed = discordutils.create_embed(
                f"Active evals ({len(comp)})",
                fields = comp,
                color = "invisible"
            )
        )