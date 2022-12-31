# [Skip to docs](docs/README.md)

---

<p align="center">
    <img src="https://humeman.com/files/humecord/hcheader.png" height="200">
</p>

# humecord
An advanced discord.py wrapper, designed to allow for easy creation of bots with less of the work.

## Features
* A wide array of helper functions to simplify development
* Designed to easily integrate with APIs/databases (-> easy sharding, multiple bots with the same data)
* Pre-command argument validation, data retrieval, and permission checking
* Very configurable
* Supports slash and message commands with no additional work
* Advanced development tools
    * Error logs are sent to a debug channel of your choice
    * View all logs directly from discord
    * Interactive Python console from the terminal/discord chat
* Very user-configurable: customizable settings with a few lines of YAML config and editable messages
* Easily extensible:
    * [humeman/statusreporter](https://github.com/humeman/statusreporter): Advanced status monitoring bot which can remotely restart, send commands to, monitor usage of any Humecord bot
    * [humeman/humetunes](https://github.com/humeman/humetunes): YouTube music commands, with advanced searching, filters, and more

## Components
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
    * Slash commands
    * Message commands
    * Message components
    * Modals

* Built in command set:
    * !dev - manages your bot, entirely from discord
    * !help - automatically compiled from your registered commands
    * !about - gives details about your bot, and fully customizable
    * !botban - ban users from using the bot (global, syncs to API if used)
    * !dm - dms a user, works with embeds and attachments
    * !exec - executes a function asynchronously from discord
    * !logs - interactive discord log viewer
    * !messages - allows users to edit bot messages
    * !overrides - allows users to make one bot override another for some event when multiple are in use
    * !profile - changes the bot's discord profile
    * !settings - allows users to change guild settings (settings in config.yml)
    * !syslogger - enables/disables error reporting for system logs
    * !useredit - changes the internal bot rank for a discord user

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
* Python 3.11 (recommended), 3.7 (required)
* [discord.py](https://github.com/rapptz/discord.py) 2.1.0 or higher

## Getting started
Read the documentation for Humecord by [clicking here](docs/README.md).

Read the [getting started guide]() for a full tutorial.

## Bots using Humecord
| Created by           | Bots                                                              |
|:--------------------:| ----------------------------------------------------------------- |
| humeman (me)         | [humebot](https://humeman.com/bots/humebot) - all of the below + moderation |
|                      | [teck tip bot](https://humeman.com/bots/tecktip) - copypastas, games, music |
|                      | [humetunes](https://humeman.com/bots/humetunes) - music |
|                      | [huskhook](https://humeman.com/bots/huskhook) - pterodactyl interface + minecraft server utils |
|                      | [guildmanager](https://humeman.com/bots/guildmanager) - hypixel & minecraft chatbots |
|                      | [statusreporter](https://github.com/humeman/statusreporter) - bot monitoring & server status |
|                      | [testcord](https://humeman.com/bots/testcord) - testing bot for new humecord releases |
| theseconddiarykeeper | [theseconddiarykeeper.com/bots](https://theseconddiarykeeper.com/bots) - just check here |
