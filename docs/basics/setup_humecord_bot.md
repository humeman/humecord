### [humecord](../..)/[docs](../README.md)/[basics](./README.md)/install_humecord

---
# humecord tutorial: part 3
## setting up a humecord bot

This document outlines how to create a Humecord bot.

---
## procedure
Begin by creating a folder to contain all of your bot's files.

Within that folder, we'll need to create a few files:

__main.py__
This is the file you'll use to start your bot. It imports humecord, specifies an import file (see below), and starts the bot.
```py
# main.py
import humecord

humecord.bot.init("from classes import imports", "imports")
humecord.bot.start()
```

__classes/imports.py__
The imports.py file is what Humecord uses to load all your custom commands, events, and loops. You can learn more about how it works at [docs/classes/imports](/docs/classes/imports.md), or in a later part of this tutorial.
```py
# classes/imports.py
class Imports:
    def __init__(self):
        self.loader = {
            "commands": {

            },
            "events": [

            ],
            "loops": [

            ]
        }
```
At this point, you're ready to run your bot for the first time!
```sh
# Linux
$ python3 main.py

# Windows
> py main.py
```

When the bot starts for the first time, you'll get an error message stating that no configuration file was found and a prompt to automatically generate one. Type "y" into the terminal and press ENTER to generate it for you.

Then, you can press CTRL + C to exit.


---
## next steps
[Part 3: Set up a Humecord bot](./setup_humecord_bot.md)