import discord
import time
import asyncio
import traceback
import aiohttp
import aiofiles
import math

import humecord

from humecord.utils import (
    dateutils,
    discordutils,
    hcutils,
    miscutils,
    components
)

class DevCommand:
    def __init__(self):
        self.name = "dev"

        self.description = "All HumeCord development controls."

        self.aliases = ["development"]

        self.permission = "bot.dev"

        self.subcommands = {
            "error": {
                "function": self.error,
                "description": "Forces an error."
            },
            "reload": {
                "function": self.reload,
                "description": "Reloads the bot."
            },
            "close": {
                "function": self.close,
                "description": "Closes the bot."
            },
            "loops": {
                "function": LoopsSubcommand.run,
                "description": "Manages the bot's loops."
            },
            "exec": {
                "function": ExecSubcommand.run,
                "description": "Allows for execution of code."
            },
            "dm": {
                "function": DMSubcommand.run,
                "description": "DMs someone."
            },
            "profile": {
                "function": ProfileSubcommand.run,
                "description": "Manages the bot's profile."
            },
            "botban": {
                "function": BotBanSubcommand.run,
                "description": "Manages bot-banned users."
            }
        }

        self.shortcuts = {
            "loops": "dev loops",
            "loop": "dev loops",
            "exec": "dev exec",
            "dm": "dev dm",
            "reply": "dev dm reply",
            "reload": "dev reload",
            "close": "dev close",
            "botban": "dev botban",
            "literallyjustfuckingdieihateyousomuch": "dev close"
        }

        global bot
        from humecord import bot

    async def error(self, message, resp, args, gdb, alternate_gdb = None, preferred_gdb = None):
        raise humecord.utils.exceptions.TestException("dev.error call")

    async def reload(self, message, resp, args, gdb, alternate_gdb, preferred_gdb):
        if len(args) > 2:
            safe = args[2].lower() not in ["f", "force"]

        else:
            safe = True

        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['loading']}  Reloading bot...",
                description = f"Safe reload: `{'Yes' if safe else 'No'}`",
                color = "icon_blue"
            )
        )

        await bot.loader.load(safe_stop = safe)

        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['success']}  Reloaded!",
                color = "success"
            )
        )

    async def close(self, message, resp, args, gdb, alternate_gdb, preferred_gdb):
        await resp.send(
            embed = discordutils.create_embed(
                f"{bot.config.lang['emoji']['loading']}  Shutting down...",
                color = "icon_blue"
            )
        )
        
        raise KeyboardInterrupt

