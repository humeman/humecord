# 🤖 humecord
An advanced discord.py wrapper, designed to allow for easy creation of bots with less of the work.

## Features
* Easy to use handlers for:
    * All discord.py events
    * Commands
    * Loops

* Storage interfaces for:
    * HTTP APIs
    * Websockets
    * Local files
    * MySQL

* Supports:
    * Normal message commands
    * Message components
    * Slash commands

* Built in command set:
    * !dev - manages your bot, entirely from discord
    * !help - automatically compiled from your registered commands
    * !about - gives details about your bot, and fully customizable

* Advanced development tools
    * Error reporting and logging, in both your console & a Discord channel
    * Fully interactive Python shell in a Discord channel

* Lots of time-saving features
    * A wide and ever-growing array of development utilities for use in your code
    * Handlers and such to make writing any feature easier than ever

## Support
You can get any support you need with developing using Humecord, as well as help with using my own bots, in the [HumeBots discord](https://discord.gg/nhaRXY28Yn).

Feel free to create an issue here if you believe you found an issue or improvement in the code itself.

And, head over to the Discussions tab for any Humecord-related question if you don't want to use the discord.

## Extensions
You can find details on implementing StatusReporter support, which is my monitoring bot for any Humecord instance, at:
* the [humeman/statusreporter](https://github.com/humeman/statusreporter) github repo
* the docs: [docs/misc/status](docs/misc/status.md)

Info on creating a Humecord compatible API and websocket is listed at [docs/interfaces](docs/interfaces).

You can, alternatively, create your own interface to support whatever storage system you use. Learn more [here](docs/interfaces/create.md).

## Requirements
Humecord runs on:
* Python 3.6 or higher
* discord.py 2.0.0a

## Getting started
Read the documentation for Humecord by [clicking here](docs).

To install it:
```sh
$ git clone https://github.com/humeman/humecord
$ mv humecord ~/.local/lib/python3.[press tab]/site-packages
```

## Bots using Humecord
| Created by           | Bots                                                              |
|:--------------------:| ----------------------------------------------------------------- |
| humeman (me)         | [humebot](https://humeman.com/bots/humebot) - all of the below, merged |
|                      | [teck tip bot](https://humeman.com/bots/tecktip) - copypastas |
|                      | [humetunes](https://humeman.com/bots/humetunes) - music |
|                      | [huskbot](https://humeman.com/bots/tecktip) - moderation |
|                      | [huskhook](https://humeman.com/bots/huskhook) - pterodactyl interface + minecraft server utils |
|                      | [guildmanager](https://humeman.com/bots/guildmanager) - hypixel & minecraft chatbots |
|                      | [statusreporter](https://github.com/humeman/statusreporter) - bot monitoring & server status |
|                      | [testcord](https://humeman.com/bots/testcord) - testing bot for new humecord releases |
|                      | [yuno](https://humeman.com/bots/humebot) - reskin of humebot, requested by [theseconddiarykeeper](https://github.com/TheSecondDiaryKeeper) |
| theseconddiarykeeper | Currently working on migrating his bots to Humecord. 
|                      | Check back soon.