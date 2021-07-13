from humecord.utils import (
    discordutils,
    components,
    miscutils,
    debug
)

import copy
import math

class SettingsCommand:
    def __init__(
            self
        ):

        self.name = "settings"

        self.description = "Manages my settings in your server."

        self.aliases = ["config", "configuration"]

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
            location: str = "home",
            item: str = None,
            gen_new: bool = True,
            page: int = 0
        ):

        categories = {}

        for name, setting in bot.config.settings.items():
            # Check if category exists, first
            if setting["category"] not in categories:
                categories[setting["category"]] = {
                    "amount": 0,
                    "details": bot.config.settings_categories[setting["category"]],
                    "settings": []
                }

            categories[setting["category"]]["amount"] += 1
            categories[setting["category"]]["settings"].append(name)

        if location == "home":
            selected = "home"
            selected_category = ""

            # Compile into fields & buttons
            fields = []
            for category, details in categories.items():
                cat = details["details"]
                fields.append(
                    {
                        "name": f"%-a% {cat['emoji']}  {cat['name']} ({details['amount']})",
                        "value": cat["description"]
                    }
                )

            # Create embed
            embed = discordutils.create_embed(
                title = f"{message.guild.name}'s settings",
                fields = fields
            )

            ext_buttons = []

        else:
            selected = ""
            selected_category = item

            category = categories[item]

            max_pages = math.floor(len(category["settings"]) / 5)

            # Compile settings
            fields = []
            options = {}
            for setting_name in category["settings"][page * 5:(page + 1) * 5]:
                setting = bot.config.settings[setting_name]

                value = await self.format(
                    gdb,
                    setting
                )

                # Append
                fields.append(
                    {
                        "name": f"%-a% {setting['name']}",
                        "value": f"{setting['description']}\nSet to: {value}"
                    }
                )

                options[setting_name] = {
                    "name": setting["name"],
                    "emoji": category["details"]["emoji"],
                    "description": setting["description"]
                }

            if page == 0:
                backward_button = ["secondary", self.pass_]

            else:
                backward_button = ["primary", lambda *args: self.list_(*args, "category", str(item), False, page - 1)]
            
            if page == max_pages:
                forward_button = ["secondary", self.pass_]

            else:
                forward_button = ["primary", lambda *args: self.list_(*args, "category", str(item), False, page + 1)]

            ext_buttons = [
                components.create_dropdown(
                    message,
                    placeholder = "Select a setting to edit",
                    id = "sel",
                    options = options,
                    row = 0,
                    callback = lambda *args: self.setting_page(*args, False, int(page))
                ),
                components.create_button(
                    message,
                    label = "🡸",
                    id = "back",
                    style = backward_button[0],
                    callback = backward_button[1],
                    only_sender = True,
                    row = 2
                ),
                components.create_button(
                    message,
                    label = "🡺",
                    id = "forward",
                    style = forward_button[0],
                    callback = forward_button[1],
                    only_sender = True,
                    row = 2
                )
            ]

            embed = discordutils.create_embed(
                f"{message.guild.name} → {category['details']['name']}",
                fields = fields
            )

        buttons = [
            components.create_button(
                message,
                label = "🏠",
                id = "home",
                style = "success" if selected == "home" else "primary",
                callback = lambda *args: self.list_(*args, "home", None, False),
                only_sender = True,
                row = 1
            )
        ]

        for category, details in categories.items():
            cat = details["details"]
            
            buttons.append(
                components.create_button(
                    message,
                    label = f"{cat['emoji']} {cat['name']}",
                    id = category,
                    style = "success" if selected_category == category else "secondary",
                    callback = lambda *args: self.list_(*args, "category", str(category), False),
                    only_sender = True,
                    row = 1
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

    async def setting_page(
            self,
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb,
            values: list,
            gen_new: bool = False,
            origin: int = 0
        ):

        if len(values) == 0:
            return

        setting_name = values[0]

        # Find setting
        setting = bot.config.settings[setting_name]

        # Get value
        value = await self.format(
            gdb,
            setting
        )

        # Get category
        category = bot.config.settings_categories[setting["category"]]

        # Generate embed
        embed = discordutils.create_embed(
            f"{message.guild.name} → {category['name']} → {setting['name']}",
            description = f"{setting['description']}\n\nSet to: {value}\n\nTo edit this setting, reply to this message with a new value."
        )

        view = components.create_view(
            [
                components.create_button(
                    message,
                    label = "🡸",
                    id = "back",
                    style = "primary",
                    callback = lambda *args: self.list_(*args, "category", setting["category"], False, origin),
                    only_sender = True,
                    row = 0
                ),
                components.create_button(
                    message,
                    label = "Reset",
                    id = "reset",
                    style = "danger",
                    callback = lambda *args: self.reset(*args, values, False, origin),
                    only_sender = True,
                    row = 0
                )
            ]
        )

        # Add reply callback
        bot.replies.add_callback(
            resp.interaction.message.id,
            message.author.id,
            lambda *args: self.edit_setting(resp, *args, values, False, origin),
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

    async def edit_setting(
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
            gen_new: bool = False,
            origin: int = 0
        ):
        # Make sure the message has content
        if message.content is None or len(message.content) == 0:
            await new_resp.send(
                embed = discordutils.error(
                    message.author,
                    "Invalid message!",
                    "Reply with text to change the setting to."
                )
            )
            return

        if len(values) == 0:
            return
        
        setting_name = values[0]

        # Find setting
        setting = bot.config.settings[setting_name]

        # Get category
        category = bot.config.settings_categories[setting["category"]]

        # Try to validate
        valid, new = await bot.args.parse(
            setting["validate"],
            message.content,
            {}
        )

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
        path = [f"['{x}']" for x in setting["path"].strip("/").split("/")]
        exec(
            f"gdb{''.join(path)} = new"
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

        await self.setting_page(
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb,
            values,
            gen_new,
            origin
        )


    async def reset(
            self,
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb,
            values: list,
            gen_new: bool = False,
            origin: int = 0
        ):

        if len(values) == 0:
            return
        
        setting_name = values[0]

        # Find setting
        setting = bot.config.settings[setting_name]

        # Get value
        value = await self.format(
            gdb,
            setting
        )

        # Get category
        category = bot.config.settings_categories[setting["category"]]

        # Edit GDB
        new = copy.copy(miscutils.follow_path(bot.config.defaults["guild"], setting["path"]))
        path = [f"['{x}']" for x in setting["path"].strip("/").split("/")]
        exec(
            f"gdb{''.join(path)} = new"
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

        await self.setting_page(
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb,
            values,
            gen_new,
            origin
        )