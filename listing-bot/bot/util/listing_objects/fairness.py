import discord
from discord.ui import View, button

class FairnessView(View):
    def __init__(self, *args):
        super().__init__(timeout=None)

    @button(
        label="What?",
        style=discord.ButtonStyle.grey,
        custom_id="fairness:info"
    )
    async def fairness_info(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Fairness Information",
            description="This value is calculated by taking the value of the account (`/value`) and dividing it by the price of the account. This value is then compared to a list to determine a fairness rating.",
            color=discord.Color.embed_background()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)