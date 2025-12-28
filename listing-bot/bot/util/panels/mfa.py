import discord
from discord.ui import View, button, select
from bot.bot import Bot

from bot.util.ticket import MFASell, MFABuy

class MFASale(View):
    def __init__(self, bot:Bot, *args, **kwargs):
        super().__init__(*args, **kwargs, timeout=None)
        self.bot = bot

    
    @button(
        label="Sell an MFA",
        custom_id="sell:mfa",
        style=discord.ButtonStyle.red,
        row=1
    )
    async def sell_profile(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_modal(MFASell(self.bot))

    @select(
        placeholder="Select a rank.",
        options=[
            discord.SelectOption(label="Non", description="This MFA has no rank.", value="Non"),
            discord.SelectOption(label="VIP", description="This MFA has the VIP rank.", value="VIP"),
            discord.SelectOption(label="VIP+", description="This MFA has the VIP+ rank.", value="VIP+"),
            discord.SelectOption(label="MVP", description="This MFA has the MVP rank.", value="MVP"),
            discord.SelectOption(label="MVP+", description="This MFA has the MVP+ rank.", value="MVP+"),
        ],
        custom_id="mfa:buy",
        row=0
    )
    async def buy_mfa(self, select: discord.ui.Select, interaction: discord.Interaction):
        await interaction.response.send_modal(MFABuy(self.bot, select.values[0]))
