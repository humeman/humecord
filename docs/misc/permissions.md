# permissions system

This document outlines how the HumeCord discord permission system works.
These permissions are used everywhere - command permissions, interactions,
permission overrides, and so on.

## basic outline

Here's a sample permission:

`guild.admin`

Before the period specifies where to look for the specified permissions.
For example, if you want to check for admin in a server or for specific 
permissions, you'll have to use the `guild.` prefix.

To access things outside of the guild, like if the user is a developer:

`bot.dev`

## chaining

Permissions can be combined with a `+` to use multiple.

For example:

`guild.admin+bot.dev` will allow any guild admins or bot developers
to use the command. You can chain up to 10 permissions together in one
string and still have it be valid.

## guild permissions

Guild permissions are special in that they can be defined with users,
roles, permissions, and so on.

For example:

`guild.role[123,456]`

will allow people with role IDs 123 and 456 to run the command.

Permissions that accept a number of arguments, specified with brackets
and commas, will be denoted as `argument permissions`.

## negating permissions

Permissions can be negated with a `!`.

For example:

`!guild.role[123]` will disallow anyone with the role ID `123`.

## the complete permission list
### bot
* `bot.dev` - Members listed in bot.config.devs

* `bot.owner` - Bot's owner, found in bot.config.owner

* `bot.mods` - Members listed in bot.config.mods

* `bot.self` - Only the bot itself. Not sure why you'd want to use this though.

* `bot.none` - No one.

* `bot.vip` - VIP members (later will include those who've voted today, or patreon)

### guild
* `guild.admin` - Members of a guild with the administrator permission
    * Can also be accomplished with `guild.permission[admin]`

* `guild.mod` - People with general moderation permissions.
    * Defined in bot.config.mod_perms

* `guild.role[args]` - Members with a role (found by ID).
    * Ex: `guild.role[123,456]` will allow members with any role with ID 123 or 456

* `guild.rolename[args]` - Same as the above, but searches by name instead of ID.
    * Ex: `guild.rolename[cool role,cooler role]` will allow anyone with roles "cool role" or "cooler role" to execute the command
    * Beware: This can be abused by people that can create roles, since it only searches by name. Always use ID where possible.

* `guild.member[args]` - Guild members (found by ID).
    * Ex: `guild.member[123]` will allow a user with ID 123

* `guild.join[arg]` - By join date
    * Ex: `guild.join[600]` will only allow someone to use a command if they've been in the guild for 10 minutes or longer.

* `guild.nitro` - Requires someone to be nitro boosting a guild.

### user
* `user.created[arg]` - Same as `guild.join`, but goes by account creation date instead of guild join.
    * Ex: `user.created[3600]` will allow anyone with an account older than 1 hour.
    
* `user.flags[args]` - Checks if a user has a profile flag.
    * Ex: `user.flags[verified_bot_developer,partner]` will allow any verified bot developer or partner.
    * A full list of flags can be found [here](https://discordpy.readthedocs.io/en/master/api.html#discord.PublicUserFlags).
