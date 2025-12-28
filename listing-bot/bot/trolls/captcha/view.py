import discord
from discord.ui import View, button

from bot.bot import Bot
import asyncio

class CaptchaView(View):
    def __init__(self, bot: Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @button(label="Solve Captcha", style=discord.ButtonStyle.green, custom_id="solve_captcha")
    async def solve_captcha(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = discord.ui.Modal(
            discord.ui.InputText(
                label="Enter Captcha",
                placeholder="Type the captcha text here..."
            ),
            title="Captcha Verification"
        )
        modal.callback = self._respond
        await interaction.response.send_modal(modal)
 
    async def _respond(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await asyncio.sleep(1)
        await interaction.respond("The data you have entered is incorrect. Please try again.", ephemeral=True)

