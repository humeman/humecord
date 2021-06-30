import discord
import humecord
from humecord.utils import (
        discordutils,
        miscutils,
        components
    )

class AboutCommand:
    def __init__(
            self
        ):

        self.name = "about"

        self.description = "Sends info about me."

        self.aliases = ["info"]

        self.permission = "bot.any"

        global bot
        from humecord import bot

    async def run(
            self,
            *args
        ):

        await self.swap(
            True,
            "home",
            *args
        )
        
    def expand_eval(
            self,
            string
        ):

        if string.startswith("eval:::"):
            return eval(string.split(":::", 1)[1])

        else:
            return string

    async def swap(
            self,
            make_new,
            category,
            message,
            resp,
            args,
            gdb,
            alternate_gdb,
            preferred_gdb
        ):

        placeholders = {
            "prefix": preferred_gdb["prefix"],
            "bot": bot.config.cool_name,
            "version": bot.config.version,
            "humecord": humecord.version,
            "owner": bot.config.owner_name,
            "support": bot.config.discord_server,
            "invite": bot.config.invite,
            "guide": bot.config.guide_page
        }

        comp = {}

        for key, value in bot.config.lang["about_response"][category].items():
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

        buttons = []

        for page, details in bot.config.lang["about_response"].items():
            buttons.append(
                components.create_button(
                    message,
                    label = details["__button__"]["text"],
                    style = "success" if page == category else details["__button__"]["style"],
                    id = page,
                    callback = self.pass_ if page == category else lambda *args, page = page: self.swap(False, str(page), *args),
                    only_sender = False
                )
            )

        view = components.create_action_row(
            buttons
        )

        if make_new:
            await resp.send(
                embed = embed,
                view = view
            )

        else:
            await resp.edit(
                embed = embed,
                view = view
            )

    async def pass_(self, *args):
        return

