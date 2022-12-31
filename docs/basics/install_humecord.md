### [humecord](../..)/[docs](../README.md)/[basics](./README.md)/install_humecord

---
# humecord tutorial: part 2
## installing humecord

This document outlines how to install Humecord and set up some boilerplate code.

---
## procedure
Open up a terminal of your choice. If you're on Windows, these steps are a bit more complicated. Consider installing [WSL](https://docs.microsoft.com/en-us/windows/wsl/install), or check out the bottom of the page for a more vanilla install option.

### Linux/Mac Install

You'll need to install `git`, `python3`, and `python3-pip` from your preferred package manager before beginning. Make sure your Python version is 3.7 (3.11 is recommended) or higher.

__Clone the Humecord repository__
```sh
$ git clone https://github.com/humeman/humecord
$ cd humecord
```

__Install dependencies__
```sh
$ pip3 install -r requirements.txt
```

__Install Humecord to site-packages__
```sh
# You may need to change either 'python3.8' or the entire target directory entirely based on your install. Press the tab key if in doubt.
$ ln -s [/full/path/to/humecord/repo]/humecord /home/[yourusername]/.local/lib/python3.8/site-packages/humecord
```

__Install discord.py__
```sh
$ cd ..
$ git clone https://github.com/Rapptz/discord.py
$ cd discord.py
$ pip3 install .
```

__Optional: Test install__
```sh
$ python3
>> import humecord
```
A full-screen outline should appear, with the top bar labeled `Humecord is initializing...`, if everything is working properly.

Press Ctrl+C to stop Humecord, then Ctrl+D to exit the Python shell once you're done.
*Bug notice: If nothing appears when you type into your terminal, press Ctrl+C once, type `stty sane`, and press ENTER again. Work in progress. :)*

### Windows Install

__Prerequisites:__
* Install [git for windows](https://gitforwindows.org/)
* Install [Python 3.10 or later](https://www.python.org/downloads/windows/)
    * Make sure you install `pip` and `py launcher` at the minimum.
    * If asked later in the install to disable the PATH length limit, make sure you do so or you might not be able to run any Python commands.

Restart any terminals before starting below to ensure the PATH variable is updated -- otherwise you'll get command not found errors.

Open up a Windows Powershell instance and execute the following commands, one by one:
__Clone the Humecord repository__
```
> git clone https://github.com/humeman/humecord
> cd humecord
```

__Install dependencies__
```
> py -m pip install -r requirements.txt
```

__Install Humecord to site-packages__
First, find and copy your Python site packages directory:
```
> py -m site --user-site
```
Then, move Humecord to that directory.
```
> cd ..
# EXAMPLE. Replace the final argument with whatever you found in the last step.
> mv humecord C:\Users\humeman\AppData\Roaming\Python\Python310\site-packages
```

__Install discord.py__
```
> git clone https://github.com/Rapptz/discord.py
> cd discord.py
> py -m pip install .
```

__Optional: Test install__
```
> py
>> import humecord
```
A full-screen outline should appear, with the top bar labeled `Humecord is initializing...`, if everything is working properly.

Press CTRL+C to close Humecord, then type `quit()` and press ENTER to exit the python shell once you're done.

---
## next steps
[Part 3: Set up a Humecord bot](./setup_humecord_bot.md)