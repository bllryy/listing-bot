import discord
from discord.ui import View, button
from bot.bot import Bot

from bot.util.ticket import CoinTicket

class CoinSale(View):
    def __init__(self, bot:Bot, *args, **kwargs):
        super().__init__(*args, **kwargs, timeout=None)
        self.bot = bot
            
    @button(
        label="Buy Coins",
        custom_id="buy:coins",
        style=discord.ButtonStyle.green,
        row=1
    )
    async def buy_coins(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(CoinTicket(self.bot, buy=True))

    @button(
        label="Sell Coins",
        custom_id="sell:coins",
        style=discord.ButtonStyle.red,
        row=1
    )
    async def sell_coins(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(CoinTicket(self.bot, buy=False))
