### [humecord](../..)/[docs](../README.md)/[classes](./README.md)/loader

---
# humecord loader

class: `humecord.classes.loader.Loader`

instance: `humecord.bot.loader`

---
This document outlines how to use the Humecord Loader, located at `bot.loader`. This system is used to manage imports of commands, events, and loops, allowing for them to be reloaded on the fly without requiring a bot restart. 


## user documentation
⚠️ **NOTE**: You're probably looking for the tutorial on **[how to use the loader](../basics/loader.md)**. This document is only the technical outline for how the loader works.

## outline
* **async .load(starting, safe_stop)**:

    Loads (or reloads) the bot.

    *Params:*
    - `starting` (bool = False): If True, loads for the first time (ie: bot just started).
    - `safe_stop` (bool = False): Gracefully shuts down the bot's components first.
* **async .load_config()**:
    
    Reloads the bot's config files.

* **async .stop_all(safe_stop)**:

    Shuts down all the bot's running loops, and then, the loop handler.

    *Params:*
    - `safe_stop` (bool = False): If True, loops/handler will be given some time to finish before closing.