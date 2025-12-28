import discord
from discord.ui import View, button
from bot.bot import Bot

from bot.util.ticket import SellGoods

class AccountSale(View):
    def __init__(self, bot:Bot, *args, **kwargs):
        super().__init__(*args, **kwargs, timeout=None)
        self.bot = bot

    @button(
        label="Sell an Account",
        custom_id="sell:account",
        style=discord.ButtonStyle.red,
        row=1
    )
    async def sell_account(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(SellGoods(self.bot, good="account"))
