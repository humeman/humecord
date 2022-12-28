from re import M
import discord
import humecord
from humecord.utils import (
    discordutils,
    miscutils,
    components,
    dateutils,
    miscutils,
    debug
)

import time

class UserEditCommand:
    def __init__(
            self
        ):

        self.name = "useredit"

        self.description = "Manages a user's details."

        self.aliases = []

        self.permission = "bot.dev"
        
        self.subcommands = {
            "__syntax__": {
                "function": self.main,
                "description": "View a user's details.",
                "syntax": "[user]"
            }
        }

        self.permission_hide = True

        global bot
        from humecord import bot

    async def main(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb,
            editing: str = "global",
            gen_new: bool = True,
            uid: int = None
        ):

        # Try to get user
        if len(args) == 0:
            user = str(uid)

        else:
            user = args[1]

        try:
            user = discordutils.get_user(user)

        except:
            for char in "<@!>":
                user = user.replace(char, "")

            try:
                uid = int(user)

            except:
                await resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid user!",
                        f"Mention a user, or paste their ID."
                    )
                )
                return

            else:
                details = str(uid)
        
        else:
            # Get user's details
            uid = int(user.id)

            details = f"{user.name}#{user.discriminator}"

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
        if editing == "global":
            group_index = group_list.index(group_name)
            active_group = group_name

        group_details = f"{group['emoji']} [{group['name']}]"

        # Now, since local groups take priority, check if that's present
        if bot.config.self_api in user_db["per_bot"]:
            group_name = user_db["per_bot"][bot.config.self_api]

            if editing == "bot":
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

        elif editing == "bot":
            # We'll assume it's 'default'
            # Overwrite our group index - we're editing local values
            group_index = 0
            active_group = group_list[0]

        # Now, we'll set our editing dropdown.
        # First, we check if they're the owner - if so, they override everything.
        if message.author.id == bot.config.bot_owner:
            allow = True
            edit_list = group_list # Allow every group

        else:
            # Otherwise, they can only edit if they are above the other user in rank
            allow = False
            # So, first, get our own group index based on what we're editing.
            if editing == "global":
                author_index = group_list.index(udb["group"])
                allow = True

            else:
                # If they have no bot rank, just deny them no matter what.
                if bot.config.self_api in udb["per_bot"]:
                    author_index = group_list.index(udb["per_bot"][bot.config.self_api])
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
            components.create_button(
                message,
                label = f"Editing: {editing}",
                emoji = bot.config.lang["emoji"]["edit"],
                id = "editing",
                style = "secondary",
                callback = lambda *args: self.main(*args, "bot" if editing == "global" else "global", False, uid = uid),
                only_sender = True,
                row = 0
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
                components.create_dropdown(
                    message,
                    placeholder = f"Select a {editing} group",
                    id = "sel",
                    options = options,
                    row = 1,
                    only_sender = True,
                    callback = lambda *args: self.edit(*args, uid, editing)
                )
            )

        kw["view"] = components.create_view(buttons)

        # Check if botbanned
        if user_db["botban"] is not None:
            if user_db["botban"]["duration"] is None or user_db["botban"]["endsat"] > time.time():
                if user_db["botban"]["duration"] is not None:
                    # Permanent
                    detail = f" %-b% **Duration:** `Permanent`"

                else:
                    detail = f" %-b% **Until:** `{dateutils.get_timestamp(user_db['botban']['endsat'])}`\n %-b%**Banned by:** `{user_db['botban']['by']}`\n %-b%**Ban duration:** `{dateutils.get_timestamp(user_db['botban']['duration'])}`"

                fields.append(
                    {
                        "name": f"%-a% Botban",
                        "value": f"User is botbanned:\n %-b%**Reason:** {user_db['botban']['reason']}\n %-b%Issued at: `{dateutils.get_timestamp(user_db['botban']['started'])}`\n{detail}"
                    }
                )

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


        if gen_new:
            await resp.send(
                embed = embed,
                **kw
            )

        else:
            await resp.edit(
                embed = embed,
                **kw
            )


    async def edit(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb,
            values,
            uid,
            editing
        ):

        if len(values) == 0:
            return

        user_db = await bot.api.get(
            "users",
            "user",
            {
                "id": uid,
                "autocreate": True
            }
        )

        if editing == "bot":
            user_db["per_bot"][bot.config.self_api] = values[0]

        else:
            user_db["group"] = values[0]

        await bot.api.put(
            "users",
            "user",
            {
                "id": uid,
                "db": {
                    "group": user_db["group"],
                    "per_bot": user_db["per_bot"]
                }
            }
        )

        await self.main(
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb,
            preferred_gdb,
            editing,
            False,
            uid = uid
        )
