from ..utils import fs

class Config:
    def __init__(self):
        """
        Constructs a config object.

        Should only be called from classes.bot.Bot.__init__().
        """

    def load_globals(
            self
        ):
        """
        Loads global configuration values from
        the specified global config file.
        """

        self.raw_globals = fs.read_yaml(self.globals_path)

        self.globals = Globals(self)

        for key, value in self.raw_globals.items():
            setattr(self.globals, key, value)

    def load_lang(
            self
        ):
        """
        Loads global configuration values from
        the specified global config file.
        """

        self.lang = fs.read_yaml(self.lang_path)

    def load_messages(
            self
        ):
        """
        Loads global message defaults.
        """

        self.messages = fs.read_yaml(self.mesasges_path)
        

class Globals:
    def __init__(
            self,
            parent: Config
        ):
        """
        Initializes a global config object.
        """

        self.parent = parent

        # If we have the API enabled, load API endpoints
        if self.parent.use_api:
            self.endpoints = fs.read_yaml(self.parent.endpoint_path)