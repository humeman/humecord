"""
HumeCord/bot.py

Constructs a bot, and stores it so it can be
used globally.

Call this instead of Bot() directly.
"""

from .classes import Bot

def init(imports):
    global bot
    bot = Bot(imports)