class LoopsSubcommand:
    async def run(message, resp, args, gdb, alternate_gdb = None, preferred_gdb = None):
        # Map:
        # !dev loops
        #   list -> List loops & status
        #   run [loop] -> Force run loop
        #   pause [loop] (time/'forever') -> Pauses a loop for a set time
        #   reset [loop] -> Resets a loop (errors, time, all)

        if len(args) >= 3:
            action = args[2].lower()

            if action in ["list"]:
                await LoopsSubcommand.list_(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            elif action in ["run"]:
                await LoopsSubcommand.run_(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            elif action in ["pause"]:
                await LoopsSubcommand.pause(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            elif action in ["unpause"]:
                await LoopsSubcommand.unpause(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            elif action in ["reset"]:
                await LoopsSubcommand.reset(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

        await resp.send(
            embed = discordutils.error(
                message.author,
                "Invalid syntax!",
                f"Specify an action.\nValid actions: `list`, `run`, `pause`, `unpause`, `reset`"
            )
        )

    async def list_(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        # Compile list
        comp = []

        for loop in bot.loops.loops:
            details = [
                f"• Runs: `{hcutils.get_loop_runtime(loop)}`",
                f"• Last run: `{hcutils.get_loop_last_run(loop)}`"
            ]

            if loop.errors > 0:
                if loop.errors >= 3:
                    details.append(f"• Errors: `{loop.errors} (paused)`")

                else:
                    details.append(f"• Errors: `{loop.errors}`")

            if loop.pause_until:
                details.append(f"• Paused for: `{dateutils.get_duration(loop.pause_until - time.time())}`")

            comp.append(
                {
                    "name": f"→ {loop.name}",
                    "value": "\n".join(details)
                }
            )

        if len(comp) == 0:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Can't list loops!",
                    "No loops are active."
                )
            )

        else:
            await resp.send(
                embed = discordutils.create_embed(
                    f"Loops",
                    fields = comp,
                    color = "invisible"
                )
            )

    async def run_(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        if len(args) < 4:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a loop to force run."
                )
            )
            return

        loop = LoopsSubcommand.get_loop(
            args[3].lower()
        )

        if loop is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid loop!",
                    f"Loop '{args[3].lower()}' does not exist."
                )
            )
            return

        humecord.bot.client.loop.create_task(
            humecord.utils.errorhandler.wrap(
                loop.run(),
                context = {
                    "Loop details": [
                        f"Loop: `{loop.name}`",
                        f"Manual call by: <@{message.author.id}>"
                    ]
                }
            )
        )

        await resp.send(
            embed = discordutils.create_embed(
                f"Ran loop {loop.name}",
                description = "Make sure to check the debug channel for errors - they will not be forwarded here.",
                color = "green"
            )
        )

    async def pause(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        if len(args) < 4:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a loop to force run."
                )
            )
            return

        loop = LoopsSubcommand.get_loop(
            args[3].lower()
        )

        if loop is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid loop!",
                    f"Loop '{args[3].lower()}' does not exist."
                )
            )
            return

        if len(args) == 4:
            # Pause indefinitely
            loop.pause = True
            details = "Indefinitely"

        else:
            try:
                duration = dateutils.parse_duration(args[4])

            except Exception as e:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid duration!",
                        f"{str(e)}"
                    )
                )
                return

            # Add to pause_until
            loop.pause_until = int(time.time()) + int(duration)
            details = f"For {dateutils.get_duration(duration)}"

        await resp.send(
            embed = discordutils.create_embed(
                f"Paused loop {loop.name}.",
                description = f"Paused: `{details}`\n\nUnpause it with `{preferred_gdb['prefix']}dev loops unpause {loop.name}`.",
                color = "green"
            )
        )

    async def unpause(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        if len(args) < 4:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a loop to force run."
                )
            )
            return

        loop = LoopsSubcommand.get_loop(
            args[3].lower()
        )

        if loop is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid loop!",
                    f"Loop '{args[3].lower()}' does not exist."
                )
            )
            return

        actions = []

        if loop.pause:
            loop.pause = False
            actions.append("• Removed indefinite pause")

        if loop.pause_until:
            actions.append(f"• Removed timer pause (was due to expire in {dateutils.get_duration(loop.pause_until - int(time.time()))})")
            loop.pause_until = None

        if loop.errors >= 3:
            actions.append(f"• Reset error counter (was at {loop.errors})")

        await resp.send(
            embed = discordutils.create_embed(
                f"Unpaused loop {loop.name}.",
                fields = [
                    {
                        "name": f"→ **Actions:**",
                        "value": "\n".join(actions)
                    }
                ],
                color = "green"
            )
        )

    async def reset(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        if len(args) < 4:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a loop to force run."
                )
            )
            return

        loop = LoopsSubcommand.get_loop(
            args[3].lower()
        )

        if loop is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid loop!",
                    f"Loop '{args[3].lower()}' does not exist."
                )
            )
            return

        actions = []

        if loop.pause:
            loop.pause = False
            actions.append("• Removed indefinite pause")

        if loop.pause_until:
            actions.append(f"• Removed timer pause (was due to expire in {dateutils.get_duration(loop.pause_until - int(time.time()))})")
            loop.pause_until = None

        if loop.errors > 0:
            actions.append(f"• Reset error counter (was at {loop.errors})")

        if loop.type == "delay":
            actions.append(f"• Reset run delay (last run {dateutils.get_duration(int(time.time()) - loop.last_run)} ago)")
            loop.last_run = -1
        
        elif loop.type == "period":
            actions.append(f"• Reset last run time (last run on {humecord.bot.files.files['__loops__.json'][loop.name]['last_run']})")
            humecord.bot.files.files["__loops__.json"][loop.name]["last_run"] = "Never"
            humecord.bot.files.write("__loops__.json")

        await resp.send(
            embed = discordutils.create_embed(
                f"Reset loop {loop.name}.",
                fields = [
                    {
                        "name": f"→ **Actions:**",
                        "value": "\n".join(actions)
                    }
                ],
                color = "green"
            )
        )


    def get_loop(loop_name):
        for loop in humecord.bot.loops.loops:
            if loop.name == loop_name:
                return loop


