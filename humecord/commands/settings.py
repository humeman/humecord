"""
/settings: humecord base commands

User-facing settings management.
"""

import copy
from typing import Optional

import humecord

from humecord.classes import (
    discordclasses
)

from humecord.utils import (
    discordutils,
    miscutils
)

class Locations:
    HOME = 0
    CATEGORY = 1
    SETTING = 2

class SettingsCommand(humecord.Command):
    def __init__(
            self
        ) -> None:
        self.name = "settings"
        self.description = "Customizes the bot's settings in this server."
        self.command_tree = {
            "": self.run
        }
        self.args = {}
        self.subcommand_details = {}
        self.messages = {}

        self.perms = "guild.admin"
        self.default_perms = "guild.admin"

        self.guildonly = True

        global bot
        from humecord import bot

    async def run(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context,
            location: Locations = Locations.HOME
        ) -> None:

        categories = {}

        for name, setting in bot.config.settings.items():
            # Check if the category exists
            if setting["category"] not in categories:
                categories[setting["category"]] = {
                    "details": bot.config.settings_categories[setting["category"]],
                    "settings": {}
                }

            categories[setting["category"]]["settings"][name] = setting

        # Now, work through our menu
        if location == Locations.HOME:
            # Display all categories
            
            # Generate fields and dropdown items
            fields = []
            options = {}
            for name, category_data in categories.items():
                details = category_data["details"]

                fields.append(
                    {
                        "name": f"%-a% {details['emoji']}  {details['name']} ({len(category_data['settings'])})",
                        "value": details["description"]
                    }
                )

                options[name] = {
                    "name": details["name"],
                    "description": details['description'],
                    "emoji": details["emoji"]
                }

            embed = discordutils.create_embed(
                title = f"{ctx.guild.name}'s settings",
                fields = fields
            )
            view = await bot.interactions.create_view(
                [
                    await bot.interactions.create_select(
                        name = "category",
                        callback = lambda *args: self.category_(*args),
                        row = 0,
                        sender = ctx.user,
                        placeholder = "Select a category",
                        options = options
                    )
                ]
            )

            await resp.edit(
                embed = embed,
                view = view
            )
            return

    def get_category_from(
            self,
            category_name: str
        ):

        category_data = {
            "details": bot.config.settings_categories[category_name],
            "settings": {}
        }

        for name, setting in bot.config.settings.items():
            # Check if the category exists
            if setting["category"] == category_name:
                category_data["settings"][name] = setting

        return category_data

    async def format(
            self,
            gdb,
            setting
        ):
        # This piece of work was copied directly from the previous settings command
        # Sorry to future me if I have to edit it

        # Get value
        try:
            value = miscutils.follow_path(gdb, setting["path"])

        except:
            return "**Error**: Value doesn't exist"

        else:
            # Run formatters
            if setting.get("list"):
                values = []

                for val in value:
                    new_val = await bot.args.format(
                        setting["type"],
                        val,
                        {}
                    )
                    
                    if "wrap_format" in setting:
                        new_val = setting["wrap_format"].replace(".", new_val)

                    values.append(new_val)

                if len(values) == 0:
                    return "*No items set!*"

                return ", ".join(values)

            else:
                if value is None:
                    return "*Not set!*"

                new_val = await bot.args.format(
                    setting["type"],
                    value,
                    {}
                )

                if "wrap_format" in setting:
                    new_val = setting["wrap_format"].replace(".", new_val)

                return new_val

    async def category_(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context,
            category_name: Optional[str] = None,
            page: int = 0
        ) -> None:
        """
        Shows a category.
        
        If category_name is None, it's retrieved from ctx.values (dropdown interaction only).
        """
        if category_name is None:
            values = getattr(ctx, "values", None)

            if values is None:
                await resp.edit(
                    embed = discordutils.error(
                        ctx.user,
                        "Something went wrong!",
                        "No dropdown item was passed to command.category(). Report this!"
                    ),
                    view = None
                )
                return

            if len(values) != 1:
                await resp.edit(
                    embed = discordutils.error(
                        ctx.user,
                        "Something went wrong!",
                        "Too many or too little dropdown items were passed to command.category(). Report this!"
                    ),
                    view = None
                )
                return

            category_name = values[0]

        # Get category
        category_data = self.get_category_from(category_name)

        # Paginate
        max_page_i = (len(category_data["settings"]) // 5) + (1 if len(category_data["settings"]) % 5 != 0 else 0) - 1
        
        # Generate this page of options
        fields = []
        options = {}
        for setting_name in list(category_data["settings"])[page * 5 : (page + 1) * 5]:
            setting_data = category_data["settings"][setting_name]

            # Get current value
            value = await self.format(
                ctx.gdb,
                setting_data
            )

            fields.append(
                {
                    "name": f"%-a% {setting_data['name']}",
                    "value": f"{setting_data['description']}\nSet to: {value}"
                }
            )

            options[setting_name] = {
                "name": setting_data["name"],
                "emoji": category_data["details"]["emoji"],
                "description": setting_data["description"]
            }

        # Define select, then home, forwards, and backwards buttons
        view = await bot.interactions.create_view([
            await bot.interactions.create_select(
                name = "setting",
                callback = self.setting,
                row = 0,
                sender = ctx.user,
                placeholder = "Select a setting",
                options = options
            ),
            await bot.interactions.create_button(
                name = "home",
                callback = self.run,
                row = 1,
                sender = ctx.user,
                label = "Home",
                emoji = "🏠",
                style = humecord.ButtonStyles.PRIMARY
            ),
            await bot.interactions.create_button(
                name = "back",
                callback = bot.interactions.skip if page == 0 else lambda *args: self.category(resp, ctx, category_name, page - 1),
                row = 1,
                disabled = page == 0,
                sender = ctx.user,
                label = "←"
            ),
            await bot.interactions.create_button(
                name = "forward",
                callback = bot.interactions.skip if page == max_page_i else lambda *args: self.category(resp, ctx, category_name, page + 1),
                row = 1,
                disabled = page == max_page_i,
                sender = ctx.user,
                label = "→"
            )
        ])

        await resp.edit(
            embed = discordutils.create_embed(
                f"{ctx.guild.name} → Settings → {category_data['details']['name']}",
                fields = fields
            ),
            view = view
        )

    async def setting(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context,
            setting_name: Optional[str] = None
        ) -> None:
        """
        Shows a setting page.
        
        If setting_name is None, it's retrieved from ctx.values (dropdown interaction only).
        """
        if setting_name is None:
            values = getattr(ctx, "values", None)

            if values is None:
                await resp.edit(
                    embed = discordutils.error(
                        ctx.user,
                        "Something went wrong!",
                        "No dropdown item was passed to command.category(). Report this!"
                    ),
                    view = None
                )
                return

            if len(values) != 1:
                await resp.edit(
                    embed = discordutils.error(
                        ctx.user,
                        "Something went wrong!",
                        "Too many or too little dropdown items were passed to command.category(). Report this!"
                    ),
                    view = None
                )
                return

            setting_name = values[0]

        # Get setting
        setting_data = bot.config.settings[setting_name]

        # Get category
        category_data = bot.config.settings_categories[setting_data["category"]]

        # Get value
        value = await self.format(
            ctx.gdb,
            setting_data
        )

        # Generate some buttons
        view = await bot.interactions.create_view(
            [
                await bot.interactions.create_button(
                    "back",
                    callback = lambda *args: self.category_(*args, category_name = setting_data["category"], page = 0),
                    sender = ctx.user,
                    label = "←"
                ),
                await bot.interactions.create_button(
                    "edit",
                    callback = lambda *args: self.show_edit_modal(*args, setting_name),
                    sender = ctx.user,
                    label = "Edit",
                    style = humecord.ButtonStyles.PRIMARY
                ),
                await bot.interactions.create_button(
                    "reset",
                    callback = lambda *args: self.reset(*args, setting_name),
                    sender = ctx.user,
                    label = "Reset",
                    style = humecord.ButtonStyles.DANGER
                )
            ]
        )

        # Get validator info
        validator = setting_data["type"]

        if setting_data.get("validate"):
            validator += f"[{setting_data['validate']}]"

        type_str = await bot.args.format_rule(validator)

        list_str = ""
        if setting_data.get("list"):
            list_str = "A list of "

        await resp.edit(
            embed = discordutils.create_embed(
                f"{ctx.guild.name} → Settings → {category_data['name']} → {setting_data['name']}",
                description = f"{setting_data['description']}\n**Type:** {list_str}{type_str}\n**Set to:** {value}"
            ),
            view = view
        )

    async def reset(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context,
            setting_name: str
        ) -> None:
        # Get setting
        setting_data = bot.config.settings[setting_name]

        new = copy.copy(miscutils.follow_path(bot.config.defaults["guild"], setting_data["path"]))
        path = [f"['{x}']" for x in setting_data["path"].strip("/").split("/")]
        exec(
            f"ctx.gdb{''.join(path)} = new"
        )

        # Put back
        await bot.api.put(
            bot.config.self_api,
            "guild",
            {
                "id": ctx.guild.id,
                "db": ctx.gdb
            }
        )

        # Run setting page again
        await self.setting(
            resp,
            ctx,
            setting_name
        )

    async def show_edit_modal(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context,
            setting_name: str
        ) -> None:
        # Find setting
        setting_data = bot.config.settings[setting_name]

        # Get category
        category_data = bot.config.settings_categories[setting_data["category"]]

        # Get old value
        real_value = miscutils.follow_path(ctx.gdb, setting_data["path"])

        if setting_data.get("list"):
            values = []

            for value in real_value:
                values.append(
                    str(value)
                )

            real_value = "\n".join(values)

        # Get validator type for user
        validator = setting_data["type"]

        if setting_data.get("validate"):
            validator += f"[{setting_data['validate']}]"

        # Create a modal
        modal = await bot.interactions.create_modal(
            name = "edit",
            callback = lambda *args: self.finish_edit(*args, setting_name),
            sender = ctx.user,
            title = f"Editing: {category_data['name']} → {setting_data['name']}",
            components = [
                await bot.interactions.create_textinput(
                    name = "input",
                    label = f"New value" + (" (ENTER for new item)" if setting_data.get("list") else ""),
                    default = str(real_value) if real_value is not None else None,
                    placeholder = "Type your new value here",
                    required = True,
                    min_length = 0,
                    max_length = 1024,
                    long = setting_data.get("list") or False
                )
            ]
        )

        await resp.send_modal(
            modal
        )

    async def finish_edit(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context,
            setting_name: str
        ) -> None:
        # Find setting
        setting_data = bot.config.settings[setting_name]

        # Get category
        category_data = self.get_category_from(setting_data["category"])

        # Get user's data
        user_input = ctx.modal_args.get("input")

        print(f"Val = {user_input}")

        # And, check if there's no value
        if user_input is None: # first to avoid string ops on NoneType
            print("reset")
            await self.reset(resp, ctx, setting_name)
            return

        if len(user_input) == 0:
            print("reset")
            await self.reset(resp, ctx, setting_name)
            return

        # Prepare for parsing
        new_value = None
        validator = setting_data["type"]

        if setting_data.get("validate"):
            validator += f"[{setting_data['validate']}]"

        # List parsing
        if setting_data.get("list"):
            # Split value into lines
            values = user_input.split("\n")
            new_value = []

            for i, value in enumerate(values):
                value = value.strip()

                # Try to parse it
                valid, new = await bot.args.parse(
                    validator,
                    value,
                    {
                        "guild": ctx.guild
                    }
                )

                if not valid:
                    await resp.edit(
                        embed = discordutils.create_embed(
                            description = f"{bot.config.lang['emoji']['error']}  Value parsing failed at list item {i + 1}!\n**Reason**: {', '.join([f'`{x}`' for x in new])}\n**Your data** (for resubmission purposes):\n```{user_input[:1000]}```",
                            color = "error"
                        )
                    )
                    return

                # Append to new values
                if "attr" in setting_data:
                    new = getattr(new, setting_data["attr"], None)

                new_value.append(new)

        else:
            # Try to parse it
            valid, new = await bot.args.parse(
                validator,
                user_input,
                {
                    "guild": ctx.guild
                }
            )

            if not valid:
                await resp.edit(
                    embed = discordutils.create_embed(
                        description = f"{bot.config.lang['emoji']['error']}  Value parsing failed!\n**Reason**: {', '.join([f'`{x}`' for x in new])}\n**Your data** (for resubmission purposes):\n```{user_input[:1000]}```",
                        color = "error"
                    )
                )
                return

            new_value = new
            
            if "attr" in setting_data:
                new_value = getattr(new_value, setting_data["attr"], None)

        # Generate new value
        path = [f"['{x}']" for x in setting_data["path"].strip("/").split("/")]
        exec(
            f"ctx.gdb{''.join(path)} = new_value"
        )

        # Put back
        await bot.api.put(
            bot.config.self_api,
            "guild",
            {
                "id": ctx.guild.id,
                "db": ctx.gdb
            }
        )

        # Refresh page
        await self.setting(
            resp,
            ctx,
            setting_name
        )