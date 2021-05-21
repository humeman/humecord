import humecord
import os
import sys
import json

class FileInterface:
    def __init__(
            self,
            bot
        ):

        if not os.path.exists("data"):
            humecord.utils.subprocess.sync_run("mkdir data")

        self.default_files = {
            "__loops__.json": {
                "loops": {}
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

    def write(
            self,
            name: str
        ):

        for file_name in self.files:
            if name in file_name:
                with open(f"data/{file_name}", "w") as f:
                    f.write(json.dumps(self.files[file_name], indent = 4))