class ExecSubcommand:
    async def run(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        if message.author.id not in humecord.bot.config.eval_perms:
            await discordutils.error(
                message.author,
                "You can't use this subcommand!",
                "Exec permissions are manually defined in config.yml, and are separate from the dev list."
            )
            return

        if len(args) >= 3:
            action = args[2].lower()

            if action in ["list"]:
                await ExecSubcommand.list(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            elif action in ["cancel"]:
                await ExecSubcommand.cancel(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            elif action in ["eval"]:
                await ExecSubcommand.eval(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            elif " ".join(args[2:]).strip().startswith("```"):
                await ExecSubcommand.exec(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

        await resp.send(
            embed = discordutils.error(
                message.author,
                "Invalid syntax!",
                "Specify an action.\nValid actions: `list`, `eval`, `cancel` (or specify a function to run with \\```)."
            )
        )

    async def exec(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        function = " ".join(args[2:]).strip()

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
        task = humecord.bot.client.loop.create_task(
            globals()["__run_exec"](humecord.bot, message, resp, args, gdb, alternate_gdb, preferred_gdb)
        )

        humecord.bot.mem_storage["evals"][task_id] = {
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
                        title = f"{humecord.bot.config.lang['emoji']['error']} Exec task cancelled.",
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
                result_title = f"{humecord.bot.config.lang['emoji']['error']} Exec task raised an exception"
                result_name = "Exception"
                result_content = f"```py\n{tb[-1000:] + ('...' if len(tb) >= 1000 else '')}\n```"
                color = "error"

        elif result:
            result_title = f"{humecord.bot.config.lang['emoji']['success']} Exec complete!"
            result_name = "Result"
            result_content = f"```{result[:1000] + ('...' if len(result) >= 1000 else '')}```"
            color = "success"

        else:
            result_title = f"{humecord.bot.config.lang['emoji']['success']} Exec complete!"
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

    async def eval(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        if len(args) < 4:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify an expression to evaluate."
                )
            )

        expression = " ".join(args[3:])

        try:
            result = str(eval(expression))

        except Exception as e:
            tb = traceback.format_exc()
            await resp.send(
                embed = discordutils.create_embed(
                    title = f"{humecord.bot.config.lang['emoji']['error']} Eval raised an exception",
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
                f"{humecord.bot.config.lang['emoji']['success']} Eval complete!",
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

    async def cancel(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        if len(args) < 4:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify exec tasks to cancel."
                )
            )
            return

        ids = args[3].split(",")

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
    
        if len(args) > 4:
            silent = args[4].lower() in ['yes', "silent", "s", "true"]

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

    async def list(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        # Compile list
        comp = []
        """
        humecord.bot.mem_storage["evals"][task_id] = {
            "started": int(time.time()),
            "task": task,
            "silent": silent
        }"""

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

class DMSubcommand:
    async def run(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        if len(args) >= 3:
            action = args[2].lower()

            if action in ["reply"]:
                await DMSubcommand.reply(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            else:
                await DMSubcommand.dm(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

        await resp.send(
            embed = discordutils.error(
                message.author,
                "Invalid syntax!",
                "Specify an action.\nValid actions: `reply` (or specify a user to DM)."
            )
        )

    async def dm(
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):
        # dev dm [user id] [message]

        if len(args) < 3:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a user to DM."
                )
            )
            return

        # Get user ID
        if len(args) < 4:
            if len(message.attachments) == 0:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid syntax!",
                        "Specify a message to send, or attach something."
                    )
                ) 
                return

            else:
                msg_args = []

        else:
            msg_args = args[3:]

        await DMSubcommand.send_direct(
            args[2], # User ID
            message,
            resp,
            msg_args # Message
        )

    async def reply(
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):

        if bot.mem_storage["reply"] is None:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Can't reply!",
                    "No one has messaged me recently."
                )
            )
            return

        # dev dm reply [message]

        # Get user ID
        if len(args) < 4:
            if len(message.attachments) == 0:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid syntax!",
                        "Specify a message to send, or attach something."
                    )
                ) 
                return

            else:
                msg_args = []

        else:
            msg_args = args[3:]

            

        await DMSubcommand.send_direct(
            bot.mem_storage["reply"], # User ID
            message,
            resp,
            msg_args # Message
        )

    async def send_direct(
            user_id,
            message,
            resp,
            msg_args
        ):

        # Get user
        try:
            user = discordutils.get_user(
                user_id,
                True,
                message
            )

        except Exception as e:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid user!",
                    str(e)
                )
            )
            return

        # Compile message
        # 1 - check if it's an embed
        if len(msg_args) != 0:
            if msg_args[0].lower() == "--embed":
                # No
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Not implemented yet!",
                        "This feature is disabled until I finish the embed parser."
                    )
                )
                return
                
                msg_args = msg_args[1:]

        # Check for attachments
        kw = {
            "content": ""
        }
        warn = []
        fields = []

        if len(message.attachments) > 0:
            # Try to attach

            attachment = message.attachments[0]

            attach_manual = False
            if attachment.size < 8000000:
                filename = f"data/tmp/{attachment.filename}"
                # Download & re-attach
                await resp.send(
                    embed = discordutils.create_embed(
                        "Downloading attachment...",
                        f"• **Name**: `{attachment.filename}`\n• **Size**: `{miscutils.get_size(attachment.size)}`",
                        color = "yellow"
                    )
                )

                async with aiohttp.ClientSession(headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.95 Safari/537.11"}) as session:
                    async with session.get(attachment.url) as resp_:
                        if resp_.status == 200:
                            async with aiofiles.open(filename, mode = "wb") as f:
                                await f.write(await resp_.read())

                            # Attach
                            kw["file"] = discord.File(filename, attachment.filename)

                            fields.append(
                                {
                                    "name": "→ Attachment",
                                    "value": f"• **Name**: `{attachment.filename}`\n• **Size**: `{miscutils.get_size(attachment.size)}`"
                                }
                            )

                        else:
                            attach_manual = True
                            

            else:
                attach_manual = True

            if attach_manual:
                # Just append the link to content
                kw["content"] = f"{attachment.url}\n"
                fields.append(
                    {
                        "name": "→ Attachment (not embedded)",
                        "value": f"• **URL**: {attachment.url}\n• **Name**: `{attachment.filename}`\n• **Size**: `{miscutils.get_size(attachment.size)}`"
                    }
                )


        kw["content"] += " ".join(msg_args)

        if len(kw["content"]) > 2000:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Can't send message!",
                    f"Your message was {len(kw['content'])} characters long, which exceeds the limit of 2000. Shorten it and try again."
                )
            )
            return

        # Send it
        try:
            await user.send(
                **kw
            )

        except:
            traceback.print_exc()
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Failed to send DM!",
                    "Either the user blocked me, or I don't share mutual servers with them."
                )
            )
            return

        await resp.send(
            embed = discordutils.create_embed(
                f"Sent DM to {user.name}#{user.discriminator}!",
                description = f"→ **Content**:\n{kw['content'][:1900]}{'**...**' if len(kw['content']) > 1900 else ''}",
                fields = fields,
                color = "green"
            )
        )

