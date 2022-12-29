"""
/about: humecord base commands

Gives some info about the running bot.
"""

from typing import Optional

import humecord

from humecord.classes import (
    discordclasses
)

from humecord.utils import (
    miscutils,
    discordutils
)

class AboutCommand(humecord.Command):
    def __init__(
            self
        ) -> None:
        self.name = "about"
        self.description = "Gives some info about me."
        self.command_tree = {
            "": self.run
        }
        self.args = {}
        self.messages = {
            "aliases": ["aboutme"]
        }
        self.perms = "bot.mod"
        self.default_perms = "guild.mod"

        global bot
        from humecord import bot

    async def run(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context
        ) -> None:
        await self.show_menu(
            resp,
            ctx,
            "home"
        )

    def expand_eval(
            self,
            string
        ):
        """
        FIXME: URGENT
        This is very bad, and should not exist.
        """

        if string.startswith("eval:::"):
            return eval(string.split(":::", 1)[1])

        else:
            return string

    async def show_menu(
            self,
            resp: discordclasses.ResponseChannel,
            ctx: discordclasses.Context,
            current_page: Optional[str]
        ):

        if current_page is None:
            # Override with component name
            current_page = ctx.component

        placeholders = {
            "prefix": ctx.gdb["prefix"],
            "bot": bot.config.cool_name,
            "version": bot.config.version,
            "humecord": humecord.version,
            "owner": bot.config.owner_name,
            "support": bot.config.discord_server,
            "invite": bot.config.invite,
            "guide": bot.config.guide_page
        }

        comp = {}

        for key, value in bot.config.lang["about_response"][current_page].items():
            if key == "fields":
                comp["fields"] = []

                for field in value:
                    comp["fields"].append(
                        {
                            "name": miscutils.expand_placeholders(field["name"], placeholders),
                            "value": miscutils.expand_placeholders(self.expand_eval(field["value"]), placeholders)
                        }
                    )

            elif not key.startswith("__"):
                comp[key] = miscutils.expand_placeholders(self.expand_eval(value), placeholders)

        embed = discordutils.create_embed(**comp)

        components = []

        for page, details in bot.config.lang["about_response"].items():
            components.append(
                await bot.interactions.create_button(
                    name = page,
                    callback = bot.interactions.skip if page == current_page else lambda *args: self.show_menu(*args, None),
                    label = details["__button__"]["text"],
                    style = humecord.ButtonStyles.SUCCESS if page == current_page else (humecord.ButtonStyles.PRIMARY if page == "home" else humecord.ButtonStyles.SECONDARY)
                )
            )

        view = await bot.interactions.create_view(
            components
        )

        await resp.edit(
            embed = embed,
            view = view
        )
