import asyncio
import shlex
from . import exceptions

import subprocess

import humecord

def sync_run(command):
    subprocess.call(command, shell = True)

def get_output(command):
    return subprocess.check_output(shlex.split(command))

async def run(command):
    cmd = Command(command)

    await cmd._init()

    return cmd

class Command:
    def __init__(self, command):
        self.command = command
        
        self.process = None
        self.task = None

    async def _init(self):
        self.process = await asyncio.create_subprocess_shell(
            self.command,
            stdin = asyncio.subprocess.PIPE,
            stdout = asyncio.subprocess.PIPE,
            stderr = asyncio.subprocess.STDOUT
        )

        asyncio.get_event_loop().create_task(self.handle_stdout())

        await self.process.wait()

        if str(self.process.returncode) != "0":
            humecord.logger.log("subprocess", "error", f"Subprocess call for '{self.command}' returned non-zero exit code: {self.process.returncode}")
            raise exceptions.SubprocessError()

    async def kill(self):
        self.process.terminate()
    
    async def handle_stdout(self):
        done = False
        while not self.process.returncode and not done:
            # Process is still running
            try:
                msg = await self.process.stdout.readuntil(b"\n")
                data = msg.decode("ascii").rstrip()

                # We will eventually log this
                humecord.terminal.log_raw("subprocess", "info", data, True)

            except asyncio.IncompleteReadError:
                done = True
                #logger.log("warn", "Subprocess exited while reading.")

            except asyncio.LimitOverrunError:
                # Shouldn't happen yet.
                humecord.logger.log("subprocess", "warn", "Subprocess limit overrun. Can't read data.")

            except:
                humecord.logger.log("subprocess", "error", "Failed to read data from subprocess.")