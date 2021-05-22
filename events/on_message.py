import humecord

async def run_command(message):
    if not message.author.bot and message.author.id != humecord.bot.client.user.id:
        await humecord.bot.commands.run(message)

async def check_debug_console(message):
    if humecord.bot.debug_console.channel and message.author.id != humecord.bot.client.user.id:
        if message.channel.id == humecord.bot.debug_console.channel.id:
            await humecord.bot.debug_console.execute(message)