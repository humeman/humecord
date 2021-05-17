import humecord

async def run_command(message):
    if not message.author.bot and message.author.id != humecord.bot.client.user.id:
        await humecord.bot.commands.run(message)