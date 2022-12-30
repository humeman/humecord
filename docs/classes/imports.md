### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/imports

---
# humecord loader

class: `humecord.classes.imports.Imports`

instance: `humecord.bot.imports`

---
This document outlines how to use the Humecord Loader, located at `bot.loader`. This system is used to manage imports of commands, events, and loops, allowing for them to be reloaded without requiring a bot restart on the fly. 

## outline

The loader looks to your `imports.py` file to decide what needs to be imported.

A basic `imports.py` file is located in `classes/imports.py` and is formatted as:

```py
import humecord
humecord.add_path("extra/path") # Optional, if you want to import from another folder

class Imports:
    def __init__(self):
        self.loader = {
            "commands": {
                # v Command categories, used in !help
                "category1": [ 
                    {
                        "imp": "from commands import sample",
                        "module": "sample",
                        "class": "SampleCommand"
                    }
                ],
                "category2": [
                    # ...
                ]
            },
            "events": [
                {
                    "imp": "from events import sample",
                    "module": "sample",
                    "class": "SampleEvent"
                }
            ],
            "loops": [
                {
                    "imp": "from loops import sample",
                    "module": "sample",
                    "class": "SampleLoop"
                }
            ]
        }
```

Then, in your `main.py`:
```py
import humecord
humecord.bot.init("from classes import imports", "Imports") # If your imports.py path is different, change it here

humecord.bot.start()
```

## modules

Each module is defined as a simple dictionary with 3 keys:
* **imp**: full Python import line
    * ex: `from folder import file`
* **module**: module containing class
    * almost always the very last word in your Python import line
    * so, for our example: `file`
* **class**: the class in the file containing your command/event/loop
    * if your class in 'folder/file.py' is SampleCommand, use:
    * `SampleCommand`

So, fully written out:
```py
{
    "imp": "from folder import file",
    "module": "file",
    "class": "SampleCommand"
}
```

## reloading

The primary benefit of using the Humecord loader instead of traditional imports is that it allows you to reload every command/event/loop on the fly without restarting the bot entirely, preventing interruptions and taking far less time. There are several ways to do so:

### in the console:
* type 'reload' into the terminal, hit enter
* press the 'ins' button on your keyboard

### from discord:
* run the `reload` command

### from statusreporter:
* tmux send [window] reload