class ProfileSubcommand:
    async def run(message, resp, args, gdb, alternate_gdb, preferred_gdb):
        if len(args) >= 3:
            action = args[2].lower()

            if action in ["reply"]:
                await DMSubcommand.reply(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            else:
                await DMSubcommand.dm(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

        await resp.send(
            embed = discordutils.error(
                message.author,
                "Invalid syntax!",
                "Specify an action.\nValid actions: `reply` (or specify a user to DM)."
            )
        )


class BotBanSubcommand:
    async def run(message, resp, args, gdb, alternate_gdb = None, preferred_gdb = None):
        # Map:
        # !dev botban
        #   list -> List banned users
        #   add [user] [duration] [description] -> Ban user
        #   remove [user] [duration] [description] -> Unban user

        if len(args) >= 3:
            action = args[2].lower()

            if action in ["list"]:
                await LoopsSubcommand.list_(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            elif action in ["add"]:
                await LoopsSubcommand.add(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

            elif action in ["remove", "del"]:
                await LoopsSubcommand.remove(message, resp, args, gdb, alternate_gdb, preferred_gdb)
                return

        await resp.send(
            embed = discordutils.error(
                message.author,
                "Invalid syntax!",
                f"Specify an action.\nValid actions: `list`, `add`, `remove`"
            )
        )

    async def list(message, resp, args, gdb, alternate_gdb = None, preferred_gdb = None):
        await BotBanSubcommand.generate_list(
            True, # Send new
            0, # Page 1
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb
        )

    async def generate_list(
            gen_new,
            page,
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):

        # Compile a list
        comp = []

        for uid, details in bot.files.files["__users__.json"]["blocked"].items():
            user = bot.client.get_user(user)

            if user is None:
                name = f"%-b% {uid}"
                u = [
                    f"  %-b% <@{uid}> (*unknown*)"
                ]

            else:
                name = f"%-a% {user.name}#{user.discriminator}",

                u = [
                    f"  %-b% <@{uid}>"
                    f"  %-b% Banned: `{dateutils.get_datetime(u['banned_on'])}`"
                ]

                if u['duration'] is None:
                    u.append(
                        f"  %-b% Duration: `Permanent`"
                    )
                    
                else:
                    u.append(
                        f"  %-b% Duration: `{dateutils.get_duration(u['duration'])}`"
                    )

                if u['reason'] is not None:
                    u.append(
                        f"  %-b% Reason: `{u['reason'][:75]}{'...' if len(u['reason']) > 75 else ''}"
                    )

            comp.append(
                {
                    "name": name,
                    "value": "\n".join(u)
                }
            )

        if len(comp) == 0:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Can't list botbans!",
                    "No one is botbanned right now."
                )
            )

        # Find page bounds
        max_pages = math.floor(len(comp) / 15)

        if page > max_pages:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid page!",
                    f"Page {page + 1} exceeds max page of {max_pages}."
                )
            )

        # Determine page
        comp = comp[15 * page:15 * (page + 1)]

        embed = discordutils.create_embed(
            f"{bot.config.cool_name}'s botbanned users (Page {page + 1}/{max_pages})",
            fields = comp,
            color = "invisible"
        )

        if page == 0:
            backward_button = ["secondary", BotBanSubcommand.pass_]

        else:
            backward_button = ["primary", lambda *args: BotBanSubcommand.generate_list(False, int(page - 1), *args)]

        if page + 1 >= max_pages:
            forward_button = ["secondary", BotBanSubcommand.pass_]

        else:
            forward_button = ["primary", lambda *args: BotBanSubcommand.generate_list(False, int(page + 1), *args)]

        # Create view
        view = components.create_view(
            [
                components.create_button(
                    message,
                    label = "🡸",
                    id = "back",
                    style = backward_button[0],
                    callback = backward_button[1]
                ),
                components.create_button(
                    message,
                    label = "🡺",
                    id = "forward",
                    style = forward_button[0],
                    callback = forward_button[1]
                )
            ]
        )

        # Send
        if gen_new:
            await resp.send(
                embed = embed,
                view = view
            )

        else:
            await resp.edit(
                embed = embed,
                view = view
            )

    async def pass_(*args):
        pass

    async def add(
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):
        # Check args

        # dev botban add [user] [duration] [reason]
        if len(args) < 4:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid syntax!",
                    "Specify a user, and optionally, a duration and reason.\nAdditionally, end the message with `-s` to not send a DM to the user."
                )
            )
            return

        try:
            user = discordutils.get_user(args[3])

        except:
            for char in "<@!>":
                user = user.replace(char, "")

            try:
                uid = int(user)

            except:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid user!",
                        f"Mention a user, or paste their ID."
                    )
                )
                return

            else:
                details = str(uid)

                dm = False
        
        else:
            # Get user's details
            uid = int(user.id)

            details = f"{user.name}#{user.discriminator} ({user.id})"

            dm = True

        if args[-1].lower() == "-s":
            silent = True
            args = args[:-1]

        else:
            silent = False

        # Check if duration is defined
        reason = "Not specified"
        try:
            duration = dateutils.get_duration(args[4])

            if len(args) > 5:
                reason = " ".join(args[5:])

        except:
            duration = None

            if len(args) > 4:
                reason = " ".join(args[4:])

        # Send to API
        details = await bot.api.put(
            "users",
            "blocked",
            {
                "id": uid,
                "reason": reason,
                "duration": duration
            }
        )

        # Check if we should dm
        if dm and (not silent):
            await user.send(
                **(
                    await bot.messages.get(
                        gdb,
                        [""],
                        {
                            "bot": bot.config.bot_name,
                            "duration": "Permanent" if duration is None else duration,
                            "reason": reason
                        }
                    )
                )
            )