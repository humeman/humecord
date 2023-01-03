"""
/exec: humecord base commands

Executes some code.
"""

import asyncio
import traceback
from typing import Optional, Union

import discord
import time

import humecord

from humecord.classes import (
    discordclasses
)

from humecord.utils import (
    dateutils,
    debug,
    discordutils,
    miscutils
)

class ExecCommand(humecord.Command):
    def __init__(
            self
        ) -> None:
        self.name = "exec"
        self.description = "Executes some code."
        self.command_tree = {
            "run %code%": self.run,
            "list": self.list,
            "cancel %taskid%": self.cancel,
            "eval %code%": self.eval
        }
        self.args = {
            "code": {
                "type": "str",
                "required": True,
                "description": "Code to execute."
            },
            "taskid": {
                "type": "str",
                "required": False,
                "description": "Exec command ID (see /exec list)."
            }
        }
        self.subcommand_details = {
            "run": {
                "description": "Runs a block of code."
            },
            "list": {
                "description": "Lists all active tasks."
            },
            "cancel": {
                "description": "Cancels a task."
            },
            "eval": {
                "description": "Evaulates some code."
            }
        }
        self.messages = {}
        self.dev = True
        self.perms = "bot.dev"
        self.default_perms = "guild.admin"

        global bot
        from humecord import bot

    async def run(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        code = ctx.args.code.strip()

        if code.endswith("silent"):
            silent = True
            code = code.rsplit("silent", 1)[0].strip()

        else:
            silent = False

        # Remove code blocks
        code = code.strip("```")

        # Remove py header
        if code.startswith("py\n"):
            code = code[2:].strip()

        # Add spacing for function creation
        function = "\n".join([f"  {x}" for x in code.split("\n")])

        # Make a new ResponseChannel to make things not break
        if resp.type == humecord.RespTypes.INTERACTION:
            new_resp = humecord.classes.discordclasses.InteractionResponseChannel(ctx.interaction, False)

        elif resp.type == humecord.RespTypes.MESSAGE:
            new_resp = humecord.classes.discordclasses.MessageResponseChannel(ctx.message)

        else:
            # hope for the best
            new_resp = resp

        # Create a function
        exec(f"async def _run_exec(bot, resp, ctx):\n{function}", globals())

        # Create hex ID
        task_id = miscutils.generate_hexid(6)

        # Create task
        task = bot.client.loop.create_task(
            globals()["_run_exec"](bot, new_resp, ctx)
        )

        bot.mem_storage["evals"][task_id] = {
            "started": int(time.time()),
            "task": task,
            "silent": silent
        }

        # Watch task, then respond
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
                        title = f"{bot.config.lang['emoji']['loading']}  Running exec task...",
                        description = f"This task is taking a while. If you'd like to cancel it, use `/exec cancel {task_id}`.",
                        color = "blue",
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
                        title = f"{bot.config.lang['emoji']['error']}  Exec task cancelled.",
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
                result_title = f"{bot.config.lang['emoji']['error']}  Exec task raised an exception."
                result_name = "Exception"
                result_content = f"```py\n{tb[-1000:] + ('...' if len(tb) >= 1000 else '')}\n```"
                color = "error"

        elif result:
            result_title = f"{bot.config.lang['emoji']['success']}  Exec complete!"
            result_name = "Result"
            result_content = f"```{result[:1000] + ('...' if len(result) >= 1000 else '')}```"
            color = "success"

        else:
            result_title = f"{bot.config.lang['emoji']['success']}  Exec complete!"
            result_name = None
            result_content = None
            color = "success"

        del globals()["_run_exec"]

        if not bot.mem_storage["evals"][task_id]["silent"]: # Refresh it
            await resp.send(
                embed = discordutils.create_embed(
                    title = result_title,
                    fields = [
                        {
                            "name": "Function executed",
                            "value": f"```{code[:1000]}{'...' if len(code) >= 1000 else ''}```"
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
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        code = ctx.args.code
        try:
            result = str(eval(code))

        except:
            tb = traceback.format_exc()
            await resp.send(
                embed = discordutils.create_embed(
                    title = f"{bot.config.lang['emoji']['error']}  Eval raised an exception",
                    fields = [
                        {
                            "name": "Expression evaluated",
                            "value": f"```{code[:1000]}{'...' if len(code) >= 1000 else ''}```"
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

        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']} Eval complete!",
                fields = [
                    {
                        "name": "Expression evaluated",
                        "value": f"```{code[:1000]}{'...' if len(code) >= 1000 else ''}```"
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
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        task_id = ctx.args.taskid

        if task_id not in bot.mem_storage["evals"]:
            await resp.error(
                ctx.user,
                "Can't cancel task!",
                f"Task ID `{task_id}` doesn't exist."
            )
            return

        task_data = bot.mem_storage["evals"][task_id]

        try:
            task_data["task"].cancel()

        except:
            await resp.error(
                ctx.user,
                "Couldn't cancel task!",
                "An exception was raised during task cancellation."
            )
            return

        await resp.embed(
            f"{bot.config.lang['emoji']['success']}  Task cancelled!",
            description = f"ID: {task_id}, cancelled after {round(time.time() - task_data['started'], 1)}s of activity",
            color = "success"
        )

    async def list(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        # Compile list of all active tasks
        comp = []

        for eval_id, eval in bot.mem_storage["evals"].items():
            comp.append(
                {
                    "name": f"→ {eval_id}",
                    "value": f"• Running for: `{dateutils.get_duration(int(time.time()) - eval['started'])}`\n• Silent: `{'yes' if eval['silent'] else 'no'}`"
                }
            )

        if len(comp) == 0:
            await resp.error(
                ctx.user,
                "Can't list active tasks!",
                "Nothing is being evaluated right now."
            )
            return

        await resp.embed(
            f"Active tasks ({len(comp)})",
            fields = comp,
            color = "invisible"
        )

        