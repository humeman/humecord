from ..utils import fs

class Config:
    def __init__(self):
        """
        Constructs a config object.

        Should only be called from classes.bot.Bot.__init__().
        """
        self.globals = Globals()

    def load_globals(
            self
        ):
        """
        Loads global configuration values from
        the specified global config file.
        """

        self.raw_globals = fs.read_yaml(self.globals_path)

        for key, value in self.raw_globals.items():
            setattr(self.globals, key, value)

class Globals:
    def __init__(
            self
        ):
        """
        Initializes a global config object.
        """

        pass