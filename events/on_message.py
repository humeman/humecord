import humecord

async def check_ping(message):
    if not message.author.bot and message.author.id != humecord.bot.client.user.id:
        if message.content.startswith("<@"):
            if message.content in [f"<@{humecord.bot.client.user.id}>", f"<@!{humecord.bot.client.user.id}>"]:
                # Create a resp instance
                resp = humecord.classes.discordclasses.MessageResponseChannel(
                    message
                )

                # Get GDB
                if humecord.bot.config.use_api:
                    gdb = await humecord.bot.api.get(humecord.bot.config.self_api, "guild", {"id": message.guild.id, "autocreate": True})

                else:
                    gdb = await humecord.bot.db.get("guild", {"id": message.guild.id})

                # Generate pdb
                pdb = {}
                for key in humecord.bot.config.preferred_gdb:
                    pdb[key] = gdb[key]

                await humecord.bot.commands.get_command("info", "about").run(
                    message,
                    resp,
                    [],
                    {},
                    None,
                    pdb
                )

async def run_command(message):
    if not message.author.bot and message.author.id != humecord.bot.client.user.id:
        await humecord.bot.commands.run(message)

async def check_debug_console(message):
    if humecord.bot.debug_console.channel and message.author.id != humecord.bot.client.user.id:
        if message.channel.id == humecord.bot.debug_console.channel.id:
            await humecord.bot.debug_console.execute(message)