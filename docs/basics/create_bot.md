### [humecord](../..)/[docs](../README.md)/[basics](./README.md)/create_bot

---
# humecord tutorial: part 1
## creating a bot

This document outlines how to create a Discord bot.

---
## procedure
1. First, head over to the Discord Developer Portal. This is where you manage the various features of your bot -- name, invite link, permissions, token, and so on. You may be asked to sign into your Discord account again.
    You can access this at [discord.com/developers/applications](https://discord.com/developers/applications).
2. Create an application by pressing the `New Application` button at the top of the screen.
    ![New Application button on Discord Developer Portal](https://humeman.com/files/humecord/1-newapplication.png)
3. Enter the name of your bot and click create. *Note that this is not the same name that will be displayed as the username of the bot across Discord clients, but users will still see the name when they attempt to add it to a server. Make sure it's something relevant!*
    ![Bot name](https://humeman.com/files/humecord/2-botname.png)
4. Set a description, and/or a profile picture for this new application. *The profile picture chosen here is only displayed when inviting the bot, just like the application name. The description is where you specify your bot's about me tag. Great place for a help command, instructions, or an invite -- check down below for more!*
    ![Application settings](https://humeman.com/files/humecord/3-applicationsettings.png)
5. Move over to the Bot tab on the left panel, then click the `Add Bot` button.
    ![Create bot](https://humeman.com/files/humecord/4-createbot.png)
6. Change the bot's username and profile picture to something suitable. This will be displayed across Discord clients.
    ![Bot profile](https://humeman.com/files/humecord/5-botprofile.png)
7. Obtain a bot token by clicking on `Reset Token`, then `Copy`. This token has to be saved in a safe place and kept secret, as anyone who has access to it can run your bot on your behalf. Ensure it's not being uploaded to Github if you're uploading your code there! We'll use this later when we configure Humecord.
    ![Reset token](https://humeman.com/files/humecord/6-resettoken.png)
    ![Copy token](https://humeman.com/files/humecord/7-copytoken.png#)
8. Enable intents. At the bottom of the page, 3 "intents" of interest are listed -- presence, server members, and message content. If you plan on interacting with any of these three, make sure to turn them on! By default, Humecord uses all of them, so it doesn't hurt to turn them all on. You'll have to get verification from Discord if your bot ever passes 100 servers to continue using them, but before then, you're good to go.
    ![Enable intents](https://humeman.com/files/humecord/8-intents.png)
9. Finally, we'll create an invite and join the bot to your server. Head over to the OAuth2 tab on the left panel, then click URL Generator below that.
    ![OAuth2 - URL Generator](https://humeman.com/files/humecord/9-oauth2.png)
10. Under scopes, check `bot` and `applications.commands`. The first permission makes the generated invite join the bot user into the specified server, and the second allows you to create slash commands.
    ![Bot and Application Commands scopes](https://humeman.com/files/humecord/10-scopes.png)
11. Select the permissions your bot will be given by default. For this demo, we'll give it Administrator -- but if you're ever making the bot public, it's advised that you try to be a bit more precise with which permissions you're using for security purposes. Then, grab your invite URL by clicking the `Copy` button at the bottom of the page. Save this along with your token -- it's good to have it on hand!
    ![Finalize invite](https://humeman.com/files/humecord/11-permissions.png)

You're all set! Use the invite you copied to add your bot to a testing server of your choice by pasting it into a browser and following the prompt normally. Make sure it's a server you have a decent set of permissions in, since to use Humecord's full debugging potential you'll need to create your bot its own text channel. 

---
## next steps
[Part 2: Installing Humecord](./install_humecord.md)