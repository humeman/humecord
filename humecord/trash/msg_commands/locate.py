from humecord.utils import (
    discordutils,
    exceptions,
    components,
    dateutils
)


class LocateCommand:
    def __init__(
            self
        ):

        self.name = "locate"
        self.description = "Locates and gets information about a user."

        self.aliases = ["finduser", "locateuser"]

        self.permission = "bot.dev"

        self.args = {
            "1": {
                "required": True,
                "index": 1,
                "rules": {
                    "arg1-b": {"rule": "user"},
                    "arg1-a": {"rule": "str"}
                }
            }
        }

        global bot
        from humecord import bot

    async def run(
            self,
            message,
            resp,
            args,
            udb,
            gdb,
            alternate_gdb = None,
            preferred_gdb = None
        ):

        user = args["1"]

        if type(user) == str:
            discover = True
            
            if "#" in user:
                uname, udisc = user.rsplit("#", 1)

                uname = uname.lower()

                try:
                    udisc = int(udisc)

                    if udisc < 1 or udisc > 9999:
                        raise

                except:
                    await resp.error(
                        message.author,
                        "Invalid user!",
                        "This user's discriminator is not valid. Ensure that the discriminator is a 4 digit number, or paste an ID instead."
                    )
                    return

            else:
                uname = user
                udisc = None

        else:
            discover = False

        members = []

        for guild in bot.client.guilds:
            sel = None

            # Check if discovering
            if discover:
                for member in guild.members:
                    if member.name.lower() == uname and member.discriminator == udisc:
                        sel = member

            else:
                member = guild.get_member(user.id)

                if member is not None:
                    sel = member

            if sel is not None:
                members.append(
                    sel
                )

        if len(members) == 0:
            await resp.error(
                message.author,
                f"Search failed!",
                f"No members located for {str(user) if not discover else uname}."
            )
            return
        
        comp = []

        for member in members:
            comp.append(
                {
                    "name": f"→ {member.guild.name} ({member.guild.id})",
                    "value": "\n".join([
                        f"• Joined: {dateutils.get_timestamp(member.joined_at)}",
                        f"• Name: {discordutils.get_member_descriptor(member)}",
                        f"• Role: {member.top_role.name} ({member.top_role.id})"
                    ])
                }
            )

        await resp.embed(
            f"{members[0].name}#{members[0].discriminator}'s shared guilds ({len(comp)})",
            fields = comp,
            footer = f"ID: {members[0].id}"
        )


        