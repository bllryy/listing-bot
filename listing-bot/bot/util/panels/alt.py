import discord
from discord.ui import View, button
from bot.bot import Bot

from bot.util.ticket import SellGoods

class AltSale(View):
    def __init__(self, bot:Bot, *args, **kwargs):
        super().__init__(*args, **kwargs, timeout=None)
        self.bot = bot

    @button(
        label="Sell an Alt",
        custom_id="sell:alt",
        style=discord.ButtonStyle.red,
        row=1
    )
    async def sell_alt(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(SellGoods(self.bot, good="alt"))
