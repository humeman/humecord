import discord
import time
from typing import Union

import humecord

class Permissions:
    def __init__(self, _bot):
        global bot
        bot = _bot

        self.bot = {
            "dev": self.BotPermissions.dev,
            "owner": self.BotPermissions.owner,
            "mod": self.BotPermissions.mod,
            "self": self.BotPermissions.self,
            "none": self.BotPermissions.none,
            "vip": self.BotPermissions.vip
        }

        self.guild = {
            "admin": self.GuildPermissions.admin,
            "mod": self.GuildPermissions.mod,
            "permission": self.GuildPermissions.permission,
            "role": self.GuildPermissions.role,
            "rolename": self.GuildPermissions.rolename,
            "member": self.GuildPermissions.member,
            "join": self.GuildPermissions.join,
            "nitro": self.GuildPermissions.nitro
        }

        self.user = {
            "created": self.UserPermissions.created,
            "flags": self.UserPermissions.flags
        }

        self.permission_dir = [x for x in dir(discord.Permissions) if (not x.startswith("_")) and type(getattr(discord.Permissions, x)) == discord.flags.flag_value]
        self.user_dir = [x for x in dir(discord.PublicUserFlags) if (not x.startswith("_")) and type(getattr(discord.PublicUserFlags, x)) == discord.flags.flag_value]

        self.mod_perms = []
        for perm in bot.config.mod_perms:
            self.mod_perms.append(self.expand_perm(perm))
        
    def expand_perm(
            self,
            perm: str
        ):
        if perm not in self.permission_dir:
            raise humecord.utils.exceptions.InvalidPermission(f"Permission {perm} does not exist")

        return perm

    async def check(
            self,
            member: Union[discord.Member, discord.User],
            permission: str
        ):

        if type(member) == discord.Member:
            valid = ["bot", "guild", "user"]

        elif type(member) == discord.User:
            valid = ["bot", "user"]

        else:
            raise humecord.utils.exceptions.InvalidUser(f"User must be of type discord.Member or discord.User")

        # Parse into rules
        rules = permission.split("+")

        if len(rules) == 0:
            return False

        for rule in rules:
            # Check if negating
            final = True
            if rule.startswith("!"):
                final = False
                rule = rule[1:]

            # Check for args
            if "[" in rule and "]" in rule:
                rule, arg_raw = rule.split("[", 1)

                args = arg_raw[:-1].split(",")

            else:
                args = []

            if "." not in rule:
                raise humecord.utils.exceptions.InvalidPermission(f"Permission {rule} has no separator")
            
            category, rule = rule.split(".", 1)

            if category not in valid:
                raise humecord.utils.exceptions.InvalidPermission(f"Permission {category} isn't valid: {', '.join(valid)} (make sure discord.Member is being passed for guild rules)")

            checks = getattr(self, category)
            
            if rule not in checks:
                raise humecord.utils.exceptions.InvalidPermission(f"Rule {rule} isn't in category {category}")

            if await checks[rule](member, args) is True:
                return True

        return False


    class BotPermissions:
        async def dev(member, args):
            return member.id in bot.config.devs

        async def owner(member, args):
            return member.id == bot.config.devs[0]

        async def mod(member, args):
            return member.id in bot.config.mods or member.id in bot.config.devs

        async def self(member, args):
            return member.id == bot.client.user.id

        async def none(member, args):
            return False
        
        async def vip(member, args):
            raise humecord.utils.exceptions.NotImplemented("The VIP system has not yet been added.")

    class GuildPermissions:
        async def admin(member, args):
            return member.guild_permissions.administrator

        async def mod(member, args):
            perms = member.guild_permissions
            for perm in bot.permissions.mod_perms:
                if getattr(perms, perm) is True:
                    return True

            return False

        async def permission(member, args):
            perms = member.guild_permissions
            for perm in args:
                if perm not in humecord.bot.permissions.permission_dir:
                    raise humecord.utils.exceptions.InvalidPermission(f"Permission {perm} does not exist")

                if getattr(perms, perm) is True:
                    return True

            return False

        async def role(member, args):
            roles = [x.id for x in member.roles]
            for role in args:
                try:
                    if int(role) in roles:
                        return True

                except:
                    raise humecord.utils.exceptions.InvalidPermission(f"Role ID {role} isn't an integer")

            return False

        async def rolename(member, args):
            roles = [x.name.lower() for x in member.roles]
            for role in args:
                if role.lower() in roles:
                    return True

            return False

        async def member(member, args):
            for mid in args:
                try:
                    if int(mid) == member.id:
                        return True

                except:
                    raise humecord.utils.exceptions.InvalidPermission(f"Member ID {mid} isn't an integer")

            return False

        async def join(member, args):
            if len(args) != 1:
                raise humecord.utils.exceptions.InvalidPermission(f"guild.join accepts only one argument")

            try:
                delay = int(args[0])

            except:
                raise humecord.utils.exceptions.InvalidPermission(f"guild.join's argument must be an integer")

            return member.joined_at.timestamp() <= int(time.time()) - delay

        async def nitro(member, args):
            return member.id in [x.id for x in member.guild.premium_subscribers]

    class UserPermissions:
        async def created(member, args):
            if len(args) != 1:
                raise humecord.utils.exceptions.InvalidPermission(f"member.created accepts only one argument")

            try:
                delay = int(args[0])

            except:
                raise humecord.utils.exceptions.InvalidPermission(f"member.created's argument must be an integer")

            return member.created_at.timestamp() <= int(time.time()) - delay

        async def flags(member, args):
            flags = member.public_flags
            for flag in args:
                if flag not in bot.permissions.user_dir:
                    raise humecord.utils.exceptions.InvalidPermission(f"User flag {flag} doesn't exist")

                if getattr(flags, flag) is True:
                    return True

            return False