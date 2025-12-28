import discord
from discord.ui import View, button
from bot.bot import Bot

from bot.util.ticket import SellGoods

class ProfileSale(View):
    def __init__(self, bot:Bot, *args, **kwargs):
        super().__init__(*args, **kwargs, timeout=None)
        self.bot = bot

    @button(
        label="Sell a Profile",
        custom_id="sell:profile",
        style=discord.ButtonStyle.red,
        row=1
    )
    async def sell_profile(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(SellGoods(self.bot, good="profile"))
