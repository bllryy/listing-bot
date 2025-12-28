from discord.ext import commands
from bot.bot import Bot

class Donut(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

def setup(bot: Bot):
    bot.add_cog(Donut(bot))