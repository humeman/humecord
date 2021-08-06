import humecord
import os
import sys
import json
import copy

class FileInterface:
    def __init__(
            self,
            bot
        ):

        if not os.path.exists("data"):
            humecord.utils.subprocess.sync_run("mkdir data")

        if not os.path.exists("data/tmp"):
            humecord.utils.subprocess.sync_run("mkdir data/tmp")

        self.default_files = {
            "__loops__.json": {
                "loops": {}
            },
            "__debugconsole__.json": {
                "listen": [],
                "commands": {}
            },
            "__bot__.json": {
                "status": bot.config.default_status["status"],
                "visibility": bot.config.default_status["visibility"],
                "activity": {
                    "type": "playing",
                    "streaming": {
                        "game": "Humecord",
                        "url": "https://twitch.tv/hume_man",
                        "twitch_name": "humeman",
                        "platform": "twitch"
                    }
                }
            },
            "__users__.json": {
                "blocked": {},
                "ratelimits": {}
            },
            "__humecord__.json": {
                "version": None,
                "system_logs": {}
            },
            **bot.config.req_files
        }

        self.files = {}

        for file_name, default in self.default_files.items():
            if not os.path.exists(f"data/{file_name}"):
                with open(f"data/{file_name}", "w+") as f:
                    f.write(json.dumps(default, indent = 4))

                humecord.utils.logger.log_step(f"Generated missing file {file_name}", "cyan")

            try:
                with open(f"data/{file_name}", "r") as f:
                    self.files[file_name] = json.loads(f.read())

            except:
                humecord.utils.logger.log("error", f"Failed to read file {file_name}.")
                sys.exit(-1)

            write = False
            for name, value in default.items():
                if name not in self.files[file_name]:
                    self.files[file_name] = copy.copy(value)
                    humecord.utils.logger.log_step(f"Added missing key '{name}' to file '{file_name}'", "cyan")
                    write = True

            if write:
                self.write(file_name)


    def write(
            self,
            name: str
        ):

        for file_name in self.files:
            if name in file_name:
                with open(f"data/{file_name}", "w") as f:
                    f.write(json.dumps(self.files[file_name], indent = 4))