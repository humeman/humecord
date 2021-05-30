
def get_message(m_type, message):
    if m_type == "message":
        return message

    else:
        raise NotImplementedError()


class SlashCommandMessage:
    def __init__(
            self,
            message_type: str,
            details: dict
        ):

        """
        Constructs a fake Message.

        Designed to allow for a seamless transition between
        regular messages and slashcommands without the pain of
        creating a fake message class or abusing the bot + 
        slashcommand system.
        """

        self.type = message_type

    async def send(
            self,
            content,
            embed = None,
            file = None,
            files = None
        ):

        await self.channel.send(content, embed = embed, file = file, files = files)


class SlashCommandChannel:
    def __init__(
            self,
            parent: SlashCommandMessage
        ):

        self.parent = parent

        if parent.type == "message":
            # Set some things
            set_values = [
                "category",
                "name",
                "guild",
                "created_at",
                "mention",
                "position",
                "permissions_synced"
            ]

            for key in set_values:
                try:
                    val = getattr(parent.channel, val, j)

                except:
                    pass

                setattr(self, key, getattr())