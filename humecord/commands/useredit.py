"""
/useredit: humecord base commands

Views and edits a user's settings.
"""

import time
from typing import Optional, Union

import discord

import humecord

from humecord.classes import (
    discordclasses
)

from humecord.utils import (
    discordutils,
    dateutils
)

class UserEditCommand(humecord.Command):
    def __init__(
            self
        ) -> None:
        self.name = "useredit"
        self.description = "Views and edits a user's settings."
        self.command_tree = {
            "%user%": self.run
        }
        self.args = {
            "user": {
                "type": "user",
                "required": True,
                "description": "User to view/edit."
            }
        }
        self.messages = {}
        self.dev = True
        self.perms = "bot.dev"
        self.default_perms = "guild.admin"

        global bot
        from humecord import bot

    async def run(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context,
            using_global: bool = True,
            user: Optional[Union[discord.User, discord.Member]] = None
        ) -> None:
        # Get some details
        if user is None:
            user = ctx.args.user

        uid = user.id
        details = str(user)

        # Get user
        user_db = await bot.api.get(
            "users",
            "user",
            {
                "id": uid,
                "autocreate": True
            }
        )

        group_list = list(bot.config.globals.groups)

        # Get group
        group_name = user_db["group"]
        group = bot.config.globals.groups[group_name]

        # Append info about that group
        fields = [
            {
                "name": f"%-a% Global group",
                "value": f"{group['emoji']} {group['name']}\n %-b% {group['description']}"
            }
        ]

        # Get our group index, and set active values
        if using_global:
            group_index = group_list.index(group_name)
            active_group = group_name

        group_details = f"{group['emoji']} [{group['name']}]"

        # Now, since local groups take priority, check if that's present
        if bot.config.self_api in user_db["per_bot"]:
            group_name = user_db["per_bot"][bot.config.self_api]

            if not using_global:
                # Overwrite our group index - we're editing local values
                group_index = group_list.index(group_name)
                active_group = group_name

            # Set new details
            group = bot.config.globals.groups[group_name]
            group_details = f"{group['emoji']} [{group['name']}]"

            # And append a field
            fields.append(
                {
                    "name": f"%-a% Bot group",
                    "value": f"{group['emoji']} {group['name']}\n %-b% {group['description']}"
                }
            )

        elif not using_global == "bot":
            # We'll assume it's 'default'
            # Overwrite our group index - we're editing local values
            group_index = 0
            active_group = group_list[0]

        # Now, we'll set our editing dropdown.
        # First, we check if they're the owner - if so, they override everything.
        if ctx.user.id == bot.config.bot_owner:
            allow = True
            edit_list = group_list # Allow every group

        else:
            # Otherwise, they can only edit if they are above the other user in rank
            allow = False
            # So, first, get our own group index based on what we're editing.
            if using_global:
                author_index = group_list.index(ctx.udb["group"])
                allow = True

            else:
                # If they have no bot rank, just deny them no matter what.
                if bot.config.self_api in ctx.udb["per_bot"]:
                    author_index = group_list.index(ctx.udb["per_bot"][bot.config.self_api])
                    allow = True

            # To make sure we don't allow through users with no bot rank
            if allow:
                # Check if the author's group is above the other's
                if author_index <= group_index:
                    allow = False

                # And they can only promote up to one below their own rank.
                else:
                    edit_list = group_list[:author_index]

        kw = {}

        buttons = [
            await bot.interactions.create_button(
                "editing",
                callback = lambda *args: self.run(*args, not using_global, user),
                sender = ctx.user,
                style = humecord.ButtonStyles.GRAY,
                emoji = bot.config.lang["emoji"]["edit"],
                label = f"Editing {'global' if using_global else bot.config.self_api} rank",
                row = 1
            )
        ]

        # Make sure they're allowed to edit
        if allow:
            # Add in our dropdown for rank editing
            # First, create options
            options = {}
            
            for name in edit_list:
                # Get the group
                group_ = bot.config.globals.groups[name]

                options[name] = {
                    "name": group_["name"],
                    "emoji": group_["emoji"],
                    "description": group_["description"][:50],
                    "default": active_group == name
                }

            buttons.append(
                await bot.interactions.create_select(
                    name = "sel",
                    sender = ctx.user,
                    placeholder = f"Change the user's {'global' if using_global else 'local'} group",
                    options = options,
                    callback = lambda *args: self.set_group(*args, using_global, user),
                    row = 0
                )
            )

        # Check if botbanned
        if user_db["botban"] is not None:
            if user_db["botban"]["duration"] is None or user_db["botban"]["endsat"] > time.time():
                if user_db["botban"].get("duration") is None:
                    # Permanent
                    detail = f"%-b% **Duration:** `Permanent`"

                else:
                    detail = f"%-b% **Until:** `{dateutils.get_timestamp(user_db['botban']['endsat'])}`\n%-b%**Ban duration:** `{dateutils.get_timestamp(user_db['botban']['duration'])}`"

                fields.append(
                    {
                        "name": f"%-a% Botban",
                        "value": f"User is botbanned:\n%-b% **Reason:** {user_db['botban']['reason']}\n%-b% **Banned by:** `{user_db['botban']['by']}`\n%-b% **Issued at:** `{dateutils.get_timestamp(user_db['botban']['started'])}`\n{detail}"
                    }
                )

                # Add a button to undo it
                buttons.append(
                    await bot.interactions.create_button(
                        "unban",
                        callback = lambda *args: self.unban(*args, using_global, user),
                        sender = ctx.user,
                        style = humecord.ButtonStyles.GRAY,
                        emoji = bot.config.lang["emoji"]["trash"],
                        label = f"Unban",
                        row = 1
                    )
                )

        kw["view"] = await bot.interactions.create_view(buttons)

        ext = []
        if uid == bot.config.bot_owner:
            ext.append(f"This user is the owner of {bot.config.cool_name}.")

        ext = "\n".join(ext)

        if ext != "":
            ext = f"\n{ext}"

        embed = discordutils.create_embed(
            f"{group_details} {details}",
            f"Editing: <@{uid}> (`{uid}`)\nThis user was first seen on `{dateutils.get_timestamp(user_db['created_at']).strip()}`.{ext}",
            fields = fields,
            color = "invisible"
        )

        await resp.edit(
            embed = embed,
            **kw
        )

    async def set_group(
            self,
            resp: humecord.ResponseChannel,
            ctx: humecord.Context,
            using_global: bool,
            user: Union[discord.Member, discord.User]
        ):

        value = ctx.values[0]

        user_db = await bot.api.get(
            "users",
            "user",
            {
                "id": user.id,
                "autocreate": True
            }
        )

        if not using_global:
            user_db["per_bot"][bot.config.self_api] = value

        else:
            user_db["group"] = value

        await bot.api.put(
            "users",
            "user",
            {
                "id": user.id,
                "db": {
                    "group": user_db["group"],
                    "per_bot": user_db["per_bot"]
                }
            }
        )

        await self.run(
            resp,
            ctx,
            using_global,
            user
        )

    async def unban(
            self,
            resp: humecord.ResponseChannel,
            ctx: humecord.Context,
            using_global: bool,
            user: Union[discord.Member, discord.User]
        ):
        user_db = await bot.api.get(
            "users",
            "user",
            {
                "id": user.id,
                "autocreate": True
            }
        )

        await bot.api.put(
            "users",
            "user",
            {
                "id": user.id,
                "db": {
                    "botban": None,
                    "botban_history": [
                        *user_db["botban_history"],
                        {
                            **user_db["botban"],
                            "end_reason": "Not specified."
                        }
                    ]
                }
            }
        )

        if user is not None:
            try:
                await user.send(
                    **(
                        await bot.messages.get(
                            ctx.gdb,
                            ["dev", "botban", "unban_dm"],
                            {
                                "note": "Not specified.",
                                "by": f"{ctx.user}"
                            },
                            {
                                "note": False
                            },
                            ext_placeholders = {
                                "user": user
                            }
                        )
                    )
                )

            except Exception as e:
                pass

        await self.run(
            resp,
            ctx,
            using_global,
            user
        )

