from humecord.utils import (
    discordutils,
    components,
    miscutils,
    debug,
    exceptions
)

import copy
import math
import time
import discord
from typing import Union

class MessagesCommand:
    def __init__(
            self
        ):

        self.name = "messages"

        self.description = "Manages messages sent by me in your server."

        self.aliases = []

        self.permission = "guild.admin"

        self.subcommands = {
            "__default__": {
                "function": self.list_,
                "description": "Lists all your settings."
            },
            #"__syntax__": {
            #    "function": self.edit,
            #    "description": "Manages your settings."
            #}
        }

        global bot
        from humecord import bot

    async def list_(
            self,
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb,
            values: list = [],
            location: str = "home",
            item: str = None,
            gen_new: bool = True,
            page: int = 0
        ):

        if len(values) == 0:
            # Set to default
            category_name = str(bot.config.messages_default_category)

        else:
            category_name = str(values[0])

        # Get section
        category = bot.config.messages[category_name]

        # Check permissions
        if not await bot.permissions.check(message.author, category["__details__"]["permission"]):
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid category!",
                    f"You need the `{category['__details__']['permission']}` permission to access that category."
                )
            )
            return

        groups = {}

        for group_name, messages in category.items():
            if group_name.startswith("__"):
                continue

            # Verify perms
            if not await bot.permissions.check(message.author, messages["__details__"]["permission"]):
                continue

            groups[group_name] = {
                "amount": 0,
                "details": messages["__details__"],
                "messages": []
            }

            for name, msg in messages.items():
                if name.startswith("__"):
                    continue

                groups[group_name]["amount"] += 1
                groups[group_name]["messages"].append(name)

        if location == "home":
            selected = "home"
            selected_group = ""

            # Compile into fields & buttons
            fields = []
            for group, details in groups.items():
                gr = details["details"]
                
                if gr["permission"] in ["bot.dev", "bot.owner"]:
                    ext = "\n*Dev only*"

                else:
                    ext = ""

                fields.append(
                    {
                        "name": f"%-a% {gr['emoji']}  {gr['name']} ({details['amount']})",
                        "value": f"{gr['description']}{ext}"
                    }
                )


            # Create embed
            embed = discordutils.create_embed(
                title = f"{message.guild.name} → Messages → {category['__details__']['name']}",
                fields = fields
            )

            # Iterate over sections
            options = {}
            for _category_name, _category_details in bot.config.messages.items():
                if "__details__" not in _category_details:
                    continue

                cat_d = _category_details["__details__"]

                options[_category_name] = {
                    "name": cat_d["name"],
                    "emoji": cat_d["emoji"],
                    "description": cat_d["description"],
                    "default": category_name == _category_name
                }

            ext_buttons = [
                components.create_dropdown(
                    message,
                    placeholder = "Select a category",
                    id = "sel_cat",
                    options = options,
                    row = 4,
                    callback = lambda *args: self.list_(*args, "home", None, False, page)
                )
            ]

        else:
            selected = ""
            selected_group = item

            print(groups)

            group = groups[item]

            max_pages = math.floor(len(group["messages"]) / 5)

            # Compile messages
            fields = []
            options = {}
            for msg_name in group["messages"][page * 5:(page + 1) * 5]:
                msg = bot.config.messages[category_name][selected_group][msg_name]

                try:
                    value = miscutils.follow(
                        gdb["messages"],
                        [category_name, selected_group, msg_name]
                    )

                except:
                    value = "*Default*"

                else:
                    value = "*Edited*"

                # Append
                fields.append(
                    {
                        "name": f"%-a% {msg['name']}",
                        "value": f"{msg['description']}\nSet to: {value}"
                    }
                )

                options[msg_name] = {
                    "name": msg["name"],
                    "emoji": category["__details__"]["emoji"],
                    #"description": msg["description"][:50]
                }

            if page == 0:
                backward_button = ["secondary", self.pass_]

            else:
                backward_button = ["primary", lambda *args: self.list_(*args, [category_name], "category", str(item), False, page - 1)]
            
            if page == max_pages:
                forward_button = ["secondary", self.pass_]

            else:
                forward_button = ["primary", lambda *args: self.list_(*args, [category_name], "category", str(item), False, page + 1)]

            ext_buttons = [
                components.create_dropdown(
                    message,
                    placeholder = "Select a message to edit",
                    id = "sel",
                    options = options,
                    row = 0, # self.message_page(*args, values, category_name, group_name, False, origin, editing, False, set_default = is_default["default"]),
                    callback = lambda *args: self.message_page(*args, category_name, group_name, False, page, None, False)
                ),
                components.create_button(
                    message,
                    label = "🡸",
                    id = "back",
                    style = backward_button[0],
                    callback = backward_button[1],
                    only_sender = True,
                    row = 3
                ),
                components.create_button(
                    message,
                    label = "🡺",
                    id = "forward",
                    style = forward_button[0],
                    callback = forward_button[1],
                    only_sender = True,
                    row = 3
                )
            ]

            embed = discordutils.create_embed(
                f"{message.guild.name} → Messages → {category['__details__']['name']} → {group['details']['name']}",
                fields = fields
            )

        buttons = [
            components.create_button(
                message,
                label = "🏠",
                id = "home",
                style = "success" if selected == "home" else "primary",
                callback = lambda *args: self.list_(*args, [category_name], "home", None, False, page),
                only_sender = True,
                row = 1
            )
        ]

        group_opts = {}

        if location != "group":
            for group, details in groups.items():
                gr = details["details"]

                group_opts[group] = {
                    "name": gr["name"],
                    "emoji": gr["emoji"],
                    "description": gr["description"][:50],
                    "default": group == selected_group
                }
                
                
            buttons.append(
                components.create_dropdown(
                    message,
                    placeholder = "Select a group to view",
                    id = "sel_gro",
                    options = group_opts,
                    row = 2, 
                    callback = lambda *args: self.list_(*args[:-1], [category_name], "group", args[-1][0], False)
                )
            )
            
        buttons += ext_buttons

        view = components.create_view(
            buttons
        )

        if gen_new:
            await resp.send(
                embed = embed,
                view = view
            )

        else:
            await resp.edit(
                embed = embed,
                view = view
            )

    async def format(
            self,
            gdb,
            setting
        ):
        # Get value
        try:
            value = copy.copy(miscutils.follow_path(gdb, setting["path"]))

        except:
            value = "**Error**: Value doesn't exist"

        else:
            # Run formatters
            for sample, format in setting["format"].items():
                if type(value) == type(sample):
                    # Find all %x%

                    rtype = None
                    if "%" in format:
                        ext = format.split("%", 1)[1]

                        if "%" in ext.split(" ")[0]:
                            # Get rule type
                            rtype = ext.split("%", 1)[0]

                    if rtype is not None:
                        # Replace
                        rule = rtype.lower()

                        return format.replace(
                            f"%{rtype}%",
                            await bot.args.format(
                                rule,
                                value,
                                {}
                            )
                        )

    async def pass_(
            self,
            *args
        ):
        pass

    async def message_page(
            self,
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb,
            values: list,
            category_name: str,
            group_name: str,
            gen_new: bool = False,
            origin: int = 0,
            editing: Union[str, None] = None,
            confirm_mode: bool = False,
            set_default: Union[str, None] = None
        ):

        if len(values) == 0:
            return

        # Get stuff
        category = bot.config.messages[category_name]
        group = category[group_name]

        msg_name = values[0]

        # Find message
        msg = group[msg_name]

        # Set default
        defaults = [
            "embed",
            "text",
            "both"
        ]

        if set_default is not None:
            # Check if message exists
            await self.generate_message(
                gdb,
                category_name,
                group_name,
                msg_name
            )

            ind = defaults.index(set_default) + 1

            if ind == len(defaults):
                ind = 0

            gdb["messages"][category_name][group_name][msg_name]["default"] = defaults[ind]

            # Put back
            await bot.api.put(
                bot.config.self_api,
                "guild",
                {
                    "id": message.guild.id,
                    "db": gdb
                }
            )

        # Find active value
        try:
            value = miscutils.follow(
                gdb["messages"],
                [category_name, group_name, msg_name]
            )

        except:
            is_default = {
                "all": True,
                "embed": True,
                "text": True,
                "default": msg["default"]
            }

            msg_value = msg

        else:
            is_default = {
                "all": False,
                "embed": False,
                "text": False
            }
            msg_value = copy.copy(value)

            if "embed" not in msg_value:
                if "embed" in msg:
                    msg_value["embed"] = msg["embed"]

                is_default["embed"] = True

            if "text" not in msg_value:
                if "text" in msg:
                    msg_value["text"] = msg["text"]

                is_default["text"] = True

            # Check if overridden
            if "default" in msg_value:
                is_default["default"] = msg_value["default"]

            else:
                is_default["default"] = msg["default"]

        if editing is None:
            # Default to the default value
            if is_default["default"] == "both":
                if msg["default"] == "both":
                    editing = "embed"

                else:
                    editing = msg["default"]

            else:
                editing = is_default["default"]

        # Get value
        fields = []

        # -> Embed
        if "embed" in msg_value:
            emb = await bot.args.format(
                "embed",
                msg_value["embed"],
                {
                    "shorten": True
                }
            )

            fields.append(
                {
                    "name": f"%-a% Embed",
                    "value": f"**Default:** {'Yes' if is_default['embed'] else 'No'}\n```yml\n{emb[:950]}{'...' if len(emb) > 950 else ''}```"
                }
            )

        if "text" in msg_value:
            fields.append(
                {
                    "name": f"%-a% Text",
                    "value": f"**Default:** {'Yes' if is_default['text'] else 'No'}\n```\n{msg_value['text'][:950]}{'...' if len(msg_value['text']) > 950 else ''}```"
                }
            )

        # Determine current default
        default = f"Currently, the **{is_default['default']}** version of this message is sent in your server."
        override_details = "To change this, press the `Default type` toggle button below." if msg["allow_type_override"] else "The type of this message cannot be overridden."
        edit_details = "To edit this message, select the type of message you'd like to edit using the `Edit` toggle button below, then reply with a new value (or click `reset` to reset it). You can also reply with a text file if the new message is too long to send in a normal message." if msg["allow_override"] else "The content of this message cannot be overridden."

        # Generate embed
        embed = discordutils.create_embed(
            f"Messages → {message.guild.name} → {category['__details__']['name']} → {group['__details__']['name']} → {msg['name']}",
            description = f"{msg['description']}\n\nTo view the full content of the selected message (see `Edit` button), click the `View full` button.\n\n{default}\n{override_details}\n\n{edit_details}",
            fields = fields
        )

        if confirm_mode:
            reset_callback = lambda *args: self.reset(*args, values, category_name, group_name, False, origin, editing)
            reset_label = f"Are you sure? Reset {editing}"

        else:
            reset_callback = lambda *args: self.message_page(*args, values, category_name, group_name, False, origin, editing, True)
            reset_label = f"Reset {editing}"
        
        buttons = [
            components.create_button(
                message,
                label = "🡸",
                id = "back",
                style = "primary",
                callback = lambda *args: self.list_(*args, [category_name], "group", group_name, False, origin),
                only_sender = True,
                row = 0
            ),
            components.create_button(
                message,
                label = f"Editing: {editing}",
                emoji = bot.config.lang["emoji"]["edit"],
                id = "editing",
                style = "secondary",
                callback = lambda *args: self.message_page(*args, values, category_name, group_name, False, origin, "text" if editing == "embed" else "embed", False),
                only_sender = True,
                row = 1
            ),
            components.create_button(
                message,
                label = f"View full {editing}",
                emoji = bot.config.lang["emoji"]["play"],
                id = "viewfull",
                style = "secondary",
                callback = lambda *args: self.send_full(*args, values, category_name, group_name, editing),
                only_sender = True,
                row = 1
            )
        ]

        if msg["allow_type_override"]:
            buttons.insert(
                2,
                components.create_button(
                    message,
                    label = f"Default type: {is_default['default']}",
                    emoji = bot.config.lang["emoji"]["info"],
                    id = "type",
                    style = "secondary",
                    callback = lambda *args: self.message_page(*args, values, category_name, group_name, False, origin, editing, False, set_default = is_default["default"]),
                    only_sender = True,
                    row = 1
                )
            )

        if not is_default[editing]:
            buttons.append(
                components.create_button(
                    message,
                    label = reset_label,
                    emoji = bot.config.lang["emoji"]["trash"],
                    id = "reset",
                    style = "danger",
                    callback = reset_callback,
                    only_sender = True,
                    row = 1
                )
            )

        view = components.create_view(buttons)

        # Add reply callback
        bot.replies.add_callback(
            resp.interaction.message.id,
            message.author.id,
            lambda *args: self.edit_message(resp, *args, values, category_name, group_name, editing, False, origin),
            delete_after = False
        )

        if gen_new:
            await resp.interaction.message.send(
                embed = embed,
                view = view
            )

        else:
            await resp.interaction.message.edit(
                embed = embed,
                view = view
            )

    async def generate_message(
            self,
            gdb,
            category_name,
            group_name,
            msg_name
        ):

        if category_name not in gdb["messages"]:
            gdb["messages"][category_name] = {}

        if group_name not in gdb["messages"][category_name]:
            gdb["messages"][category_name][group_name] = {}

        if msg_name not in gdb["messages"][category_name][group_name]:
            gdb["messages"][category_name][group_name][msg_name] = {}



    async def send_full(
            self,
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb,
            values,
            category_name,
            group_name,
            editing
        ):

        msg_name = values[0]

        # Find message
        msg = bot.config.messages[category_name][group_name][msg_name]

        # Get details
        category = bot.config.messages[category_name]
        group = category[group_name]

        try:
            value = miscutils.follow(
                gdb["messages"],
                [category_name, group_name, msg_name]
            )

        except:
            field = msg[editing]

        else:
            if editing in value:
                field = value[editing]
            
            else:
                field = msg[editing]

        # Get value
        if editing == "text":
            content = field
            ext = "txt"
        
        else:
            content = await bot.args.format(
                "embed",
                field,
                {
                    "shorten": False
                }
            )
            ext = "yml"
        
        kw = {}

        # Check length
        if len(content) > 4000:
            fname = f"data/tmp/messages-{time.time()}.txt"
            # Write to temp
            with open(fname, "w+") as f:
                f.write(content)

            # Attach as file
            kw["file"] = discord.File(fname, f"{message.guild.name}-{category_name}-{group_name}-{msg_name}.{ext}")

            description = "This message is too long to send in a single Discord message, so it's been attached as a file."

        else:
            # Add to embed
            description = f"```{ext}\n{content}```"

        # Send
        await resp.send(
            embed = discordutils.create_embed(
                f"Messages → {message.guild.name} → {category['__details__']['name']} → {group['__details__']['name']} → {msg['name']} → {editing[0].upper() + editing[1:]}",
                description = description
            ),
            **kw
        )

    async def edit_message(
            self,
            resp,
            message,
            new_resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb,
            data,
            values: list,
            category_name,
            group_name,
            editing,
            gen_new: bool = False,
            origin: int = 0
        ):
        # Make sure the message has content
        if message.content is None or len(message.content) == 0:
            # Check if they have a file instead
            err = None
            if len(message.attachments) > 0:
                # Get attachment
                attachment = message.attachments[0]

                # Check content type
                ctype = attachment.content_type

                if ";" in ctype:
                    ctype = ctype.split(";", 1)[0]

                # Should only be text/plain.
                if ctype != "text/plain":
                    await new_resp.send(
                        embed = discordutils.error(
                            message.author,
                            "Invalid message!",
                            "This file's content type is invalid. Upload a text file for me to read, or send the message directly."
                        )
                    )
                    return

                # Check file size
                # We'll cap this at 20 KB for now - no way it'll exceed that.
                if attachment.size > 1024 * 20:
                    await new_resp.send(
                        embed = discordutils.error(
                            message.author,
                            "Invalid file!",
                            f"This file is {miscutils.get_size(attachment.size, True, True)} in size, but the cap is 20KB for message uploads. Keep in mind that Discord's embed length limit is 6,000 characters, and their message length limit is 2,000 characters."
                        )
                    )
                    return

                # Download it
                try:
                    content = await discordutils.download_file(
                        attachment
                    )

                    content = content.decode("utf-8")

                except Exception as e:
                    await new_resp.send(
                        embed = discordutils.error(
                            message.author,
                            "Invalid file!",
                            f"I couldn't download that file: `{str(e)}`."
                        )
                    )
                    return
                    
            
            else:
                await new_resp.send(
                    embed = discordutils.error(
                        message.author,
                        "Invalid message!",
                        "Reply with text to change the setting to (or attach a text file)."
                    )
                )
                return

        else:
            content = message.content

        if len(values) == 0:
            return
        
        msg_name = values[0]

        # Find setting
        category = bot.config.messages[category_name]
        group = category[group_name]
        msg = group[msg_name]

        # Check if it can be edited
        if not msg["allow_override"]:
            await new_resp.send(
                embed = discordutils.error(
                    message.author,
                    "Can't edit message!",
                    "This message type cannot be edited."
                )
            )
            return
            

        # Try to validate
        if editing == "embed":
            valid, new = await bot.args.parse(
                "embed",
                content,
                {}
            )

        elif editing == "text":
            valid = True
            if len(content) > 2000:
                valid = False
                new = [f"Message limit is 2000 characters, but the message you sent is {len(content)} characters long. Consider using an embed."]

            else:
                new = content

        if not valid:
            lb = "\n"
            await new_resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid value!",
                    f"The value you specified is invalid:\n{lb.join([f'`{x}`' for x in new])}"
                )
            )
            return

        # Generate new value
        await self.generate_message(
            gdb,
            category_name,
            group_name,
            msg_name
        )

        gdb["messages"][category_name][group_name][msg_name].update(
            {
                editing: new
            }
        )

        # Put back
        await bot.api.put(
            bot.config.self_api,
            "guild",
            {
                "id": message.guild.id,
                "db": gdb
            }
        )

        await self.message_page(
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb,
            values, 
            category_name,
            group_name,
            False,
            origin,
            editing,
            False
        )


    # lambda *args: self.reset(*args, values, category_name, group_name, False, origin, editing)
    async def reset(
            self,
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb,
            values: list,
            category_name,
            group_name,
            gen_new,
            origin: int,
            editing: str
        ):

        if len(values) == 0:
            return
        
        msg_name = values[0]

        # Check if message is in guild
        try:
            value = miscutils.follow(
                gdb["messages"],
                [category_name, group_name, msg_name]
            )

        except:
            # Invalid
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Can't reset message.",
                    f"That message isn't overridden in this server."
                )
            )
            return

        # Now, delete the message type
        if editing not in value:
            await resp.send(
                embed = discordutils.error(
                    message.author,
                    "Can't reset message.",
                    f"Type {editing} isn't overridden in this server."
                )
            )
            return

        # Kill
        del gdb["messages"][category_name][group_name][msg_name][editing]

        # Put back
        await bot.api.put(
            bot.config.self_api,
            "guild",
            {
                "id": message.guild.id,
                "db": gdb
            }
        )

        await self.message_page(
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb,
            values,
            category_name,
            group_name,
            False,
            origin,
            editing,
            False
        )