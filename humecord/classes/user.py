import humecord

class Command:
    def __init__(self):
        # Validate command, fill in anything missing
        cdir = dir(self)

        if "args" not in cdir:
            # Verify subcommands aren't present
            if "subcommands" not in cdir:
                self.args = {
                    "default": {
                        "required": False,
                        "index": 1,
                        "fill": True,
                        "rules": {
                            "default1a": {"rule": "str"}
                        }
                    }
                }
                humecord.logger.log(
                    "dev",
                    "warn",
                    f"Command {self.name} is missing arguments. Args will be passed as a single string under key 'default'."
                )

        # Verify each subcommand has args, if present
        if "subcommands" in cdir:
            for sname, scmd in self.subcommands.items():
                if "args" not in scmd:
                    self.subcommands[sname]["args"] = {
                        "default": {
                            "required": False,
                            "index": 2,
                            "fill": True,
                            "rules": {
                                "default1a": {"rule": "str"}
                            }
                        }
                    }

                    humecord.logger.log(
                        "dev",
                        "warn",
                        f"Command {self.name}.{sname} is missing arguments. Args will be passed as a single string under key 'default'."
                    )

        self.slash_info = {}